"""Authentication API Endpoints for AegisAI.

Provides:
  - POST /api/v1/auth/login — obtain JWT token with role & clearance tags
  - GET  /api/v1/auth/me — view current user identity and RBAC profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.auth import (
    User,
    TokenResponse,
    create_access_token,
    get_current_user,
)
from app.db.repository import bootstrap_users, ensure_schema, find_user, verify_password
from app.db.session import SessionLocal

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Obtain a signed JWT access token for sovereign session authorization."""
    try:
        ensure_schema()
        with SessionLocal() as db:
            bootstrap_users(db)
            record = find_user(db, req.username)
            if record is None or not verify_password(req.password, record.password_hash):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
            user = User(
                id=str(record.id),
                username=record.username,
                role=record.role,
                clearance_tags=list(record.clearance_tags or []),
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service unavailable") from exc

    token = create_access_token(
        data={"sub": user.username}
    )

    return TokenResponse(access_token=token, token_type="bearer", user=user)


@router.get("/auth/me", response_model=User)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Retrieve current logged in user details and active clearance tags."""
    return current_user
