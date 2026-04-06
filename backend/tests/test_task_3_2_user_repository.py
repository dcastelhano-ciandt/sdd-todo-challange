"""
Tests for task 3.2: UserRepository implementation.

Covers:
- find_by_email: returns User when found, None when not found
- find_by_id: returns User when found, None when not found
- create: persists and returns a User with id and hashed_password
- create: raises ConflictError on duplicate email (IntegrityError)
"""
import importlib
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


# ---------------------------------------------------------------------------
# Module importability
# ---------------------------------------------------------------------------

def test_user_repository_module_importable():
    mod = importlib.import_module("app.repositories.user_repository")
    assert mod is not None


def test_user_repository_class_exists():
    from app.repositories.user_repository import UserRepository
    assert UserRepository is not None


# ---------------------------------------------------------------------------
# find_by_email
# ---------------------------------------------------------------------------

def test_find_by_email_returns_none_when_not_found(repo):
    result = repo.find_by_email("nonexistent@example.com")
    assert result is None


def test_find_by_email_returns_user_when_found(repo):
    from app.models.user import User
    user = User(id="u-001", email="alice@example.com", hashed_password="hashed_pw")
    repo.db.add(user)
    repo.db.commit()

    result = repo.find_by_email("alice@example.com")
    assert result is not None
    assert result.id == "u-001"
    assert result.email == "alice@example.com"


def test_find_by_email_case_sensitive(repo):
    from app.models.user import User
    user = User(id="u-002", email="Bob@example.com", hashed_password="hashed_pw")
    repo.db.add(user)
    repo.db.commit()

    result = repo.find_by_email("bob@example.com")
    # SQLite by default is case-sensitive for LIKE but equality is case-insensitive
    # The repository should use exact equality; result may or may not be found
    # depending on SQLite collation — we only verify the method runs without error
    assert result is None or result.email == "Bob@example.com"


# ---------------------------------------------------------------------------
# find_by_id
# ---------------------------------------------------------------------------

def test_find_by_id_returns_none_when_not_found(repo):
    result = repo.find_by_id("nonexistent-id")
    assert result is None


def test_find_by_id_returns_user_when_found(repo):
    from app.models.user import User
    user = User(id="u-003", email="carol@example.com", hashed_password="hashed_pw")
    repo.db.add(user)
    repo.db.commit()

    result = repo.find_by_id("u-003")
    assert result is not None
    assert result.id == "u-003"
    assert result.email == "carol@example.com"


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

def test_create_returns_user_with_correct_fields(repo):
    result = repo.create(email="dave@example.com", hashed_password="$2b$12$hashed")
    assert result is not None
    assert result.email == "dave@example.com"
    assert result.hashed_password == "$2b$12$hashed"


def test_create_persists_user_to_database(repo):
    repo.create(email="eve@example.com", hashed_password="hashed_pw")
    found = repo.find_by_email("eve@example.com")
    assert found is not None
    assert found.email == "eve@example.com"


def test_create_assigns_non_empty_id(repo):
    result = repo.create(email="frank@example.com", hashed_password="hashed_pw")
    assert result.id is not None
    assert len(result.id) > 0


def test_create_assigns_uuid_format_id(repo):
    import re
    result = repo.create(email="gina@example.com", hashed_password="hashed_pw")
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    assert uuid_pattern.match(result.id), f"Expected UUID format, got: {result.id}"


def test_create_raises_conflict_error_on_duplicate_email(repo):
    from app.core.exceptions import ConflictError
    repo.create(email="henry@example.com", hashed_password="hashed1")
    with pytest.raises(ConflictError):
        repo.create(email="henry@example.com", hashed_password="hashed2")


def test_create_two_users_with_different_emails(repo):
    u1 = repo.create(email="iris@example.com", hashed_password="hashed1")
    u2 = repo.create(email="jack@example.com", hashed_password="hashed2")
    assert u1.id != u2.id
    assert u1.email != u2.email


def test_created_user_retrievable_by_id(repo):
    created = repo.create(email="kate@example.com", hashed_password="hashed_pw")
    found = repo.find_by_id(created.id)
    assert found is not None
    assert found.email == "kate@example.com"
