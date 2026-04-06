"""
Tests for task 4.3: AuthService logout operation and token blacklist management.

Covers:
- logout: inserts (jti, expires_at) into token_blacklist
- logout: after logout, decode_token raises AuthenticationError for the same token
- logout: prunes expired entries lazily (expired entries are removed after logout)
- logout: non-expired entries are not pruned
"""
import uuid
import pytest
from datetime import datetime, timedelta, timezone


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
# logout — inserts into blacklist
# ---------------------------------------------------------------------------

def test_logout_inserts_jti_into_token_blacklist(auth_service, db):
    from app.models.token_blacklist import TokenBlacklist

    jti = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    auth_service.logout(jti=jti, expires_at=expires_at)

    entry = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
    assert entry is not None
    assert entry.jti == jti


def test_logout_stores_correct_expires_at(auth_service, db):
    from app.models.token_blacklist import TokenBlacklist

    jti = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    auth_service.logout(jti=jti, expires_at=expires_at)

    entry = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
    # Compare truncated to seconds to avoid microsecond drift
    assert abs((entry.expires_at - expires_at.replace(tzinfo=None)).total_seconds()) < 2


# ---------------------------------------------------------------------------
# logout — token becomes invalid after blacklisting
# ---------------------------------------------------------------------------

def test_decode_token_fails_after_logout(auth_service, db):
    from app.core.exceptions import AuthenticationError
    from jose import jwt as jose_jwt
    from app.core.config import settings

    user_id = str(uuid.uuid4())
    token = auth_service.create_access_token(user_id=user_id)
    payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    jti = payload["jti"]
    exp = datetime.utcfromtimestamp(payload["exp"])

    # Token is valid before logout
    auth_service.decode_token(token)

    # Blacklist it
    auth_service.logout(jti=jti, expires_at=exp)

    # Token is now invalid
    with pytest.raises(AuthenticationError):
        auth_service.decode_token(token)


# ---------------------------------------------------------------------------
# logout — prunes expired entries
# ---------------------------------------------------------------------------

def test_logout_prunes_expired_blacklist_entries(auth_service, db):
    from app.models.token_blacklist import TokenBlacklist

    # Insert an already-expired entry directly
    old_jti = str(uuid.uuid4())
    expired_entry = TokenBlacklist(
        jti=old_jti,
        expires_at=datetime.utcnow() - timedelta(minutes=5),
    )
    db.add(expired_entry)
    db.commit()

    # Verify it exists before logout
    assert db.query(TokenBlacklist).filter(TokenBlacklist.jti == old_jti).first() is not None

    # Trigger a new logout — should prune the expired entry
    new_jti = str(uuid.uuid4())
    auth_service.logout(
        jti=new_jti,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )

    # Expired entry should be gone
    assert db.query(TokenBlacklist).filter(TokenBlacklist.jti == old_jti).first() is None


def test_logout_does_not_prune_non_expired_entries(auth_service, db):
    from app.models.token_blacklist import TokenBlacklist

    # Insert a non-expired entry directly
    future_jti = str(uuid.uuid4())
    future_entry = TokenBlacklist(
        jti=future_jti,
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(future_entry)
    db.commit()

    # Trigger a new logout
    new_jti = str(uuid.uuid4())
    auth_service.logout(
        jti=new_jti,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )

    # Non-expired entry should still be present
    assert db.query(TokenBlacklist).filter(TokenBlacklist.jti == future_jti).first() is not None
