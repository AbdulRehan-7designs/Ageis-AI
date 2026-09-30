"""Config-driven open-weight model registry.

New models are added in ``app/core/model_catalog.json`` (and pulled in
``ollama_entrypoint.sh``). Orchestrator and UI must not hardcode Ollama tags.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Sequence, Union

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_CATALOG_PATH = Path(__file__).resolve().parent.parent / "core" / "model_catalog.json"

_CODE_PATTERNS = re.compile(
    r"\b(?:calculate|code|script|python|sandbox|formula|math|estimate|"
    r"degradation|interval|rul|function|debug|compile|unit\s*test)\b",
    re.IGNORECASE,
)
_VISION_PATTERNS = re.compile(
    r"\b(?:scanned|handwritten|photograph|image|ocr|p&id|pid|drawing|"
    r"vision|photo|diagram)\b",
    re.IGNORECASE,
)
_SUMMARY_PATTERNS = re.compile(
    r"\b(?:summar(?:y|ise|ize)|approval\s*note|brief(?:ing)?|minutes|"
    r"extract\s+(?:findings|key)|draft\s+(?:note|memo|letter))\b",
    re.IGNORECASE,
)

AUTO_SELECT_ID = "auto"


class ModelCapability(str, Enum):
    CHAT = "chat"
    REASONING = "reasoning"
    CODING = "coding"
    VISION = "vision"
    DOCUMENT_ANALYSIS = "document_analysis"
    TOOL_CALLING = "tool_calling"
    EMBEDDINGS = "embeddings"


class ModelProviderError(RuntimeError):
    """Raised when a configured provider cannot serve a request."""


class ModelProvider(ABC):
    """Provider-independent model interface for local LLM and embedding providers."""

    provider_name: str = "base"

    @abstractmethod
    async def generate(
        self,
        *,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        images: Optional[List[str]] = None,
        timeout: float = 120.0,
    ) -> str:
        """Generate a single model response."""

    @abstractmethod
    async def generate_stream(
        self,
        *,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        timeout: float = 120.0,
    ) -> AsyncIterator[str]:
        """Yield response fragments for streaming generation."""

    @abstractmethod
    async def health_check(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Return a structured health record for the provider."""

    @abstractmethod
    def model_info(self, model_name: str) -> Dict[str, Any]:
        """Return metadata for a configured model."""


class OllamaModelProvider(ModelProvider):
    """Local Ollama adapter for sovereign on-premise models."""

    provider_name = "ollama"

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL or "").rstrip("/")

    def _normalize_model(self, model_name: Optional[str]) -> str:
        model = (model_name or "").strip()
        if not model:
            raise ModelProviderError("No model name configured for the Ollama provider.")
        return model

    async def health_check(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        if not self.base_url:
            return {
                "status": "MISCONFIGURED",
                "provider": self.provider_name,
                "model": model_name,
                "message": "Ollama base URL is not configured.",
            }

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
        except httpx.RequestError as exc:
            return {
                "status": "UNAVAILABLE",
                "provider": self.provider_name,
                "model": model_name,
                "message": f"Ollama is unreachable: {exc}",
            }

        if resp.status_code != 200:
            return {
                "status": "UNAVAILABLE",
                "provider": self.provider_name,
                "model": model_name,
                "message": f"Ollama health check failed with HTTP {resp.status_code}.",
            }

        payload = resp.json()
        available_models = [
            str(item.get("name") or item.get("model") or "")
            for item in payload.get("models", [])
            if isinstance(item, dict)
        ]
        available_models = [item for item in available_models if item]
        if model_name:
            normalized = self._normalize_model(model_name)
            if normalized in available_models or any(name.startswith(f"{normalized}:") for name in available_models):
                return {
                    "status": "AVAILABLE",
                    "provider": self.provider_name,
                    "model": normalized,
                    "message": f"Model '{normalized}' is available.",
                    "available_models": available_models,
                }
            return {
                "status": "DISABLED",
                "provider": self.provider_name,
                "model": normalized,
                "message": f"Model '{normalized}' is not installed in this local Ollama instance.",
                "available_models": available_models,
            }

        return {
            "status": "AVAILABLE" if available_models else "DISABLED",
            "provider": self.provider_name,
            "model": model_name,
            "message": "Ollama is responding successfully." if available_models else "Ollama is responding but no local models are installed.",
            "available_models": available_models,
        }

    def model_info(self, model_name: str) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self._normalize_model(model_name),
            "base_url": self.base_url,
            "capabilities": [
                ModelCapability.CHAT.value,
                ModelCapability.REASONING.value,
                ModelCapability.DOCUMENT_ANALYSIS.value,
                ModelCapability.VISION.value,
            ],
        }

    async def generate(
        self,
        *,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        images: Optional[List[str]] = None,
        timeout: float = 120.0,
    ) -> str:
        model_name = self._normalize_model(model)
        health = await self.health_check(model_name)
        if health["status"] in {"MISCONFIGURED", "UNAVAILABLE"}:
            raise ModelProviderError(health.get("message") or "Ollama is unavailable.")
        if health["status"] == "DISABLED":
            raise ModelProviderError(f"Model '{model_name}' is not installed locally.")

        payload = {
            "model": model_name,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": options or {"temperature": 0.1, "num_predict": 512},
        }
        if images:
            payload["images"] = list(images)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
        except httpx.TimeoutException as exc:
            raise ModelProviderError(f"Ollama timed out while generating for '{model_name}'.") from exc
        except httpx.RequestError as exc:
            raise ModelProviderError(f"Ollama request failed for '{model_name}': {exc}") from exc

        if resp.status_code != 200:
            raise ModelProviderError(
                f"Ollama returned HTTP {resp.status_code} for model '{model_name}'."
            )

        data = resp.json()
        answer = str(data.get("response") or "").strip()
        if not answer:
            raise ModelProviderError(f"Ollama returned an empty response for model '{model_name}'.")
        return answer

    async def generate_stream(
        self,
        *,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        timeout: float = 120.0,
    ) -> AsyncIterator[str]:
        model_name = self._normalize_model(model)
        payload = {
            "model": model_name,
            "prompt": prompt,
            "system": system,
            "stream": True,
            "options": options or {"temperature": 0.1, "num_predict": 512},
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as resp:
                    async for line in resp.aiter_lines():
                        if not line.strip() or not line.startswith("data: "):
                            continue
                        payload_text = line[6:]
                        try:
                            chunk = json.loads(payload_text)
                        except json.JSONDecodeError:
                            continue
                        fragment = str(chunk.get("response") or "")
                        if fragment:
                            yield fragment
        except httpx.TimeoutException as exc:
            raise ModelProviderError(f"Ollama timed out while streaming '{model_name}'.") from exc
        except httpx.RequestError as exc:
            raise ModelProviderError(f"Ollama streaming failed for '{model_name}': {exc}") from exc


@dataclass(frozen=True)
class RegisteredModel:
    id: str
    provider: str = "ollama"
    model: str = ""
    ollama_tag: str = ""
    display_name: str = ""
    task_types: List[str] = field(default_factory=list)
    capabilities: List[ModelCapability] = field(default_factory=list)
    description: str = ""
    vram_hint: str = ""
    context_window: Optional[int] = None
    enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "model", self.model or self.ollama_tag or self.id)
        object.__setattr__(self, "ollama_tag", self.ollama_tag or self.model or self.id)
        object.__setattr__(self, "display_name", self.display_name or self.id)
        if not self.capabilities:
            object.__setattr__(self, "capabilities", _infer_capabilities(self.task_types))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider,
            "model": self.model,
            "ollama_tag": self.ollama_tag,
            "display_name": self.display_name,
            "task_types": list(self.task_types),
            "capabilities": [cap.value for cap in self.capabilities],
            "description": self.description,
            "vram_hint": self.vram_hint,
            "context_window": self.context_window,
            "enabled": self.enabled,
        }


@dataclass(frozen=True)
class ModelSelection:
    task_type: str
    model_id: str
    ollama_tag: str
    display_name: str
    auto_selected: bool
    reason: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type,
            "model_id": self.model_id,
            "ollama_tag": self.ollama_tag,
            "display_name": self.display_name,
            "auto_selected": self.auto_selected,
            "reason": self.reason,
        }


def _infer_capabilities(task_types: Sequence[str]) -> List[ModelCapability]:
    capabilities: List[ModelCapability] = []
    task_map = {
        "chat": ModelCapability.CHAT,
        "reasoning": ModelCapability.REASONING,
        "code": ModelCapability.CODING,
        "coding": ModelCapability.CODING,
        "calculation": ModelCapability.CODING,
        "sandbox": ModelCapability.CODING,
        "vision": ModelCapability.VISION,
        "ocr": ModelCapability.VISION,
        "drawing": ModelCapability.VISION,
        "document_analysis": ModelCapability.DOCUMENT_ANALYSIS,
        "document_summary": ModelCapability.DOCUMENT_ANALYSIS,
        "document_qa": ModelCapability.DOCUMENT_ANALYSIS,
        "tool_calling": ModelCapability.TOOL_CALLING,
        "embeddings": ModelCapability.EMBEDDINGS,
    }
    for task_name in task_types:
        capability = task_map.get(str(task_name).lower())
        if capability and capability not in capabilities:
            capabilities.append(capability)
    if not capabilities:
        capabilities = [ModelCapability.CHAT, ModelCapability.REASONING]
    return capabilities


class ModelRegistry:
    """Load catalog, overlay env tag overrides, and expose the model abstraction."""

    def __init__(self, catalog_path: Optional[Path] = None) -> None:
        self._path = catalog_path or _CATALOG_PATH
        self._models: Dict[str, RegisteredModel] = {}
        self._providers: Dict[str, ModelProvider] = {"ollama": OllamaModelProvider()}
        self.reload()

    @staticmethod
    def _run_async(coro: Any) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def reload(self) -> None:
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        models: Dict[str, RegisteredModel] = {}
        for item in raw.get("models", []):
            capabilities = [
                _coerce_capability(capability)
                for capability in (item.get("capabilities") or _infer_capabilities(item.get("task_types") or []))
            ]
            model = RegisteredModel(
                id=item["id"],
                provider=item.get("provider", "ollama"),
                model=item.get("model") or item.get("ollama_tag") or item["id"],
                ollama_tag=item.get("ollama_tag") or item.get("model") or item["id"],
                display_name=item.get("display_name") or item["id"],
                task_types=list(item.get("task_types") or []),
                capabilities=capabilities,
                description=item.get("description") or "",
                vram_hint=item.get("vram_hint") or "",
                context_window=item.get("context_window"),
                enabled=bool(item.get("enabled", True)),
            )
            models[model.id] = model
        self._models = self._apply_env_overrides(models)

    @staticmethod
    def _apply_env_overrides(models: Dict[str, RegisteredModel]) -> Dict[str, RegisteredModel]:
        overrides = {
            "chat": settings.AEGIS_MODEL_GENERAL or settings.DEFAULT_CHAT_MODEL,
            "coder": settings.AEGIS_MODEL_CODING or settings.DEFAULT_CODER_MODEL,
            "vision": settings.AEGIS_MODEL_VISION or settings.DEFAULT_VISION_MODEL,
        }
        updated = dict(models)
        for model_id, tag in overrides.items():
            existing = updated.get(model_id)
            if not existing or not tag:
                continue
            if existing.ollama_tag == tag:
                continue
            updated[model_id] = RegisteredModel(
                id=existing.id,
                provider=existing.provider,
                model=tag,
                ollama_tag=tag,
                display_name=existing.display_name,
                task_types=existing.task_types,
                capabilities=list(existing.capabilities),
                description=existing.description,
                vram_hint=existing.vram_hint,
                context_window=existing.context_window,
                enabled=existing.enabled,
            )
        return updated

    def resolve_model(self, model_id_or_tag: Optional[str]) -> Optional[RegisteredModel]:
        if not model_id_or_tag:
            return None
        token = str(model_id_or_tag).strip()
        if not token:
            return None
        if token in self._models:
            return self._models[token]
        lowered = token.lower()
        for model in self._models.values():
            aliases = {
                model.id.lower(),
                model.model.lower(),
                model.ollama_tag.lower(),
                model.display_name.lower(),
            }
            if lowered in aliases:
                return model
        return None

    def register_model(self, model: RegisteredModel) -> RegisteredModel:
        self._models[model.id] = model
        return model

    def list_models(self, include_disabled: bool = False) -> List[RegisteredModel]:
        models = list(self._models.values())
        if not include_disabled:
            models = [m for m in models if m.enabled]
        return models

    def get(self, model_id_or_tag: Optional[str]) -> Optional[RegisteredModel]:
        return self.resolve_model(model_id_or_tag)

    def find_by_capability(self, capability: Union[str, ModelCapability]) -> List[RegisteredModel]:
        value = capability.value if isinstance(capability, ModelCapability) else str(capability).strip().lower()
        target = _coerce_capability(value)
        return [
            model for model in self.list_models(include_disabled=False)
            if target in model.capabilities
        ]

    def get_provider(self, model_id_or_tag: Optional[str]) -> ModelProvider:
        model = self.resolve_model(model_id_or_tag)
        if model is None:
            raise KeyError(f"Unknown model '{model_id_or_tag}'.")
        provider = self._providers.get(model.provider, self._providers["ollama"])
        return provider

    async def generate_text(
        self,
        *,
        model_id_or_tag: str,
        prompt: str,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        timeout: float = 120.0,
    ) -> str:
        model = self.resolve_model(model_id_or_tag)
        if model is None:
            raise KeyError(f"Unknown model '{model_id_or_tag}'.")
        if not model.enabled:
            raise ModelProviderError(f"Model '{model.id}' is disabled.")
        provider = self.get_provider(model.id)
        return await provider.generate(
            model=model.ollama_tag,
            prompt=prompt,
            system=system,
            options=options,
            timeout=timeout,
        )

    async def health_check_async(self, model_id_or_tag: str) -> Dict[str, Any]:
        model = self.resolve_model(model_id_or_tag)
        if model is None:
            raise KeyError(f"Unknown model '{model_id_or_tag}'.")
        if not model.enabled:
            return {
                "status": "DISABLED",
                "provider": model.provider,
                "model": model.ollama_tag,
                "message": f"Model '{model.id}' is disabled.",
            }
        provider = self.get_provider(model.id)
        return await provider.health_check(model.ollama_tag)

    def health_check(self, model_id_or_tag: str) -> Dict[str, Any]:
        return self._run_async(self.health_check_async(model_id_or_tag))

    def enabled_chat_model(self) -> RegisteredModel:
        chat = self._models.get("chat")
        if chat and chat.enabled:
            return chat
        for model in self._models.values():
            if model.enabled:
                return model
        raise RuntimeError("No enabled models in catalog")

    def classify_task(self, query: str) -> str:
        text = query or ""
        if _CODE_PATTERNS.search(text):
            return "code"
        if _VISION_PATTERNS.search(text):
            return "vision"
        if _SUMMARY_PATTERNS.search(text):
            return "document_summary"
        return "document_qa"

    def _model_for_task(self, task_type: str) -> Optional[RegisteredModel]:
        for model in self._models.values():
            if model.enabled and task_type in model.task_types:
                return model
        if task_type == "document_summary":
            return self._model_for_task("document_qa") or self._model_for_task("chat")
        if task_type == "vision":
            return None
        return self.enabled_chat_model()

    def resolve_override(self, override: Optional[str]) -> Optional[RegisteredModel]:
        if not override:
            return None
        token = override.strip()
        if not token or token.lower() in {AUTO_SELECT_ID, "automatic", "auto-select"}:
            return None
        resolved = self.resolve_model(token)
        if resolved is not None:
            return resolved
        return RegisteredModel(
            id="override",
            provider="ollama",
            model=token,
            ollama_tag=token,
            display_name=token,
            task_types=[],
            capabilities=[ModelCapability.CHAT, ModelCapability.REASONING],
            description="Caller-supplied model override",
            enabled=True,
        )

    def select(self, query: str, override: Optional[str] = None) -> ModelSelection:
        forced = self.resolve_override(override)
        task_type = self.classify_task(query)

        if forced:
            return ModelSelection(
                task_type=task_type,
                model_id=forced.id,
                ollama_tag=forced.ollama_tag,
                display_name=forced.display_name,
                auto_selected=False,
                reason=f"Manual override → {forced.ollama_tag}",
            )

        chosen = self._model_for_task(task_type)
        if chosen is None:
            fallback = self.enabled_chat_model()
            return ModelSelection(
                task_type=task_type,
                model_id=fallback.id,
                ollama_tag=fallback.ollama_tag,
                display_name=fallback.display_name,
                auto_selected=True,
                reason=(
                    f"Task '{task_type}' has no enabled specialist; "
                    f"using {fallback.ollama_tag}"
                ),
            )

        return ModelSelection(
            task_type=task_type,
            model_id=chosen.id,
            ollama_tag=chosen.ollama_tag,
            display_name=chosen.display_name,
            auto_selected=True,
            reason=f"Task '{task_type}' → {chosen.ollama_tag}",
        )


def _coerce_capability(value: Union[str, ModelCapability]) -> ModelCapability:
    if isinstance(value, ModelCapability):
        return value
    normalized = str(value).strip().lower()
    for capability in ModelCapability:
        if normalized == capability.value:
            return capability
    raise ValueError(f"Unsupported model capability '{value}'.")


model_registry = ModelRegistry()
