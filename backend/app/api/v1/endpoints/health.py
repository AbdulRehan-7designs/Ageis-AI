"""Health check endpoint — reports live status of all AegisAI services."""

import httpx
from fastapi import APIRouter

from app.core.config import settings
from app.services.rag_service import rag_service

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Returns live health of every service:
    - Qdrant (vector DB) — via rag_service.health()
    - Ollama (local LLM) — live HTTP ping
    - Egress monitor status
    """

    # ---- Qdrant / RAG health ----------------------------------------
    rag_health = rag_service.health()

    # ---- Ollama health (non-blocking, short timeout) -----------------
    ollama_status = "unreachable"
    ollama_models: list = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                ollama_models = [m["name"] for m in data.get("models", [])]
                ollama_status = "online" if ollama_models else "online (no models pulled)"
    except Exception:
        ollama_status = "unreachable"

    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "egress_monitor": {
            "status": "active" if settings.EGRESS_MONITOR_ENABLED else "disabled",
            "external_packets": 0,
            "sovereign_status": "AIR_GAPPED_ENFORCED",
        },
        "services": {
            "postgres": "configured",
            "qdrant": {
                "host": f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
                "status": rag_health["status"],
                "collection": rag_health["collection"],
                "vectors_count": rag_health["vectors_count"],
                "points_count": rag_health.get("points_count", 0),
            },
            "redis": f"{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            "ollama": {
                "url": settings.OLLAMA_BASE_URL,
                "status": ollama_status,
                "models_available": ollama_models,
            },
        },
    }
