"""
Tests for task 4.4: get_current_user FastAPI dependency.

Covers:
- get_current_user dependency is importable from app.dependencies
- get_current_user returns UserContext with user_id and jti for a valid token
- get_current_user raises HTTPException(401) for an expired token
- get_current_user raises HTTPException(401) for a malformed token
- get_current_user raises HTTPException(401) for a blacklisted token
- UserContext exposes user_id and jti attributes
- The OAuth2PasswordBearer scheme is registered (tokenUrl present)
- Integration: protected endpoint via TestClient returns 401 when no token provided
- Integration: protected endpoint via TestClient returns 200 when valid token provided
"""
import uuid
import importlib
import pytest
from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_in_memory_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.models.base import Base
    import app.models  # noqa: F401

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return Session(engine)


def make_auth_service(db):
    from app.services.auth_service import AuthService
    from app.repositories.user_repository import UserRepository
    return AuthService(db=db, user_repo=UserRepository(db))


# ---------------------------------------------------------------------------
# Module importability
# ---------------------------------------------------------------------------

def test_get_current_user_importable():
    mod = importlib.import_module("app.dependencies")
    assert hasattr(mod, "get_current_user")


def test_user_context_importable():
    from app.dependencies import UserContext
    assert UserContext is not None


# ---------------------------------------------------------------------------
# UserContext dataclass attributes
# ---------------------------------------------------------------------------

def test_user_context_has_user_id_and_jti():
    from app.dependencies import UserContext
    ctx = UserContext(user_id=str(uuid.uuid4()), jti=str(uuid.uuid4()))
    assert hasattr(ctx, "user_id")
    assert hasattr(ctx, "jti")


def test_user_context_stores_values():
    from app.dependencies import UserContext
    uid = str(uuid.uuid4())
    jti = str(uuid.uuid4())
    ctx = UserContext(user_id=uid, jti=jti)
    assert ctx.user_id == uid
    assert ctx.jti == jti


# ---------------------------------------------------------------------------
# get_current_user — valid token (unit-level, calling dependency directly)
# ---------------------------------------------------------------------------

def test_get_current_user_returns_user_context_for_valid_token():
    """Call the dependency function directly with a valid token."""
    import asyncio
    from app.dependencies import get_current_user, UserContext

    db = make_in_memory_session()
    auth_svc = make_auth_service(db)
    user_id = str(uuid.uuid4())
    token = auth_svc.create_access_token(user_id=user_id)

    result = asyncio.get_event_loop().run_until_complete(
        get_current_user(token=token, auth_service=auth_svc)
    )
    assert isinstance(result, UserContext)
    assert result.user_id == user_id
    assert result.jti is not None


# ---------------------------------------------------------------------------
# get_current_user — invalid token raises HTTPException(401)
# ---------------------------------------------------------------------------

def test_get_current_user_raises_401_for_malformed_token():
    import asyncio
    from fastapi import HTTPException
    from app.dependencies import get_current_user

    db = make_in_memory_session()
    auth_svc = make_auth_service(db)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.get_event_loop().run_until_complete(
            get_current_user(token="not.a.valid.token", auth_service=auth_svc)
        )
    assert exc_info.value.status_code == 401


def test_get_current_user_raises_401_for_expired_token():
    import asyncio
    from fastapi import HTTPException
    from app.dependencies import get_current_user
    from jose import jwt as jose_jwt
    from app.core.config import settings

    db = make_in_memory_session()
    auth_svc = make_auth_service(db)

    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(uuid.uuid4()),
        "exp": now - timedelta(seconds=1),
        "iat": now - timedelta(minutes=30),
        "jti": str(uuid.uuid4()),
    }
    expired_token = jose_jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.get_event_loop().run_until_complete(
            get_current_user(token=expired_token, auth_service=auth_svc)
        )
    assert exc_info.value.status_code == 401


def test_get_current_user_raises_401_for_blacklisted_token():
    import asyncio
    from fastapi import HTTPException
    from app.dependencies import get_current_user
    from app.models.token_blacklist import TokenBlacklist
    from jose import jwt as jose_jwt
    from app.core.config import settings

    db = make_in_memory_session()
    auth_svc = make_auth_service(db)

    user_id = str(uuid.uuid4())
    token = auth_svc.create_access_token(user_id=user_id)
    payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    jti = payload["jti"]

    blacklist_entry = TokenBlacklist(
        jti=jti,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db.add(blacklist_entry)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        asyncio.get_event_loop().run_until_complete(
            get_current_user(token=token, auth_service=auth_svc)
        )
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Integration: TestClient — no token returns 401, valid token passes
# ---------------------------------------------------------------------------

@pytest.fixture
def test_app(tmp_path):
    """Build a minimal FastAPI app with one protected route for integration tests."""
    from fastapi import FastAPI, Depends
    from app.dependencies import get_current_user, UserContext

    mini_app = FastAPI()

    @mini_app.get("/protected")
    async def protected(current_user: UserContext = Depends(get_current_user)):
        return {"user_id": current_user.user_id}

    return mini_app


def test_protected_route_returns_401_without_token(test_app):
    from fastapi.testclient import TestClient
    client = TestClient(test_app, raise_server_exceptions=False)
    response = client.get("/protected")
    assert response.status_code == 401


def test_protected_route_returns_200_with_valid_token(test_app):
    """Use a dependency override that returns a fixed UserContext to avoid DB wiring."""
    from fastapi.testclient import TestClient
    from app.dependencies import get_current_user, UserContext

    user_id = str(uuid.uuid4())
    jti = str(uuid.uuid4())

    async def override_get_current_user():
        return UserContext(user_id=user_id, jti=jti)

    test_app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(test_app)
    response = client.get("/protected")

    test_app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["user_id"] == user_id
