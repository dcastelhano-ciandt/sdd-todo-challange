"""
Tests for task 4.1: AuthService password hashing and JWT token operations.

Covers:
- hash_password: returns a bcrypt hash distinct from the plaintext
- verify_password: returns True for correct password, False for wrong password
- create_access_token: returns a JWT string with sub, exp, iat, jti claims
- decode_token: returns payload for a valid token
- decode_token: raises AuthenticationError for expired token
- decode_token: raises AuthenticationError for blacklisted (jti in token_blacklist) token
- decode_token: raises AuthenticationError for a malformed/invalid token
"""
import importlib
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_db_session():
    """Return an in-memory SQLite session with all tables created."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.models.base import Base
    import app.models  # noqa: F401 — registers all models

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return Session(engine)


@pytest.fixture
def db():
    session = make_db_session()
    yield session
    session.close()


@pytest.fixture
def auth_service(db):
    from app.services.auth_service import AuthService
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository(db)
    return AuthService(db=db, user_repo=user_repo)


# ---------------------------------------------------------------------------
# Module importability
# ---------------------------------------------------------------------------

def test_auth_service_module_importable():
    mod = importlib.import_module("app.services.auth_service")
    assert mod is not None


def test_auth_service_class_exists():
    from app.services.auth_service import AuthService
    assert AuthService is not None


# ---------------------------------------------------------------------------
# hash_password
# ---------------------------------------------------------------------------

def test_hash_password_returns_string(auth_service):
    result = auth_service.hash_password("MyPassword1!")
    assert isinstance(result, str)


def test_hash_password_is_not_plaintext(auth_service):
    plain = "MyPassword1!"
    hashed = auth_service.hash_password(plain)
    assert hashed != plain


def test_hash_password_starts_with_bcrypt_prefix(auth_service):
    hashed = auth_service.hash_password("SomePass99")
    # passlib bcrypt hashes start with $2b$ or $2a$
    assert hashed.startswith("$2")


def test_hash_password_two_calls_produce_different_hashes(auth_service):
    """bcrypt uses a random salt each time."""
    h1 = auth_service.hash_password("same_password")
    h2 = auth_service.hash_password("same_password")
    assert h1 != h2


# ---------------------------------------------------------------------------
# verify_password
# ---------------------------------------------------------------------------

def test_verify_password_returns_true_for_correct_password(auth_service):
    plain = "CorrectHorseBattery"
    hashed = auth_service.hash_password(plain)
    assert auth_service.verify_password(plain, hashed) is True


def test_verify_password_returns_false_for_wrong_password(auth_service):
    plain = "CorrectHorseBattery"
    hashed = auth_service.hash_password(plain)
    assert auth_service.verify_password("wrong_password", hashed) is False


def test_verify_password_returns_false_for_empty_string(auth_service):
    hashed = auth_service.hash_password("something")
    assert auth_service.verify_password("", hashed) is False


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------

def test_create_access_token_returns_string(auth_service):
    token = auth_service.create_access_token(user_id=str(uuid.uuid4()))
    assert isinstance(token, str)


def test_create_access_token_has_three_parts(auth_service):
    """A JWT is three base64url segments separated by dots."""
    token = auth_service.create_access_token(user_id=str(uuid.uuid4()))
    parts = token.split(".")
    assert len(parts) == 3


def test_create_access_token_contains_sub_claim(auth_service):
    from jose import jwt as jose_jwt
    from app.core.config import settings
    user_id = str(uuid.uuid4())
    token = auth_service.create_access_token(user_id=user_id)
    payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == user_id


def test_create_access_token_contains_exp_claim(auth_service):
    from jose import jwt as jose_jwt
    from app.core.config import settings
    token = auth_service.create_access_token(user_id=str(uuid.uuid4()))
    payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert "exp" in payload


def test_create_access_token_contains_iat_claim(auth_service):
    from jose import jwt as jose_jwt
    from app.core.config import settings
    token = auth_service.create_access_token(user_id=str(uuid.uuid4()))
    payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert "iat" in payload


def test_create_access_token_contains_jti_claim(auth_service):
    from jose import jwt as jose_jwt
    from app.core.config import settings
    token = auth_service.create_access_token(user_id=str(uuid.uuid4()))
    payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert "jti" in payload


def test_create_access_token_jti_is_unique_per_call(auth_service):
    from jose import jwt as jose_jwt
    from app.core.config import settings
    user_id = str(uuid.uuid4())
    t1 = auth_service.create_access_token(user_id=user_id)
    t2 = auth_service.create_access_token(user_id=user_id)
    p1 = jose_jwt.decode(t1, settings.SECRET_KEY, algorithms=["HS256"])
    p2 = jose_jwt.decode(t2, settings.SECRET_KEY, algorithms=["HS256"])
    assert p1["jti"] != p2["jti"]


# ---------------------------------------------------------------------------
# decode_token — valid token
# ---------------------------------------------------------------------------

def test_decode_token_returns_payload_for_valid_token(auth_service):
    user_id = str(uuid.uuid4())
    token = auth_service.create_access_token(user_id=user_id)
    payload = auth_service.decode_token(token)
    assert payload["sub"] == user_id


def test_decode_token_payload_contains_jti(auth_service):
    token = auth_service.create_access_token(user_id=str(uuid.uuid4()))
    payload = auth_service.decode_token(token)
    assert "jti" in payload


# ---------------------------------------------------------------------------
# decode_token — expired token
# ---------------------------------------------------------------------------

def test_decode_token_raises_authentication_error_for_expired_token(auth_service):
    from app.core.exceptions import AuthenticationError
    # Create a token that expired 1 second ago by overriding TTL
    from jose import jwt as jose_jwt
    from app.core.config import settings
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(uuid.uuid4()),
        "exp": now - timedelta(seconds=1),
        "iat": now - timedelta(minutes=30),
        "jti": str(uuid.uuid4()),
    }
    expired_token = jose_jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")
    with pytest.raises(AuthenticationError):
        auth_service.decode_token(expired_token)


# ---------------------------------------------------------------------------
# decode_token — malformed token
# ---------------------------------------------------------------------------

def test_decode_token_raises_authentication_error_for_malformed_token(auth_service):
    from app.core.exceptions import AuthenticationError
    with pytest.raises(AuthenticationError):
        auth_service.decode_token("not.a.valid.jwt.token")


def test_decode_token_raises_authentication_error_for_empty_token(auth_service):
    from app.core.exceptions import AuthenticationError
    with pytest.raises(AuthenticationError):
        auth_service.decode_token("")


# ---------------------------------------------------------------------------
# decode_token — blacklisted token
# ---------------------------------------------------------------------------

def test_decode_token_raises_authentication_error_for_blacklisted_jti(auth_service, db):
    from app.core.exceptions import AuthenticationError
    from app.models.token_blacklist import TokenBlacklist

    user_id = str(uuid.uuid4())
    token = auth_service.create_access_token(user_id=user_id)

    # Extract jti and blacklist it
    from jose import jwt as jose_jwt
    from app.core.config import settings
    payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    jti = payload["jti"]

    blacklist_entry = TokenBlacklist(
        jti=jti,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db.add(blacklist_entry)
    db.commit()

    with pytest.raises(AuthenticationError):
        auth_service.decode_token(token)
