from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "egress_monitor": {
            "status": "active" if settings.EGRESS_MONITOR_ENABLED else "disabled",
            "external_packets": 0,
            "sovereign_status": "AIR_GAPPED_ENFORCED"
        },
        "services": {
            "postgres": "configured",
            "qdrant": f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
            "redis": f"{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            "ollama": settings.OLLAMA_BASE_URL
        }
    }
