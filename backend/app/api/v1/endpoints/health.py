"""Health and sovereignty status with role-appropriate disclosure."""

import socket

import httpx
from fastapi import APIRouter, Depends

from app.core.auth import User, get_optional_current_user
from app.core.config import settings
from app.services.egress_guard import egress_guard
from app.services.model_registry import model_registry
from app.services.rag_service import rag_service

router = APIRouter()


def _tcp_status(host: str, port: int) -> str:
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return "online"
    except OSError:
        return "offline"


@router.get("/egress")
async def egress_status(current_user: User | None = Depends(get_optional_current_user)):
    snapshot = egress_guard.snapshot()
    if current_user is None:
        return {"status": "available", "sovereign_status": snapshot["sovereign_status"]}
    result = {
        "status": "active" if snapshot["enabled"] else "disabled",
        "sovereign_status": snapshot["sovereign_status"],
        "blocked_count": snapshot["blocked_count"],
        "allowed_count": snapshot["allowed_count"],
    }
    if current_user.role == "ADMIN":
        result["events"] = snapshot.get("events", [])
    return result


@router.get("/health")
async def health_check(current_user: User | None = Depends(get_optional_current_user)):
    rag_health = rag_service.health()
    egress = egress_guard.snapshot(event_limit=8)
    ollama_status = "unreachable"
    ollama_models: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                ollama_models = [model["name"] for model in response.json().get("models", [])]
                ollama_status = "online" if ollama_models else "online (no models pulled)"
    except Exception:
        ollama_status = "unreachable"

    postgres_status = _tcp_status(settings.POSTGRES_SERVER, settings.POSTGRES_PORT)
    redis_status = _tcp_status(settings.REDIS_HOST, settings.REDIS_PORT)
    service_statuses = [postgres_status, redis_status, rag_health["status"], "online" if ollama_status.startswith("online") else "offline"]
    overall_status = "healthy" if all(value == "online" for value in service_statuses) else (
        "degraded" if any(value in {"online", "degraded", "online (no models pulled)"} for value in service_statuses) else "unavailable"
    )
    response = {
        "status": overall_status,
        "system": settings.PROJECT_NAME,
        "egress_monitor": {
            "status": "active" if egress["enabled"] else "disabled",
            "sovereign_status": egress["sovereign_status"],
        },
    }
    if current_user is None:
        return response

    response["egress_monitor"].update({
        "enforcing": egress["enforcing"],
        "external_packets": egress["blocked_count"],
        "allowed_internal": egress["allowed_count"],
    })
    response["services"] = {
        "qdrant": {"status": rag_health["status"]},
        "redis": {"status": redis_status},
        "ollama": {"status": ollama_status},
    }
    if current_user.role == "ADMIN":
        response["environment"] = settings.ENVIRONMENT
        response["services"].update({
            "postgres": {"host": f"{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}", "status": postgres_status},
            "qdrant": {
                "host": f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
                "status": rag_health["status"],
                "collection": rag_health["collection"],
                "vectors_count": rag_health["vectors_count"],
                "points_count": rag_health.get("points_count", 0),
            },
            "redis": {"host": f"{settings.REDIS_HOST}:{settings.REDIS_PORT}", "status": redis_status},
            "ollama": {"url": settings.OLLAMA_BASE_URL, "status": ollama_status, "models_available": ollama_models},
            "model_registry": {
                "enabled": [
                    {"id": model.id, "ollama_tag": model.ollama_tag, "task_types": model.task_types}
                    for model in model_registry.list_models()
                ]
            },
        })
    return response
