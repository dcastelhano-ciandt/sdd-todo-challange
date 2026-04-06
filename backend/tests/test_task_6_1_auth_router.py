"""
Tests for task 6.1: Auth router — Pydantic schemas + HTTP endpoints.

Covers:
POST /api/v1/auth/register
- 201 + TokenResponse on valid registration
- 409 on duplicate email
- 422 on missing/malformed email
- 422 on password shorter than 8 characters
- 422 on missing fields

POST /api/v1/auth/login
- 200 + TokenResponse on valid credentials
- 401 on wrong password
- 401 on unknown email
- 422 on missing fields

POST /api/v1/auth/logout
- 200 + MessageResponse when authenticated
- 401 when no token provided
- 401 when token is invalid

Pydantic schemas:
- RegisterRequest requires EmailStr and password min_length=8
- LoginRequest requires email and password
- TokenResponse has access_token and token_type fields
- MessageResponse has a message field
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.base import Base
import app.models  # noqa: F401 — registers all ORM models


# ---------------------------------------------------------------------------
# App + client fixtures using an in-memory SQLite database
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_engine():
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def client(test_engine):
    """TestClient wired to an in-memory database via dependency override."""
    from app.main import app
    from app.dependencies import get_db

    def override_get_db():
        session = Session(test_engine)
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REGISTER_URL = "/api/v1/auth/register"
_LOGIN_URL = "/api/v1/auth/login"
_LOGOUT_URL = "/api/v1/auth/logout"

_VALID_EMAIL = "user6_1@example.com"
_VALID_PASSWORD = "secret123"


def _register_and_get_token(client, email=_VALID_EMAIL, password=_VALID_PASSWORD):
    """Register a new user and return the access token string."""
    resp = client.post(_REGISTER_URL, json={"email": email, "password": password})
    assert resp.status_code == 201, resp.json()
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Pydantic schema: RegisterRequest validation
# ---------------------------------------------------------------------------

def test_register_422_on_missing_email(client):
    resp = client.post(_REGISTER_URL, json={"password": _VALID_PASSWORD})
    assert resp.status_code == 422


def test_register_422_on_invalid_email_format(client):
    resp = client.post(_REGISTER_URL, json={"email": "not-an-email", "password": _VALID_PASSWORD})
    assert resp.status_code == 422


def test_register_422_on_missing_password(client):
    resp = client.post(_REGISTER_URL, json={"email": "other6@example.com"})
    assert resp.status_code == 422


def test_register_422_on_password_too_short(client):
    resp = client.post(_REGISTER_URL, json={"email": "short6@example.com", "password": "abc"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/auth/register — success
# ---------------------------------------------------------------------------

def test_register_returns_201(client):
    resp = client.post(_REGISTER_URL, json={"email": _VALID_EMAIL, "password": _VALID_PASSWORD})
    assert resp.status_code == 201


def test_register_response_contains_access_token(client):
    resp = client.post(
        _REGISTER_URL, json={"email": "tokencheck6@example.com", "password": _VALID_PASSWORD}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 0


def test_register_response_token_type_is_bearer(client):
    resp = client.post(
        _REGISTER_URL, json={"email": "bearertype6@example.com", "password": _VALID_PASSWORD}
    )
    assert resp.status_code == 201
    assert resp.json()["token_type"] == "bearer"


# ---------------------------------------------------------------------------
# POST /api/v1/auth/register — conflict
# ---------------------------------------------------------------------------

def test_register_409_on_duplicate_email(client):
    email = "dup6@example.com"
    client.post(_REGISTER_URL, json={"email": email, "password": _VALID_PASSWORD})
    resp = client.post(_REGISTER_URL, json={"email": email, "password": _VALID_PASSWORD})
    assert resp.status_code == 409


def test_register_409_response_has_detail(client):
    email = "dup6b@example.com"
    client.post(_REGISTER_URL, json={"email": email, "password": _VALID_PASSWORD})
    resp = client.post(_REGISTER_URL, json={"email": email, "password": _VALID_PASSWORD})
    assert resp.status_code == 409
    assert "detail" in resp.json()


# ---------------------------------------------------------------------------
# Pydantic schema: LoginRequest validation
# ---------------------------------------------------------------------------

def test_login_422_on_missing_email(client):
    resp = client.post(_LOGIN_URL, json={"password": _VALID_PASSWORD})
    assert resp.status_code == 422


def test_login_422_on_missing_password(client):
    resp = client.post(_LOGIN_URL, json={"email": _VALID_EMAIL})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login — success
# ---------------------------------------------------------------------------

def test_login_returns_200(client):
    # Ensure user exists
    client.post(_REGISTER_URL, json={"email": "login6@example.com", "password": _VALID_PASSWORD})
    resp = client.post(_LOGIN_URL, json={"email": "login6@example.com", "password": _VALID_PASSWORD})
    assert resp.status_code == 200


def test_login_response_contains_access_token(client):
    client.post(_REGISTER_URL, json={"email": "login6b@example.com", "password": _VALID_PASSWORD})
    resp = client.post(_LOGIN_URL, json={"email": "login6b@example.com", "password": _VALID_PASSWORD})
    body = resp.json()
    assert "access_token" in body
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 0


def test_login_response_token_type_is_bearer(client):
    client.post(_REGISTER_URL, json={"email": "login6c@example.com", "password": _VALID_PASSWORD})
    resp = client.post(_LOGIN_URL, json={"email": "login6c@example.com", "password": _VALID_PASSWORD})
    assert resp.json()["token_type"] == "bearer"


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login — failures
# ---------------------------------------------------------------------------

def test_login_401_on_wrong_password(client):
    client.post(_REGISTER_URL, json={"email": "wrongpwd6@example.com", "password": _VALID_PASSWORD})
    resp = client.post(_LOGIN_URL, json={"email": "wrongpwd6@example.com", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_login_401_on_unknown_email(client):
    resp = client.post(_LOGIN_URL, json={"email": "nobody6@example.com", "password": _VALID_PASSWORD})
    assert resp.status_code == 401


def test_login_401_response_does_not_disclose_field(client):
    """Both wrong email and wrong password must return the same 401 — no disclosure."""
    client.post(_REGISTER_URL, json={"email": "nodisclose6@example.com", "password": _VALID_PASSWORD})
    resp_wrong_pwd = client.post(
        _LOGIN_URL, json={"email": "nodisclose6@example.com", "password": "wrongpassword"}
    )
    resp_wrong_email = client.post(
        _LOGIN_URL, json={"email": "nobody6@example.com", "password": _VALID_PASSWORD}
    )
    assert resp_wrong_pwd.status_code == 401
    assert resp_wrong_email.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/auth/logout — authenticated
# ---------------------------------------------------------------------------

def test_logout_returns_200_with_valid_token(client):
    token = _register_and_get_token(client, email="logout6@example.com")
    resp = client.post(_LOGOUT_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_logout_response_contains_message(client):
    token = _register_and_get_token(client, email="logout6b@example.com")
    resp = client.post(_LOGOUT_URL, headers={"Authorization": f"Bearer {token}"})
    body = resp.json()
    assert "message" in body
    assert isinstance(body["message"], str)


def test_logout_invalidates_token(client):
    """After logout the same token must not be usable again (blacklisted)."""
    token = _register_and_get_token(client, email="logout6c@example.com")
    client.post(_LOGOUT_URL, headers={"Authorization": f"Bearer {token}"})
    # A second logout attempt with the same token should return 401 (blacklisted).
    resp = client.post(_LOGOUT_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/auth/logout — unauthenticated
# ---------------------------------------------------------------------------

def test_logout_401_without_token(client):
    resp = client.post(_LOGOUT_URL)
    assert resp.status_code == 401


def test_logout_401_with_invalid_token(client):
    resp = client.post(_LOGOUT_URL, headers={"Authorization": "Bearer not.a.valid.token"})
    assert resp.status_code == 401
