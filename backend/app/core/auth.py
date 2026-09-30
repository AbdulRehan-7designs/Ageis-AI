"""Authentication & Role-Based Access Control (RBAC) Module for AegisAI.

Provides lightweight JWT generation, verification, and FastAPI security dependencies:
  - User identity model (username, role, clearance_tags)
  - Pre-defined role-to-clearance mapping (ADMIN, ENGINEER, OPERATOR, AUDITOR)
  - OAuth2 / HTTP Bearer token dependency (`get_current_user`)
  - Role enforcement dependency (`require_role`)
"""

import base64
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

# Secret key for JWT signing — loaded from settings or fallback
SECRET_KEY = getattr(settings, "JWT_SECRET_KEY", None) or settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Role to clearance tags mapping
ROLE_CLEARANCE_MAP: Dict[str, List[str]] = {
    "ADMIN": ["SECRET", "CONFIDENTIAL", "RESTRICTED", "INTERNAL", "PUBLIC"],
    "ENGINEER": ["CONFIDENTIAL", "RESTRICTED", "INTERNAL", "PUBLIC"],
    "OPERATOR": ["RESTRICTED", "INTERNAL", "PUBLIC"],
    "AUDITOR": ["INTERNAL", "PUBLIC"],
    "PUBLIC": ["PUBLIC"],
}


class User(BaseModel):
    id: str | None = None
    username: str
    role: str
    clearance_tags: List[str]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


# Pure Python HMAC-SHA256 JWT implementation (no extra dependencies required)
def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _b64url_decode(data_str: str) -> bytes:
    padding = '=' * (4 - (len(data_str) % 4))
    return base64.urlsafe_b64decode(data_str + padding)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": int(expire.timestamp()), "iat": int(now.timestamp())})

    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _b64url_encode(json.dumps(to_encode, separators=(',', ':')).encode('utf-8'))

    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token structure")

        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()

        if not hmac.compare_digest(_b64url_encode(expected_sig), sig_b64):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token signature verification failed")

        payload = json.loads(_b64url_decode(payload_b64).decode('utf-8'))

        if "exp" in payload and payload["exp"] < time.time():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

        return payload
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token decode error: {str(e)}")


security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> User:
    """FastAPI dependency for authenticating user and extracting RBAC clearance tags."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token identity missing")

    # Reload the identity from PostgreSQL so role and clearance cannot be
    # changed by client-supplied token claims or stale frontend state.
    try:
        from app.db.repository import find_user
        from app.db.repository import ensure_schema
        from app.db.session import SessionLocal
        ensure_schema()
        with SessionLocal() as db:
            record = find_user(db, username)
            if record is None:
                if settings.ENVIRONMENT != "development" or not settings.ALLOW_DEVELOPMENT_IDENTITY_FALLBACK:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User session is no longer valid")
                # Existing integration tests and local signed-token workflows
                # can run without provisioning a PostgreSQL user. Login in
                # every deployed environment still requires a persisted user.
                role = str(payload.get("role") or "ENGINEER").upper()
                logger.warning("Using development signed-token compatibility identity for %s", username)
                return User(
                    username=username,
                    role=role,
                    clearance_tags=list(ROLE_CLEARANCE_MAP.get(role, [])),
                )
            return User(
                id=str(record.id),
                username=record.username,
                role=record.role,
                clearance_tags=list(record.clearance_tags or []),
            )
    except HTTPException:
        raise
    except Exception as exc:
        if settings.ENVIRONMENT == "development" and settings.ALLOW_DEVELOPMENT_IDENTITY_FALLBACK:
            role = str(payload.get("role") or "ENGINEER").upper()
            logger.warning("Using development signed-token compatibility identity for %s: %s", username, exc)
            return User(
                username=username,
                role=role,
                clearance_tags=list(ROLE_CLEARANCE_MAP.get(role, [])),
            )
        logger.error("Unable to load authenticated identity: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service unavailable")


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[User]:
    """Return an authenticated user when credentials are supplied, otherwise public context."""
    if not credentials:
        return None
    return get_current_user(credentials)


def require_role(allowed_roles: List[str]):
    """Factory dependency for role-based endpoint restriction."""

    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in [r.upper() for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user.role}' lacks permission. Required: {allowed_roles}",
            )
        return user

    return role_checker
