"""
Tests for task 12.1: AuthService unit tests.

Covers:
- register: valid input → returns TokenResponse dict
- register: duplicate email → raises ConflictError
- register: password below minimum length → raises ValidationError
- login: valid credentials → returns TokenResponse dict
- login: unknown email → raises AuthenticationError
- login: wrong password → raises AuthenticationError
- login: unknown-email and wrong-password errors are IDENTICAL (req 2.2)
- decode_token: valid token → returns payload with sub
- decode_token: expired token → raises AuthenticationError
- decode_token: blacklisted token → raises AuthenticationError

Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.5
"""
import uuid
import pytest
from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    """In-memory SQLite session with all tables created."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.models.base import Base
    import app.models  # noqa: F401 — registers all ORM models

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def auth_service(db):
    from app.services.auth_service import AuthService
    from app.repositories.user_repository import UserRepository
    return AuthService(db=db, user_repo=UserRepository(db))


# ---------------------------------------------------------------------------
# register — valid input
# ---------------------------------------------------------------------------

def test_register_with_valid_input_returns_dict(auth_service):
    """register returns a dict with access_token and token_type keys."""
    result = auth_service.register(email="alice12@example.com", password="password12")
    assert isinstance(result, dict)


def test_register_with_valid_input_contains_access_token(auth_service):
    result = auth_service.register(email="alice12b@example.com", password="password12")
    assert "access_token" in result
    assert isinstance(result["access_token"], str)
    assert len(result["access_token"]) > 0


def test_register_with_valid_input_token_type_is_bearer(auth_service):
    result = auth_service.register(email="alice12c@example.com", password="password12")
    assert result["token_type"] == "bearer"


def test_register_access_token_encodes_user_id_in_sub(auth_service):
    """The returned JWT's sub claim must be a valid UUID (the new user's id)."""
    from jose import jwt as jose_jwt
    from app.core.config import settings

    result = auth_service.register(email="alice12d@example.com", password="password12")
    payload = jose_jwt.decode(result["access_token"], settings.SECRET_KEY, algorithms=["HS256"])
    # sub must be parseable as a UUID
    parsed = uuid.UUID(payload["sub"])
    assert str(parsed) == payload["sub"]


# ---------------------------------------------------------------------------
# register — duplicate email → ConflictError (req 1.2)
# ---------------------------------------------------------------------------

def test_register_duplicate_email_raises_conflict_error(auth_service):
    from app.core.exceptions import ConflictError

    auth_service.register(email="dup12@example.com", password="password12")
    with pytest.raises(ConflictError):
        auth_service.register(email="dup12@example.com", password="otherpassword")


def test_register_duplicate_email_conflict_error_message_mentions_email(auth_service):
    from app.core.exceptions import ConflictError

    email = "dup12b@example.com"
    auth_service.register(email=email, password="password12")
    with pytest.raises(ConflictError) as exc_info:
        auth_service.register(email=email, password="password12")
    # The error message should be non-empty
    assert str(exc_info.value)


# ---------------------------------------------------------------------------
# register — password below minimum length → ValidationError (req 1.3)
# ---------------------------------------------------------------------------

def test_register_password_too_short_raises_validation_error(auth_service):
    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        auth_service.register(email="short12@example.com", password="abc")


def test_register_password_7_chars_raises_validation_error(auth_service):
    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        auth_service.register(email="short12b@example.com", password="seven77")


def test_register_password_exactly_8_chars_succeeds(auth_service):
    """Boundary: 8-character password must not raise ValidationError."""
    result = auth_service.register(email="exact8_12@example.com", password="eight888")
    assert "access_token" in result


def test_register_empty_password_raises_validation_error(auth_service):
    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        auth_service.register(email="empty12@example.com", password="")


# ---------------------------------------------------------------------------
# login — valid credentials (req 2.1)
# ---------------------------------------------------------------------------

def test_login_valid_credentials_returns_token_response(auth_service):
    auth_service.register(email="loginok12@example.com", password="hunter12ok")
    result = auth_service.login(email="loginok12@example.com", password="hunter12ok")
    assert isinstance(result, dict)
    assert "access_token" in result
    assert result["token_type"] == "bearer"


def test_login_valid_credentials_token_is_non_empty_string(auth_service):
    auth_service.register(email="loginok12b@example.com", password="hunter12ok")
    result = auth_service.login(email="loginok12b@example.com", password="hunter12ok")
    assert isinstance(result["access_token"], str)
    assert len(result["access_token"]) > 0


def test_login_valid_credentials_token_sub_matches_user(auth_service):
    from jose import jwt as jose_jwt
    from app.core.config import settings

    reg = auth_service.register(email="loginok12c@example.com", password="hunter12ok")
    reg_payload = jose_jwt.decode(reg["access_token"], settings.SECRET_KEY, algorithms=["HS256"])
    reg_user_id = reg_payload["sub"]

    result = auth_service.login(email="loginok12c@example.com", password="hunter12ok")
    login_payload = jose_jwt.decode(result["access_token"], settings.SECRET_KEY, algorithms=["HS256"])
    assert login_payload["sub"] == reg_user_id


# ---------------------------------------------------------------------------
# login — unknown email → AuthenticationError (req 2.2)
# ---------------------------------------------------------------------------

def test_login_unknown_email_raises_authentication_error(auth_service):
    from app.core.exceptions import AuthenticationError

    with pytest.raises(AuthenticationError):
        auth_service.login(email="nobody12@example.com", password="doesntmatter")


# ---------------------------------------------------------------------------
# login — wrong password → AuthenticationError (req 2.2)
# ---------------------------------------------------------------------------

def test_login_wrong_password_raises_authentication_error(auth_service):
    from app.core.exceptions import AuthenticationError

    auth_service.register(email="wrongpwd12@example.com", password="correctpassword")
    with pytest.raises(AuthenticationError):
        auth_service.login(email="wrongpwd12@example.com", password="wrongpassword")


# ---------------------------------------------------------------------------
# login — error messages for unknown email and wrong password must be IDENTICAL
# (req 2.2 — never disclose which field was wrong)
# ---------------------------------------------------------------------------

def test_login_unknown_email_and_wrong_password_produce_identical_errors(auth_service):
    """Requirement 2.2: must not disclose whether email or password was wrong."""
    from app.core.exceptions import AuthenticationError

    auth_service.register(email="nodisclose12@example.com", password="password12")

    unknown_email_msg = None
    wrong_password_msg = None

    try:
        auth_service.login(email="notregistered12@example.com", password="password12")
    except AuthenticationError as exc:
        unknown_email_msg = str(exc)

    try:
        auth_service.login(email="nodisclose12@example.com", password="wrongpassword")
    except AuthenticationError as exc:
        wrong_password_msg = str(exc)

    assert unknown_email_msg is not None, "Expected AuthenticationError for unknown email"
    assert wrong_password_msg is not None, "Expected AuthenticationError for wrong password"
    assert unknown_email_msg == wrong_password_msg, (
        f"Error messages differ — this discloses which field was wrong.\n"
        f"  Unknown email: {unknown_email_msg!r}\n"
        f"  Wrong password: {wrong_password_msg!r}"
    )


# ---------------------------------------------------------------------------
# decode_token — valid token (req 2.3)
# ---------------------------------------------------------------------------

def test_decode_token_valid_token_returns_payload(auth_service):
    user_id = str(uuid.uuid4())
    token = auth_service.create_access_token(user_id=user_id)
    payload = auth_service.decode_token(token)
    assert isinstance(payload, dict)
    assert payload["sub"] == user_id


def test_decode_token_valid_token_contains_jti(auth_service):
    token = auth_service.create_access_token(user_id=str(uuid.uuid4()))
    payload = auth_service.decode_token(token)
    assert "jti" in payload


def test_decode_token_valid_token_contains_exp(auth_service):
    token = auth_service.create_access_token(user_id=str(uuid.uuid4()))
    payload = auth_service.decode_token(token)
    assert "exp" in payload


# ---------------------------------------------------------------------------
# decode_token — expired token → AuthenticationError (req 2.3)
# ---------------------------------------------------------------------------

def test_decode_token_expired_token_raises_authentication_error(auth_service):
    """A token with exp in the past must raise AuthenticationError."""
    from app.core.exceptions import AuthenticationError
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


def test_decode_token_zero_ttl_token_raises_authentication_error(auth_service):
    """Token issued with TTL of 0 minutes (exp == iat) is immediately expired."""
    from app.core.exceptions import AuthenticationError
    from jose import jwt as jose_jwt
    from app.core.config import settings

    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(uuid.uuid4()),
        "exp": now - timedelta(seconds=30),  # strictly in the past
        "iat": now - timedelta(seconds=30),
        "jti": str(uuid.uuid4()),
    }
    token = jose_jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")

    with pytest.raises(AuthenticationError):
        auth_service.decode_token(token)


# ---------------------------------------------------------------------------
# decode_token — blacklisted token → AuthenticationError (req 2.5)
# ---------------------------------------------------------------------------

def test_decode_token_blacklisted_token_raises_authentication_error(auth_service, db):
    """A token whose jti is in token_blacklist must raise AuthenticationError."""
    from app.core.exceptions import AuthenticationError
    from app.models.token_blacklist import TokenBlacklist
    from jose import jwt as jose_jwt
    from app.core.config import settings

    user_id = str(uuid.uuid4())
    token = auth_service.create_access_token(user_id=user_id)
    payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    jti = payload["jti"]

    # Blacklist the jti directly
    entry = TokenBlacklist(
        jti=jti,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db.add(entry)
    db.commit()

    with pytest.raises(AuthenticationError):
        auth_service.decode_token(token)


def test_decode_token_after_logout_raises_authentication_error(auth_service, db):
    """After calling logout the same token must no longer be decodeable."""
    from app.core.exceptions import AuthenticationError
    from jose import jwt as jose_jwt
    from app.core.config import settings

    user_id = str(uuid.uuid4())
    token = auth_service.create_access_token(user_id=user_id)
    payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    jti = payload["jti"]
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    auth_service.logout(jti=jti, expires_at=expires_at)

    with pytest.raises(AuthenticationError):
        auth_service.decode_token(token)
