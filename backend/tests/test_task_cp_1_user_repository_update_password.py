"""
Tests for change-password task 1: UserRepository.update_password

Covers:
- update_password: updates hashed_password column for an existing user
- update_password: returns the updated User entity with the new hashed_password
- update_password: persists the change so it is visible in a subsequent find_by_id
- update_password: raises NotFoundError when user_id does not exist
- update_password: does not modify any other column (email is unchanged)
- update_password: multiple sequential calls each persist the latest hash

Requirements: 4.1
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    """Provide an in-memory SQLite session with all tables created."""
    from app.models.base import Base
    import app.models  # noqa: F401 — registers all models on Base.metadata

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def repo(db_session):
    from app.repositories.user_repository import UserRepository
    return UserRepository(db_session)


@pytest.fixture
def existing_user(repo):
    """Create and return a persisted user with a known hashed_password."""
    return repo.create(
        email="testuser@example.com",
        hashed_password="$2b$12$original_hashed_password",
    )


# ---------------------------------------------------------------------------
# Method existence
# ---------------------------------------------------------------------------

def test_update_password_method_exists(repo):
    assert hasattr(repo, "update_password"), (
        "UserRepository must have an update_password method"
    )


def test_update_password_is_callable(repo):
    assert callable(getattr(repo, "update_password", None))


# ---------------------------------------------------------------------------
# Happy path: successful update
# ---------------------------------------------------------------------------

def test_update_password_returns_user_entity(repo, existing_user):
    from app.models.user import User
    result = repo.update_password(existing_user.id, "$2b$12$new_hashed_password")
    assert isinstance(result, User)


def test_update_password_returns_entity_with_new_hash(repo, existing_user):
    new_hash = "$2b$12$new_hashed_password"
    result = repo.update_password(existing_user.id, new_hash)
    assert result.hashed_password == new_hash


def test_update_password_persists_change_to_database(repo, existing_user):
    new_hash = "$2b$12$new_hashed_password"
    repo.update_password(existing_user.id, new_hash)
    refreshed = repo.find_by_id(existing_user.id)
    assert refreshed is not None
    assert refreshed.hashed_password == new_hash


def test_update_password_does_not_change_email(repo, existing_user):
    original_email = existing_user.email
    repo.update_password(existing_user.id, "$2b$12$some_new_hash")
    refreshed = repo.find_by_id(existing_user.id)
    assert refreshed.email == original_email


def test_update_password_does_not_change_user_id(repo, existing_user):
    original_id = existing_user.id
    result = repo.update_password(existing_user.id, "$2b$12$some_new_hash")
    assert result.id == original_id


def test_update_password_returned_entity_id_matches_input(repo, existing_user):
    result = repo.update_password(existing_user.id, "$2b$12$hash_x")
    assert result.id == existing_user.id


# ---------------------------------------------------------------------------
# Sequential updates
# ---------------------------------------------------------------------------

def test_update_password_second_call_overwrites_first(repo, existing_user):
    repo.update_password(existing_user.id, "$2b$12$first_hash")
    repo.update_password(existing_user.id, "$2b$12$second_hash")
    refreshed = repo.find_by_id(existing_user.id)
    assert refreshed.hashed_password == "$2b$12$second_hash"


# ---------------------------------------------------------------------------
# Error case: user not found
# ---------------------------------------------------------------------------

def test_update_password_raises_not_found_for_unknown_id(repo):
    from app.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        repo.update_password("nonexistent-id", "$2b$12$some_hash")


def test_update_password_not_found_error_message_contains_id(repo):
    from app.core.exceptions import NotFoundError
    unknown_id = "totally-unknown-id"
    with pytest.raises(NotFoundError) as exc_info:
        repo.update_password(unknown_id, "$2b$12$some_hash")
    assert unknown_id in str(exc_info.value)


def test_update_password_not_found_does_not_mutate_database(repo, existing_user):
    """A failed update for a nonexistent ID must not touch other records."""
    from app.core.exceptions import NotFoundError
    original_hash = existing_user.hashed_password
    with pytest.raises(NotFoundError):
        repo.update_password("ghost-id", "$2b$12$intruder_hash")
    untouched = repo.find_by_id(existing_user.id)
    assert untouched.hashed_password == original_hash
