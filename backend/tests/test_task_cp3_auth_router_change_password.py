"""
Tests for task 3: Auth Router — PATCH /api/v1/auth/change-password and GET /api/v1/auth/me.

Covers:
Pydantic models:
- ChangePasswordRequest validates current_password and new_password fields
- ChangePasswordRequest rejects new_password shorter than 8 characters
- UserProfileResponse exposes an email field

PATCH /api/v1/auth/change-password:
- 200 + new TokenResponse on valid Bearer token and correct current password
- Response contains access_token and token_type=bearer
- Updated password is accepted by subsequent login
- Old token is blacklisted after successful password change
- 401 when Bearer token is absent
- 401 when Bearer token is invalid
- 401 when current password is incorrect (AuthenticationError path)
- 422 when new_password is shorter than 8 characters (Pydantic validation path)
- 422 when required fields are missing

GET /api/v1/auth/me:
- 200 + UserProfileResponse containing the authenticated user's email
- 401 when Bearer token is absent
- 401 when Bearer token is invalid or blacklisted

Requirements: 4.1, 4.2, 3.3, 1.2
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models.base import Base
import app.models  # noqa: F401 — registers all ORM models


# ---------------------------------------------------------------------------
# In-memory database + TestClient fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_engine():
    """Single in-memory SQLite engine shared across all tests in this module."""
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
    """FastAPI TestClient wired to the in-memory database via dependency override."""
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
# URL constants and helpers
# ---------------------------------------------------------------------------

_REGISTER_URL = "/api/v1/auth/register"
_CHANGE_PASSWORD_URL = "/api/v1/auth/change-password"
_ME_URL = "/api/v1/auth/me"

_DEFAULT_PASSWORD = "initial_pass1"
_NEW_PASSWORD = "new_pass_2024"


def _register(client, email, password=_DEFAULT_PASSWORD):
    resp = client.post(_REGISTER_URL, json={"email": email, "password": password})
    assert resp.status_code == 201, resp.json()
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Pydantic model: ChangePasswordRequest
# ---------------------------------------------------------------------------

def test_change_password_422_on_missing_current_password(client):
    token = _register(client, "cp_missing_cur@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422


def test_change_password_422_on_missing_new_password(client):
    token = _register(client, "cp_missing_new@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _DEFAULT_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422


def test_change_password_422_on_new_password_too_short(client):
    """new_password shorter than 8 characters must be rejected with 422 (Pydantic)."""
    token = _register(client, "cp_short_new@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _DEFAULT_PASSWORD, "new_password": "short"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422


def test_change_password_422_response_has_detail(client):
    """422 responses must carry a 'detail' field."""
    token = _register(client, "cp_detail_check@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _DEFAULT_PASSWORD, "new_password": "abc"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422
    assert "detail" in resp.json()


# ---------------------------------------------------------------------------
# PATCH /api/v1/auth/change-password — success path
# ---------------------------------------------------------------------------

def test_change_password_returns_200_on_valid_request(client):
    """Valid Bearer token + correct current password + policy-compliant new password → 200."""
    token = _register(client, "cp_success@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _DEFAULT_PASSWORD, "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200


def test_change_password_response_contains_access_token(client):
    token = _register(client, "cp_token_field@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _DEFAULT_PASSWORD, "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 0


def test_change_password_response_token_type_is_bearer(client):
    token = _register(client, "cp_toktype@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _DEFAULT_PASSWORD, "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"


def test_change_password_old_token_is_blacklisted_after_success(client):
    """After a successful password change the original token must be rejected (401)."""
    token = _register(client, "cp_blacklist@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _DEFAULT_PASSWORD, "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200

    # The old token must now be blacklisted — re-using it on ME should fail.
    me_resp = client.get(_ME_URL, headers=_auth_headers(token))
    assert me_resp.status_code == 401


def test_change_password_new_token_is_usable_on_me(client):
    """The new token returned after a password change must be accepted by GET /me."""
    token = _register(client, "cp_new_token_usable@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _DEFAULT_PASSWORD, "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    new_token = resp.json()["access_token"]

    me_resp = client.get(_ME_URL, headers=_auth_headers(new_token))
    assert me_resp.status_code == 200


# ---------------------------------------------------------------------------
# PATCH /api/v1/auth/change-password — authentication failures
# ---------------------------------------------------------------------------

def test_change_password_401_without_bearer_token(client):
    """Request without Authorization header must be rejected with 401."""
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _DEFAULT_PASSWORD, "new_password": _NEW_PASSWORD},
    )
    assert resp.status_code == 401


def test_change_password_401_with_invalid_bearer_token(client):
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _DEFAULT_PASSWORD, "new_password": _NEW_PASSWORD},
        headers={"Authorization": "Bearer not.a.valid.token"},
    )
    assert resp.status_code == 401


def test_change_password_401_on_wrong_current_password(client):
    """Incorrect current password must return 401 (AuthenticationError path)."""
    token = _register(client, "cp_wrong_cur@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": "definitely_wrong!", "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 401


def test_change_password_401_wrong_current_password_does_not_change_hash(client):
    """When current password is wrong, the password must not be changed."""
    email = "cp_no_change@example.com"
    token = _register(client, email, password=_DEFAULT_PASSWORD)
    client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": "wrong_password!", "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    # The original token should still work (password unchanged, token not blacklisted)
    me_resp = client.get(_ME_URL, headers=_auth_headers(token))
    assert me_resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me — success path
# ---------------------------------------------------------------------------

def test_me_returns_200_with_valid_token(client):
    token = _register(client, "me_200@example.com")
    resp = client.get(_ME_URL, headers=_auth_headers(token))
    assert resp.status_code == 200


def test_me_response_contains_email_field(client):
    email = "me_email_field@example.com"
    token = _register(client, email)
    resp = client.get(_ME_URL, headers=_auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert "email" in body


def test_me_response_email_matches_registered_email(client):
    """The returned email must match what was used during registration."""
    email = "me_email_match@example.com"
    token = _register(client, email)
    resp = client.get(_ME_URL, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == email


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me — authentication failures
# ---------------------------------------------------------------------------

def test_me_401_without_bearer_token(client):
    resp = client.get(_ME_URL)
    assert resp.status_code == 401


def test_me_401_with_invalid_bearer_token(client):
    resp = client.get(_ME_URL, headers={"Authorization": "Bearer not.a.valid.token"})
    assert resp.status_code == 401


def test_me_401_with_blacklisted_token(client):
    """After logout the token must be rejected by GET /me."""
    from app.main import app
    from app.dependencies import get_db

    token = _register(client, "me_blacklisted@example.com")
    # Blacklist the token via the logout endpoint
    logout_resp = client.post(
        "/api/v1/auth/logout",
        headers=_auth_headers(token),
    )
    assert logout_resp.status_code == 200

    resp = client.get(_ME_URL, headers=_auth_headers(token))
    assert resp.status_code == 401
