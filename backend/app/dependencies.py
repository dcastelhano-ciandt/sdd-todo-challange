"""
FastAPI dependency providers shared across routers.

get_db          — yields a SQLAlchemy Session and closes it after the request.
get_auth_service — provides an AuthService instance wired to the current db session.
get_current_user — extracts and validates the JWT Bearer token; returns UserContext.
UserContext      — dataclass holding the authenticated user_id and jti.
"""
from dataclasses import dataclass
from typing import Generator

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError

# Module-level engine instance, replaceable in tests.
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# ---------------------------------------------------------------------------
# OAuth2 scheme
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# UserContext
# ---------------------------------------------------------------------------

@dataclass
class UserContext:
    """Holds the authenticated user identity extracted from a validated JWT."""
    user_id: str
    jti: str


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# AuthService factory
# ---------------------------------------------------------------------------

def get_auth_service(db: Session = Depends(get_db)):
    """Provide an AuthService instance bound to the current request session."""
    from app.services.auth_service import AuthService
    from app.repositories.user_repository import UserRepository
    return AuthService(db=db, user_repo=UserRepository(db))


# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service=Depends(get_auth_service),
) -> UserContext:
    """FastAPI dependency that validates the Bearer JWT and returns UserContext.

    Raises HTTPException(401) for any invalid, expired, or blacklisted token.
    """
    try:
        payload = auth_service.decode_token(token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    jti = payload.get("jti")

    if not user_id or not jti:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserContext(user_id=user_id, jti=jti)
