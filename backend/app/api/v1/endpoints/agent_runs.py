from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.core.auth import User, get_current_user
from app.db.repository import list_runs
from app.db.session import SessionLocal
from app.services.agent_orchestrator import agent_orchestrator

router = APIRouter()


@router.get("/agent-runs", response_model=List[Dict[str, Any]])
async def list_agent_runs(current_user: User = Depends(get_current_user)):
    """Return actual completed orchestrator runs for the authenticated user."""
    if current_user.id:
        with SessionLocal() as db:
            from app.db.repository import find_user
            user = find_user(db, current_user.username)
            if user:
                return list_runs(db, user, include_all=current_user.role == "ADMIN")
    return agent_orchestrator.list_runs(username=current_user.username)
