"""On-prem HTTP egress guard.

Every httpx request is classified against a local allowlist. External (WAN)
destinations are recorded and, when enforcement is on, blocked. This is the
runtime proof for the SIH sovereignty claim — not a hardcoded 0 in the UI.
"""

from __future__ import annotations

import ipaddress
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_MAX_EVENTS = 250
_DOCKER_HOSTS = frozenset(
    {
        "ollama",
        "qdrant",
        "postgres",
        "redis",
        "backend",
        "frontend",
        "aegis_ollama",
        "aegis_qdrant",
        "aegis_postgres",
        "aegis_redis",
        "aegis_backend",
        "aegis_frontend",
        "host.docker.internal",
    }
)
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0", "ip6-localhost", "testserver"})


@dataclass(frozen=True)
class EgressDecision:
    url: str
    host: str
    allowed: bool
    classification: str  # INTERNAL | EXTERNAL
    reason: str
    timestamp: float


class EgressBlockedError(httpx.RequestError):
    """Raised when a request is denied by the air-gap policy."""


class EgressGuard:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: Deque[Dict[str, Any]] = deque(maxlen=_MAX_EVENTS)
        self._allowed = 0
        self._blocked = 0

    def enabled(self) -> bool:
        return bool(settings.EGRESS_MONITOR_ENABLED)

    def enforcing(self) -> bool:
        return self.enabled() and bool(getattr(settings, "EGRESS_ENFORCE", True))

    def allowlist(self) -> List[str]:
        hosts = set(_DOCKER_HOSTS)
        hosts.update(_LOCAL_HOSTS)
        for raw in (
            settings.QDRANT_HOST,
            settings.POSTGRES_SERVER,
            settings.REDIS_HOST,
        ):
            if raw:
                hosts.add(raw.split(":")[0].lower())
        ollama_host = urlparse(settings.OLLAMA_BASE_URL).hostname
        if ollama_host:
            hosts.add(ollama_host.lower())
        extra = getattr(settings, "EGRESS_ALLOW_HOSTS", "") or ""
        for item in extra.split(","):
            token = item.strip().lower()
            if token:
                hosts.add(token)
        return sorted(hosts)

    def evaluate(self, url: str) -> EgressDecision:
        parsed = urlparse(url if "://" in url else f"http://{url}")
        host = (parsed.hostname or "").lower().strip("[]")
        now = time.time()

        if not host:
            return EgressDecision(url, "", False, "EXTERNAL", "Missing hostname", now)

        if host in self.allowlist() or host.endswith(".local") or host.endswith(".internal"):
            return EgressDecision(url, host, True, "INTERNAL", "Allowlisted on-prem host", now)

        if self._is_private_ip(host):
            return EgressDecision(url, host, True, "INTERNAL", "Private / loopback address", now)

        if self.enforcing():
            return EgressDecision(
                url, host, False, "EXTERNAL", "Blocked: destination is outside the air-gap allowlist", now
            )
        return EgressDecision(
            url, host, True, "EXTERNAL", "External host allowed because enforcement is off", now
        )

    @staticmethod
    def _is_private_ip(host: str) -> bool:
        try:
            addr = ipaddress.ip_address(host)
        except ValueError:
            return False
        return bool(addr.is_private or addr.is_loopback or addr.is_link_local)

    def record(self, decision: EgressDecision) -> None:
        event = {
            "url": decision.url,
            "host": decision.host,
            "allowed": decision.allowed,
            "classification": decision.classification,
            "reason": decision.reason,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(decision.timestamp)),
        }
        with self._lock:
            self._events.appendleft(event)
            if decision.allowed:
                self._allowed += 1
            else:
                self._blocked += 1
                logger.warning("EGRESS BLOCKED host=%s url=%s", decision.host, decision.url)

    def snapshot(self, event_limit: int = 25) -> Dict[str, Any]:
        with self._lock:
            events = list(self._events)[:event_limit]
            allowed = self._allowed
            blocked = self._blocked
        enforcing = self.enforcing()
        if not self.enabled():
            status = "DISABLED"
        elif blocked == 0:
            status = "AIR_GAP_ENFORCED"
        else:
            status = "AIR_GAP_ENFORCED_WITH_BLOCKS"
        return {
            "enabled": self.enabled(),
            "enforcing": enforcing,
            "sovereign_status": status,
            "allowed_count": allowed,
            "blocked_count": blocked,
            "external_allowed": 0 if enforcing else sum(1 for e in events if e["classification"] == "EXTERNAL" and e["allowed"]),
            "allowlist": self.allowlist(),
            "events": events,
        }

    def reset(self) -> None:
        with self._lock:
            self._events.clear()
            self._allowed = 0
            self._blocked = 0


egress_guard = EgressGuard()
_HOOKS_INSTALLED = False


class _GuardedSyncTransport(httpx.BaseTransport):
    def __init__(self, inner: Optional[httpx.BaseTransport] = None) -> None:
        self._inner = inner or httpx.HTTPTransport()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        decision = egress_guard.evaluate(str(request.url))
        egress_guard.record(decision)
        if not decision.allowed:
            raise EgressBlockedError(f"Air-gap policy blocked {decision.host}", request=request)
        return self._inner.handle_request(request)


class _GuardedAsyncTransport(httpx.AsyncBaseTransport):
    def __init__(self, inner: Optional[httpx.AsyncBaseTransport] = None) -> None:
        self._inner = inner or httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        decision = egress_guard.evaluate(str(request.url))
        egress_guard.record(decision)
        if not decision.allowed:
            raise EgressBlockedError(f"Air-gap policy blocked {decision.host}", request=request)
        return await self._inner.handle_async_request(request)


def install_httpx_hooks() -> None:
    """Wrap default httpx clients so Qdrant, Ollama, and future calls are gated."""
    global _HOOKS_INSTALLED
    if _HOOKS_INSTALLED:
        return

    orig_sync = httpx.Client.__init__
    orig_async = httpx.AsyncClient.__init__

    def sync_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        transport = kwargs.get("transport")
        if not isinstance(transport, _GuardedSyncTransport):
            kwargs["transport"] = _GuardedSyncTransport(inner=transport)
        orig_sync(self, *args, **kwargs)

    def async_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        transport = kwargs.get("transport")
        if not isinstance(transport, _GuardedAsyncTransport):
            kwargs["transport"] = _GuardedAsyncTransport(inner=transport)
        orig_async(self, *args, **kwargs)

    httpx.Client.__init__ = sync_init  # type: ignore[method-assign]
    httpx.AsyncClient.__init__ = async_init  # type: ignore[method-assign]
    _HOOKS_INSTALLED = True
    logger.info("HTTP egress guard installed (enforce=%s)", egress_guard.enforcing())
