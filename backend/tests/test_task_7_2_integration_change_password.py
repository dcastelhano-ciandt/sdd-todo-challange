"""
Integration tests for task 7.2: backend integration tests for the new
change-password and /me endpoints.

Each test exercises the full HTTP stack through a FastAPI TestClient wired to an
in-memory SQLite database.  Where the task requires it, assertions are also made
directly against the database (hashed_password column, token_blacklist table) so
that the integration between the HTTP layer, the service layer, and the repository
layer is validated end-to-end.

Covers:
- PATCH /api/v1/auth/change-password with a valid Bearer token and correct
  current password: HTTP 200, new token in response, hashed_password updated
  in DB, old JTI present in token_blacklist.
- PATCH /api/v1/auth/change-password with a correct token but wrong current
  password: HTTP 401, hashed_password unchanged in DB.
- PATCH /api/v1/auth/change-password without a Bearer token: HTTP 401.
- Presenting the old token after a successful password change: HTTP 401
  (token blacklisted).
- GET /api/v1/auth/me with a valid token: HTTP 200, correct email in response.

Requirements: 4.1, 4.2, 4.3, 5.4, 1.2
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.models.base import Base
import app.models  # noqa: F401 — registers all ORM models


# ---------------------------------------------------------------------------
# Fixtures
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


@pytest.fixture
def db_session(test_engine):
    """A short-lived SQLAlchemy session used to inspect DB state within a test.

    Using a separate session from the one the app uses ensures we read committed
    data (SQLite with StaticPool shares the same connection, so we can see
    committed rows immediately).
    """
    session = Session(test_engine)
    yield session
    session.close()


# ---------------------------------------------------------------------------
# URL constants and helpers
# ---------------------------------------------------------------------------

_REGISTER_URL = "/api/v1/auth/register"
_CHANGE_PASSWORD_URL = "/api/v1/auth/change-password"
_ME_URL = "/api/v1/auth/me"

_INITIAL_PASSWORD = "initial_pass1"
_NEW_PASSWORD = "new_pass_2024"


def _register(client, email, password=_INITIAL_PASSWORD):
    """Register a new user and return the access token."""
    resp = client.post(_REGISTER_URL, json={"email": email, "password": password})
    assert resp.status_code == 201, resp.json()
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _decode_jti(token):
    """Decode the JTI claim from a JWT without verifying the signature.

    Used only to extract the JTI for blacklist assertions — the signature was
    already validated by the endpoint.
    """
    from jose import jwt as jose_jwt
    from app.core.config import settings

    payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    return payload["jti"]


# ---------------------------------------------------------------------------
# PATCH /api/v1/auth/change-password — valid token + correct password (req 4.1)
# ---------------------------------------------------------------------------

def test_change_password_returns_http_200_on_valid_request(client):
    """Valid Bearer token + correct current password + policy-compliant new password
    must return HTTP 200."""
    token = _register(client, "int72_200@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _INITIAL_PASSWORD, "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200


def test_change_password_response_contains_new_access_token(client):
    """The 200 response must contain a non-empty access_token string."""
    token = _register(client, "int72_token@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _INITIAL_PASSWORD, "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 0


def test_change_password_response_new_token_differs_from_old_token(client):
    """The returned token must be a fresh token, different from the original."""
    token = _register(client, "int72_newtoken@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _INITIAL_PASSWORD, "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    new_token = resp.json()["access_token"]
    assert new_token != token


def test_change_password_hashed_password_updated_in_db(client, db_session):
    """After a successful password change the hashed_password column in the users
    table must differ from the original value (req 4.1)."""
    from app.models.user import User
    from jose import jwt as jose_jwt
    from app.core.config import settings

    token = _register(client, "int72_dbhash@example.com")

    # Capture the user_id from the token before the password change.
    payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    user_id = payload["sub"]

    # Read the original hash directly from the database.
    original_user = db_session.get(User, user_id)
    assert original_user is not None
    original_hash = original_user.hashed_password

    # Perform the password change via HTTP.
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _INITIAL_PASSWORD, "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200

    # Expire the local cache and re-read from the database.
    db_session.expire_all()
    updated_user = db_session.get(User, user_id)
    assert updated_user.hashed_password != original_hash, (
        "hashed_password must be updated in the database after a successful "
        "password change"
    )


def test_change_password_old_jti_present_in_token_blacklist(client, db_session):
    """After a successful password change the old JTI must be recorded in the
    token_blacklist table (req 5.4)."""
    from app.models.token_blacklist import TokenBlacklist

    token = _register(client, "int72_blacklist@example.com")
    old_jti = _decode_jti(token)

    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _INITIAL_PASSWORD, "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200

    # The old JTI must now be present in the token_blacklist table.
    entry = db_session.query(TokenBlacklist).filter(
        TokenBlacklist.jti == old_jti
    ).first()
    assert entry is not None, (
        f"Old JTI '{old_jti}' must be present in token_blacklist after password change"
    )


# ---------------------------------------------------------------------------
# PATCH /api/v1/auth/change-password — correct token, wrong current password
# (req 4.2)
# ---------------------------------------------------------------------------

def test_change_password_returns_http_401_on_wrong_current_password(client):
    """Correct Bearer token but wrong current password must return HTTP 401."""
    token = _register(client, "int72_wrong_pass@example.com")
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": "definitely_wrong!", "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 401


def test_change_password_hashed_password_unchanged_on_wrong_current_password(
    client, db_session
):
    """When the current password is incorrect the hashed_password in the users
    table must remain unchanged (req 4.2)."""
    from app.models.user import User
    from jose import jwt as jose_jwt
    from app.core.config import settings

    token = _register(client, "int72_unchanged_hash@example.com")

    payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    user_id = payload["sub"]

    original_user = db_session.get(User, user_id)
    original_hash = original_user.hashed_password

    # Attempt password change with the wrong current password.
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": "wrong_password!", "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 401

    # The hash must be identical to what it was before the failed attempt.
    db_session.expire_all()
    unchanged_user = db_session.get(User, user_id)
    assert unchanged_user.hashed_password == original_hash, (
        "hashed_password must not change when the current password is wrong"
    )


# ---------------------------------------------------------------------------
# PATCH /api/v1/auth/change-password — no Bearer token (req 4.3)
# ---------------------------------------------------------------------------

def test_change_password_returns_http_401_without_bearer_token(client):
    """A request that omits the Authorization header must be rejected with HTTP 401."""
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _INITIAL_PASSWORD, "new_password": _NEW_PASSWORD},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Old token is rejected after successful password change (req 5.4)
# ---------------------------------------------------------------------------

def test_old_token_returns_http_401_after_successful_password_change(client):
    """Presenting the original token after a successful password change must return
    HTTP 401 because the JTI has been blacklisted (req 5.4)."""
    token = _register(client, "int72_oldtoken@example.com")

    # Perform a successful password change.
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _INITIAL_PASSWORD, "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200

    # Using the old token on any protected endpoint must now return 401.
    me_resp = client.get(_ME_URL, headers=_auth_headers(token))
    assert me_resp.status_code == 401, (
        "The old token must be rejected (blacklisted) after a successful password change"
    )


def test_old_token_rejected_on_change_password_endpoint_after_successful_change(
    client,
):
    """The old token must also be rejected on the change-password endpoint itself
    after it has been blacklisted."""
    token = _register(client, "int72_oldtoken2@example.com")

    # First password change — succeeds.
    resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _INITIAL_PASSWORD, "new_password": _NEW_PASSWORD},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200

    # Attempt to use the original token again on the same endpoint.
    second_resp = client.patch(
        _CHANGE_PASSWORD_URL,
        json={"current_password": _NEW_PASSWORD, "new_password": "another_pass99"},
        headers=_auth_headers(token),
    )
    assert second_resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me — valid token (req 1.2)
# ---------------------------------------------------------------------------

def test_me_returns_http_200_with_valid_token(client):
    """GET /api/v1/auth/me with a valid Bearer token must return HTTP 200."""
    token = _register(client, "int72_me_200@example.com")
    resp = client.get(_ME_URL, headers=_auth_headers(token))
    assert resp.status_code == 200


def test_me_response_contains_email_field(client):
    """The /me response body must contain an 'email' key."""
    token = _register(client, "int72_me_field@example.com")
    resp = client.get(_ME_URL, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert "email" in resp.json()


def test_me_response_email_matches_registered_email(client):
    """The email returned by GET /api/v1/auth/me must match the registered address
    (req 1.2)."""
    email = "int72_me_match@example.com"
    token = _register(client, email)
    resp = client.get(_ME_URL, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == email


def test_me_returns_http_401_without_bearer_token(client):
    """GET /api/v1/auth/me without an Authorization header must return HTTP 401."""
    resp = client.get(_ME_URL)
    assert resp.status_code == 401
