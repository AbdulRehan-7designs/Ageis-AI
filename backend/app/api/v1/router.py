from fastapi import APIRouter
from app.api.v1.endpoints import agent_runs, health, chat, document, audit, auth, sandbox, models, reports, conversations

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(models.router, tags=["Model Registry"])
api_router.include_router(auth.router, tags=["Authentication & RBAC"])
api_router.include_router(chat.router, tags=["Chat Agent"])
api_router.include_router(document.router, tags=["Documents"])
api_router.include_router(audit.router, tags=["Audit & Governance"])
api_router.include_router(sandbox.router, tags=["Code Execution Sandbox"])
api_router.include_router(reports.router, tags=["Engineering Reports"])
api_router.include_router(agent_runs.router, tags=["Agent Runs"])
api_router.include_router(conversations.router, tags=["Conversations"])
