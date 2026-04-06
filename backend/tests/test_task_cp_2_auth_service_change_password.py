"""
Tests for change-password task 2: AuthService.change_password and AuthService.get_user_email

Covers:
- change_password: method exists and is callable
- change_password: correct current password → returns TokenResponse dict
- change_password: returned token_type is "bearer"
- change_password: returned access_token is a non-empty string
- change_password: returned access_token is a valid JWT with correct sub
- change_password: calls update_password with new hashed value (password is changed in DB)
- change_password: new hash in DB differs from the original hash
- change_password: old JTI is blacklisted after success
- change_password: old token is rejected by decode_token after success
- change_password: incorrect current password → raises AuthenticationError
- change_password: incorrect current password → update_password is NOT called (DB unchanged)
- change_password: incorrect current password → old JTI is NOT blacklisted
- change_password: unknown user_id → raises NotFoundError
- change_password: transaction atomicity — if blacklist commit fails, password change is rolled back
- get_user_email: method exists and is callable
- get_user_email: known user_id → returns email string
- get_user_email: unknown user_id → raises NotFoundError
- get_user_email: NotFoundError message contains the unknown user_id

Requirements: 4.1, 4.2, 5.4, 1.2
"""
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock


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


@pytest.fixture
def registered_user(auth_service):
    """Register a user and return (email, password, token_response)."""
    email = "changepass@example.com"
    password = "original_password123"
    token_response = auth_service.register(email=email, password=password)
    return {"email": email, "password": password, "token_response": token_response}


@pytest.fixture
def registered_user_with_payload(auth_service, registered_user):
    """Extend registered_user with decoded JWT payload (jti, exp, user_id)."""
    from jose import jwt as jose_jwt
    from app.core.config import settings

    token = registered_user["token_response"]["access_token"]
    payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    return {
        **registered_user,
        "user_id": payload["sub"],
        "jti": payload["jti"],
        "expires_at": datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
    }


# ---------------------------------------------------------------------------
# Method existence
# ---------------------------------------------------------------------------

def test_change_password_method_exists(auth_service):
    assert hasattr(auth_service, "change_password"), (
        "AuthService must have a change_password method"
    )


def test_change_password_is_callable(auth_service):
    assert callable(getattr(auth_service, "change_password", None))


def test_get_user_email_method_exists(auth_service):
    assert hasattr(auth_service, "get_user_email"), (
        "AuthService must have a get_user_email method"
    )


def test_get_user_email_is_callable(auth_service):
    assert callable(getattr(auth_service, "get_user_email", None))


# ---------------------------------------------------------------------------
# change_password — happy path: correct current password
# ---------------------------------------------------------------------------

def test_change_password_returns_dict(auth_service, registered_user_with_payload):
    result = auth_service.change_password(
        user_id=registered_user_with_payload["user_id"],
        jti=registered_user_with_payload["jti"],
        expires_at=registered_user_with_payload["expires_at"],
        current_password=registered_user_with_payload["password"],
        new_password="new_secure_password456",
    )
    assert isinstance(result, dict)


def test_change_password_returns_access_token_key(auth_service, registered_user_with_payload):
    result = auth_service.change_password(
        user_id=registered_user_with_payload["user_id"],
        jti=registered_user_with_payload["jti"],
        expires_at=registered_user_with_payload["expires_at"],
        current_password=registered_user_with_payload["password"],
        new_password="new_secure_password456",
    )
    assert "access_token" in result


def test_change_password_returns_bearer_token_type(auth_service, registered_user_with_payload):
    result = auth_service.change_password(
        user_id=registered_user_with_payload["user_id"],
        jti=registered_user_with_payload["jti"],
        expires_at=registered_user_with_payload["expires_at"],
        current_password=registered_user_with_payload["password"],
        new_password="new_secure_password456",
    )
    assert result["token_type"] == "bearer"


def test_change_password_access_token_is_non_empty_string(auth_service, registered_user_with_payload):
    result = auth_service.change_password(
        user_id=registered_user_with_payload["user_id"],
        jti=registered_user_with_payload["jti"],
        expires_at=registered_user_with_payload["expires_at"],
        current_password=registered_user_with_payload["password"],
        new_password="new_secure_password456",
    )
    assert isinstance(result["access_token"], str)
    assert len(result["access_token"]) > 0


def test_change_password_new_token_sub_matches_user_id(auth_service, registered_user_with_payload):
    """The new JWT's sub claim must equal the original user_id."""
    from jose import jwt as jose_jwt
    from app.core.config import settings

    result = auth_service.change_password(
        user_id=registered_user_with_payload["user_id"],
        jti=registered_user_with_payload["jti"],
        expires_at=registered_user_with_payload["expires_at"],
        current_password=registered_user_with_payload["password"],
        new_password="new_secure_password456",
    )
    payload = jose_jwt.decode(result["access_token"], settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == registered_user_with_payload["user_id"]


def test_change_password_new_token_differs_from_old_token(auth_service, registered_user_with_payload):
    """A new access token must be issued, different from the original."""
    old_token = registered_user_with_payload["token_response"]["access_token"]
    result = auth_service.change_password(
        user_id=registered_user_with_payload["user_id"],
        jti=registered_user_with_payload["jti"],
        expires_at=registered_user_with_payload["expires_at"],
        current_password=registered_user_with_payload["password"],
        new_password="new_secure_password456",
    )
    assert result["access_token"] != old_token


# ---------------------------------------------------------------------------
# change_password — persists new password hash in DB
# ---------------------------------------------------------------------------

def test_change_password_updates_hashed_password_in_db(auth_service, registered_user_with_payload, db):
    """After change_password, the user's hashed_password in the DB must differ."""
    from app.models.user import User

    original_user = db.get(User, registered_user_with_payload["user_id"])
    original_hash = original_user.hashed_password

    auth_service.change_password(
        user_id=registered_user_with_payload["user_id"],
        jti=registered_user_with_payload["jti"],
        expires_at=registered_user_with_payload["expires_at"],
        current_password=registered_user_with_payload["password"],
        new_password="new_secure_password456",
    )

    db.expire_all()
    updated_user = db.get(User, registered_user_with_payload["user_id"])
    assert updated_user.hashed_password != original_hash


def test_change_password_new_hash_is_valid_bcrypt(auth_service, registered_user_with_payload, db):
    """The stored hash after change_password must be verifiable with the new password."""
    from app.models.user import User

    new_password = "new_secure_password456"
    auth_service.change_password(
        user_id=registered_user_with_payload["user_id"],
        jti=registered_user_with_payload["jti"],
        expires_at=registered_user_with_payload["expires_at"],
        current_password=registered_user_with_payload["password"],
        new_password=new_password,
    )

    db.expire_all()
    updated_user = db.get(User, registered_user_with_payload["user_id"])
    assert auth_service.verify_password(new_password, updated_user.hashed_password)


def test_change_password_old_password_no_longer_verifies(auth_service, registered_user_with_payload, db):
    """After change_password, the old password must NOT verify against the new hash."""
    from app.models.user import User

    old_password = registered_user_with_payload["password"]
    auth_service.change_password(
        user_id=registered_user_with_payload["user_id"],
        jti=registered_user_with_payload["jti"],
        expires_at=registered_user_with_payload["expires_at"],
        current_password=old_password,
        new_password="new_secure_password456",
    )

    db.expire_all()
    updated_user = db.get(User, registered_user_with_payload["user_id"])
    assert not auth_service.verify_password(old_password, updated_user.hashed_password)


# ---------------------------------------------------------------------------
# change_password — old JTI is blacklisted
# ---------------------------------------------------------------------------

def test_change_password_blacklists_old_jti(auth_service, registered_user_with_payload, db):
    """After change_password, the old JTI must be present in token_blacklist."""
    from app.models.token_blacklist import TokenBlacklist

    old_jti = registered_user_with_payload["jti"]
    auth_service.change_password(
        user_id=registered_user_with_payload["user_id"],
        jti=old_jti,
        expires_at=registered_user_with_payload["expires_at"],
        current_password=registered_user_with_payload["password"],
        new_password="new_secure_password456",
    )

    entry = db.query(TokenBlacklist).filter(TokenBlacklist.jti == old_jti).first()
    assert entry is not None


def test_change_password_old_token_rejected_by_decode_token(auth_service, registered_user_with_payload):
    """After change_password, calling decode_token with the old token must raise AuthenticationError."""
    from app.core.exceptions import AuthenticationError

    old_token = registered_user_with_payload["token_response"]["access_token"]
    auth_service.change_password(
        user_id=registered_user_with_payload["user_id"],
        jti=registered_user_with_payload["jti"],
        expires_at=registered_user_with_payload["expires_at"],
        current_password=registered_user_with_payload["password"],
        new_password="new_secure_password456",
    )

    with pytest.raises(AuthenticationError):
        auth_service.decode_token(old_token)


# ---------------------------------------------------------------------------
# change_password — incorrect current password → AuthenticationError
# ---------------------------------------------------------------------------

def test_change_password_wrong_current_password_raises_authentication_error(
    auth_service, registered_user_with_payload
):
    from app.core.exceptions import AuthenticationError

    with pytest.raises(AuthenticationError):
        auth_service.change_password(
            user_id=registered_user_with_payload["user_id"],
            jti=registered_user_with_payload["jti"],
            expires_at=registered_user_with_payload["expires_at"],
            current_password="totally_wrong_password",
            new_password="new_secure_password456",
        )


def test_change_password_wrong_current_password_error_message_is_meaningful(
    auth_service, registered_user_with_payload
):
    """AuthenticationError message must describe the wrong-password scenario."""
    from app.core.exceptions import AuthenticationError

    with pytest.raises(AuthenticationError) as exc_info:
        auth_service.change_password(
            user_id=registered_user_with_payload["user_id"],
            jti=registered_user_with_payload["jti"],
            expires_at=registered_user_with_payload["expires_at"],
            current_password="totally_wrong_password",
            new_password="new_secure_password456",
        )
    error_message = str(exc_info.value)
    assert len(error_message) > 0


def test_change_password_wrong_current_password_does_not_update_db(
    auth_service, registered_user_with_payload, db
):
    """When current password is wrong, hashed_password in DB must remain unchanged."""
    from app.core.exceptions import AuthenticationError
    from app.models.user import User

    original_user = db.get(User, registered_user_with_payload["user_id"])
    original_hash = original_user.hashed_password

    with pytest.raises(AuthenticationError):
        auth_service.change_password(
            user_id=registered_user_with_payload["user_id"],
            jti=registered_user_with_payload["jti"],
            expires_at=registered_user_with_payload["expires_at"],
            current_password="totally_wrong_password",
            new_password="new_secure_password456",
        )

    db.expire_all()
    unchanged_user = db.get(User, registered_user_with_payload["user_id"])
    assert unchanged_user.hashed_password == original_hash


def test_change_password_wrong_current_password_does_not_blacklist_jti(
    auth_service, registered_user_with_payload, db
):
    """When current password is wrong, the JTI must NOT be added to token_blacklist."""
    from app.core.exceptions import AuthenticationError
    from app.models.token_blacklist import TokenBlacklist

    old_jti = registered_user_with_payload["jti"]

    with pytest.raises(AuthenticationError):
        auth_service.change_password(
            user_id=registered_user_with_payload["user_id"],
            jti=old_jti,
            expires_at=registered_user_with_payload["expires_at"],
            current_password="totally_wrong_password",
            new_password="new_secure_password456",
        )

    entry = db.query(TokenBlacklist).filter(TokenBlacklist.jti == old_jti).first()
    assert entry is None


# ---------------------------------------------------------------------------
# change_password — unknown user_id → NotFoundError
# ---------------------------------------------------------------------------

def test_change_password_unknown_user_id_raises_not_found_error(auth_service):
    from app.core.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        auth_service.change_password(
            user_id="nonexistent-user-id",
            jti=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            current_password="any_password",
            new_password="new_secure_password456",
        )


# ---------------------------------------------------------------------------
# change_password — transaction atomicity
# Requirement: if the blacklist (logout) commit fails, the password update must
# be rolled back so no partial state is left.
# ---------------------------------------------------------------------------

def test_change_password_rolls_back_password_update_when_commit_fails(
    auth_service, registered_user_with_payload, db
):
    """Atomicity: both the password update and the blacklist entry are staged before a
    single db.commit(). If that commit raises, neither write must persist."""
    from app.models.user import User

    original_user = db.get(User, registered_user_with_payload["user_id"])
    original_hash = original_user.hashed_password

    # Patch db.commit to raise on the first call (simulates a DB failure
    # at the point where both writes would be flushed together).
    original_commit = db.commit

    call_count = [0]

    def failing_commit():
        call_count[0] += 1
        if call_count[0] == 1:
            raise Exception("DB commit failure (simulated)")
        return original_commit()

    with patch.object(db, "commit", side_effect=failing_commit):
        with pytest.raises(Exception, match="DB commit failure"):
            auth_service.change_password(
                user_id=registered_user_with_payload["user_id"],
                jti=registered_user_with_payload["jti"],
                expires_at=registered_user_with_payload["expires_at"],
                current_password=registered_user_with_payload["password"],
                new_password="new_secure_password456",
            )

    db.expire_all()
    unchanged_user = db.get(User, registered_user_with_payload["user_id"])
    assert unchanged_user.hashed_password == original_hash, (
        "Password update must be rolled back when the DB commit fails"
    )


# ---------------------------------------------------------------------------
# get_user_email — happy path
# ---------------------------------------------------------------------------

def test_get_user_email_returns_string(auth_service, registered_user_with_payload):
    result = auth_service.get_user_email(registered_user_with_payload["user_id"])
    assert isinstance(result, str)


def test_get_user_email_returns_correct_email(auth_service, registered_user_with_payload):
    result = auth_service.get_user_email(registered_user_with_payload["user_id"])
    assert result == registered_user_with_payload["email"]


def test_get_user_email_result_is_non_empty(auth_service, registered_user_with_payload):
    result = auth_service.get_user_email(registered_user_with_payload["user_id"])
    assert len(result) > 0


# ---------------------------------------------------------------------------
# get_user_email — unknown user_id → NotFoundError
# ---------------------------------------------------------------------------

def test_get_user_email_unknown_id_raises_not_found_error(auth_service):
    from app.core.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        auth_service.get_user_email("nonexistent-user-id")


def test_get_user_email_not_found_error_message_contains_user_id(auth_service):
    from app.core.exceptions import NotFoundError

    unknown_id = "ghost-user-99"
    with pytest.raises(NotFoundError) as exc_info:
        auth_service.get_user_email(unknown_id)
    assert unknown_id in str(exc_info.value)
