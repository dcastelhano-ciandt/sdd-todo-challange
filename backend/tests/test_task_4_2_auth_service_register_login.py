"""
Tests for task 4.2: AuthService registration and login business logic.

Covers:
- register: valid email+password → returns TokenResponse dict
- register: duplicate email → raises ConflictError
- register: password shorter than 8 chars → raises ValidationError
- login: valid credentials → returns TokenResponse dict
- login: unknown email → raises AuthenticationError
- login: wrong password → raises AuthenticationError
- login: error messages for unknown email and wrong password are identical
  (requirement 2.2 — must not disclose which field was wrong)
"""
import uuid
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.models.base import Base
    import app.models  # noqa: F401

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


@pytest.fixture
def auth_service(db):
    from app.services.auth_service import AuthService
    from app.repositories.user_repository import UserRepository
    return AuthService(db=db, user_repo=UserRepository(db))


# ---------------------------------------------------------------------------
# register — success
# ---------------------------------------------------------------------------

def test_register_returns_token_response_dict(auth_service):
    result = auth_service.register(email="alice@example.com", password="password123")
    assert isinstance(result, dict)
    assert "access_token" in result
    assert result["token_type"] == "bearer"


def test_register_token_is_non_empty_string(auth_service):
    result = auth_service.register(email="bob@example.com", password="mypassword")
    assert isinstance(result["access_token"], str)
    assert len(result["access_token"]) > 0


def test_register_access_token_is_valid_jwt(auth_service):
    """The returned token must decode to a payload containing sub == user_id."""
    from jose import jwt as jose_jwt
    from app.core.config import settings

    result = auth_service.register(email="carol@example.com", password="securePass1")
    payload = jose_jwt.decode(result["access_token"], settings.SECRET_KEY, algorithms=["HS256"])
    # sub must be a valid UUID string
    assert uuid.UUID(payload["sub"])


# ---------------------------------------------------------------------------
# register — duplicate email
# ---------------------------------------------------------------------------

def test_register_raises_conflict_error_on_duplicate_email(auth_service):
    from app.core.exceptions import ConflictError

    auth_service.register(email="dave@example.com", password="firstpassword")
    with pytest.raises(ConflictError):
        auth_service.register(email="dave@example.com", password="secondpassword")


# ---------------------------------------------------------------------------
# register — weak password
# ---------------------------------------------------------------------------

def test_register_raises_validation_error_for_short_password(auth_service):
    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        auth_service.register(email="eve@example.com", password="short")


def test_register_raises_validation_error_for_7_char_password(auth_service):
    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        auth_service.register(email="frank@example.com", password="seven77")


def test_register_accepts_exactly_8_char_password(auth_service):
    result = auth_service.register(email="grace@example.com", password="eight888")
    assert "access_token" in result


# ---------------------------------------------------------------------------
# login — success
# ---------------------------------------------------------------------------

def test_login_returns_token_response_dict(auth_service):
    auth_service.register(email="henry@example.com", password="hunter12")
    result = auth_service.login(email="henry@example.com", password="hunter12")
    assert "access_token" in result
    assert result["token_type"] == "bearer"


def test_login_token_is_non_empty_string(auth_service):
    auth_service.register(email="iris@example.com", password="irispass1")
    result = auth_service.login(email="iris@example.com", password="irispass1")
    assert isinstance(result["access_token"], str)
    assert len(result["access_token"]) > 0


def test_login_access_token_sub_matches_registered_user(auth_service):
    from jose import jwt as jose_jwt
    from app.core.config import settings

    auth_service.register(email="jack@example.com", password="jackpass1")
    result = auth_service.login(email="jack@example.com", password="jackpass1")
    payload = jose_jwt.decode(result["access_token"], settings.SECRET_KEY, algorithms=["HS256"])
    assert uuid.UUID(payload["sub"])


# ---------------------------------------------------------------------------
# login — unknown email
# ---------------------------------------------------------------------------

def test_login_raises_authentication_error_for_unknown_email(auth_service):
    from app.core.exceptions import AuthenticationError

    with pytest.raises(AuthenticationError):
        auth_service.login(email="unknown@example.com", password="doesntmatter")


# ---------------------------------------------------------------------------
# login — wrong password
# ---------------------------------------------------------------------------

def test_login_raises_authentication_error_for_wrong_password(auth_service):
    from app.core.exceptions import AuthenticationError

    auth_service.register(email="kate@example.com", password="correctpassword")
    with pytest.raises(AuthenticationError):
        auth_service.login(email="kate@example.com", password="wrongpassword")


# ---------------------------------------------------------------------------
# login — error message must not disclose which field was wrong (req 2.2)
# ---------------------------------------------------------------------------

def test_login_error_messages_are_identical_for_unknown_email_and_wrong_password(auth_service):
    """Requirement 2.2: Never disclose whether email or password was incorrect."""
    from app.core.exceptions import AuthenticationError

    auth_service.register(email="leo@example.com", password="leopassword")

    unknown_email_error = None
    wrong_password_error = None

    try:
        auth_service.login(email="notleo@example.com", password="leopassword")
    except AuthenticationError as e:
        unknown_email_error = str(e)

    try:
        auth_service.login(email="leo@example.com", password="wrongpassword")
    except AuthenticationError as e:
        wrong_password_error = str(e)

    assert unknown_email_error is not None
    assert wrong_password_error is not None
    assert unknown_email_error == wrong_password_error
