"""
Tests for search task 1.1: TaskRepository — case-insensitive title search.

Covers:
- list_by_user with q: returns only tasks whose titles contain the keyword
- list_by_user with q: case-insensitive matching
- list_by_user with q=None: returns all tasks without title filter (backward-compatible)
- list_by_user with status + q: applies both filters simultaneously
- list_by_user with q: results ordered by created_at DESC

Requirements: 2.1, 2.2, 2.3, 2.4
"""
import uuid
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    from app.models.base import Base
    import app.models  # noqa: F401

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def repo(db_session):
    from app.repositories.task_repository import TaskRepository
    return TaskRepository(db_session)


@pytest.fixture
def seeded_user(db_session):
    """Insert a user and return its id."""
    from app.models.user import User
    user = User(id="user-search-001", email="search@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    return "user-search-001"


@pytest.fixture
def other_user(db_session):
    """Insert a second user and return its id."""
    from app.models.user import User
    user = User(id="user-search-002", email="other-search@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    return "user-search-002"


# ---------------------------------------------------------------------------
# Requirement 2.1: SQL LIKE on title column
# ---------------------------------------------------------------------------

def test_list_by_user_with_keyword_returns_matching_tasks(repo, seeded_user, db_session):
    """Tasks containing the keyword in their title are returned."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Buy groceries",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Write report",
        completed=False, created_at=datetime(2026, 1, 1, 11, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Buy milk",
        completed=False, created_at=datetime(2026, 1, 1, 12, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, q="Buy")
    titles = [t.title for t in result]
    assert "Buy groceries" in titles
    assert "Buy milk" in titles
    assert "Write report" not in titles


def test_list_by_user_with_keyword_returns_only_exact_substring_matches(repo, seeded_user, db_session):
    """Only tasks whose title contains the keyword as a substring are returned."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Call doctor",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Schedule meeting",
        completed=False, created_at=datetime(2026, 1, 1, 11, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, q="doctor")
    assert len(result) == 1
    assert result[0].title == "Call doctor"


# ---------------------------------------------------------------------------
# Requirement 2.2: Case-insensitive match via lower()
# ---------------------------------------------------------------------------

def test_list_by_user_keyword_is_case_insensitive_uppercase_query(repo, seeded_user, db_session):
    """Searching with uppercase keyword matches lowercase titles."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="buy supplies",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, q="BUY")
    assert len(result) == 1
    assert result[0].title == "buy supplies"


def test_list_by_user_keyword_is_case_insensitive_lowercase_query(repo, seeded_user, db_session):
    """Searching with lowercase keyword matches uppercase titles."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="SCHEDULE MEETING",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, q="schedule")
    assert len(result) == 1
    assert result[0].title == "SCHEDULE MEETING"


def test_list_by_user_keyword_is_case_insensitive_mixed_case(repo, seeded_user, db_session):
    """Mixed-case keyword matches regardless of title casing."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Prepare Report",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, q="rEpOrT")
    assert len(result) == 1
    assert result[0].title == "Prepare Report"


# ---------------------------------------------------------------------------
# Requirement 2.1: No filter when q is None (backward-compatible)
# ---------------------------------------------------------------------------

def test_list_by_user_with_q_none_returns_all_tasks(repo, seeded_user, db_session):
    """Passing q=None returns all tasks without title filtering."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Task Alpha",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Task Beta",
        completed=True, created_at=datetime(2026, 1, 1, 11, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, q=None)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# Requirement 2.3: Title filter chains with completed filter
# ---------------------------------------------------------------------------

def test_list_by_user_with_status_and_keyword_applies_both_filters(repo, seeded_user, db_session):
    """Both completed=False and keyword filter are applied simultaneously."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Buy groceries (pending)",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Buy milk (done)",
        completed=True, created_at=datetime(2026, 1, 1, 11, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Write report",
        completed=False, created_at=datetime(2026, 1, 1, 12, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=False, q="buy")
    titles = [t.title for t in result]
    assert "Buy groceries (pending)" in titles
    assert "Buy milk (done)" not in titles
    assert "Write report" not in titles


def test_list_by_user_with_completed_true_and_keyword(repo, seeded_user, db_session):
    """Both completed=True and keyword filter applied simultaneously."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Buy supplies (done)",
        completed=True, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Buy bread (pending)",
        completed=False, created_at=datetime(2026, 1, 1, 11, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=True, q="buy")
    assert len(result) == 1
    assert result[0].title == "Buy supplies (done)"


# ---------------------------------------------------------------------------
# Requirement 2.4: ORDER BY created_at DESC preserved with keyword filter
# ---------------------------------------------------------------------------

def test_list_by_user_with_keyword_preserves_order_by_created_at_desc(repo, seeded_user, db_session):
    """Results are ordered newest first even when a keyword filter is active."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="meeting: old",
        completed=False, created_at=datetime(2026, 1, 1, 9, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="meeting: new",
        completed=False, created_at=datetime(2026, 1, 1, 11, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="unrelated task",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, q="meeting")
    assert len(result) == 2
    assert result[0].title == "meeting: new"
    assert result[1].title == "meeting: old"


# ---------------------------------------------------------------------------
# Edge: no match returns empty list (requirement 1.5)
# ---------------------------------------------------------------------------

def test_list_by_user_with_keyword_no_match_returns_empty_list(repo, seeded_user, db_session):
    """When no tasks match the keyword, an empty list is returned (not an error)."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Buy groceries",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, q="xyz_no_match")
    assert result == []


# ---------------------------------------------------------------------------
# User scoping preserved with keyword filter (requirement 1.6)
# ---------------------------------------------------------------------------

def test_list_by_user_with_keyword_does_not_return_other_users_tasks(
    repo, seeded_user, other_user, db_session
):
    """Keyword filter never exposes tasks belonging to another user."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="My meeting notes",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=other_user, title="Their meeting notes",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, q="meeting")
    assert len(result) == 1
    assert result[0].title == "My meeting notes"
