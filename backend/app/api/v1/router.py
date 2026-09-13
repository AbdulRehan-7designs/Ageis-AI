from fastapi import APIRouter
from app.api.v1.endpoints import health, chat, document, audit

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(chat.router, tags=["Chat Agent"])
api_router.include_router(document.router, tags=["Documents"])
api_router.include_router(audit.router, tags=["Audit & Governance"])
