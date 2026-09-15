"""Authentication API Endpoints for AegisAI.

Provides:
  - POST /api/v1/auth/login — obtain JWT token with role & clearance tags
  - GET  /api/v1/auth/me — view current user identity and RBAC profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.core.auth import (
    User,
    TokenResponse,
    create_access_token,
    get_current_user,
    ROLE_CLEARANCE_MAP,
)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: Optional[str] = None
    role: Optional[str] = "ENGINEER"


# Preset mock users for SIH demonstration
MOCK_USERS = {
    "admin": {"password": "adminpassword", "role": "ADMIN"},
    "engineer": {"password": "engineerpassword", "role": "ENGINEER"},
    "operator": {"password": "operatorpassword", "role": "OPERATOR"},
    "auditor": {"password": "auditorpassword", "role": "AUDITOR"},
}


@router.post("/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Obtain a signed JWT access token for sovereign session authorization."""
    username_lower = req.username.lower()
    role = req.role.upper() if req.role else "ENGINEER"

    if username_lower in MOCK_USERS:
        preset = MOCK_USERS[username_lower]
        role = preset["role"]

    if role not in ROLE_CLEARANCE_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{role}'. Valid roles: {list(ROLE_CLEARANCE_MAP.keys())}",
        )

    clearance_tags = ROLE_CLEARANCE_MAP[role]
    user = User(username=req.username, role=role, clearance_tags=clearance_tags)

    token = create_access_token(
        data={"sub": user.username, "role": user.role, "clearance_tags": user.clearance_tags}
    )

    return TokenResponse(access_token=token, token_type="bearer", user=user)


@router.get("/auth/me", response_model=User)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Retrieve current logged in user details and active clearance tags."""
    return current_user
