"""
Tests for tasks 3.1, 3.2, 3.3: TaskRepository with due_date and sorting.

Covers:
- create accepts and persists due_date
- create persists due_date=None (default)
- list_by_user with sort_by=None falls back to created_at DESC
- list_by_user with sort_by="due_date" sort_dir="asc" orders nullslast(asc)
- list_by_user with sort_by="due_date" sort_dir="desc" orders nullslast(desc)
- tasks with due_date appear before NULL rows in ASC order
- tasks with due_date appear before NULL rows in DESC order
"""
import uuid
import pytest
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


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
    from app.models.user import User
    user = User(id="user-001", email="owner@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    return "user-001"


# ---------------------------------------------------------------------------
# create with due_date
# ---------------------------------------------------------------------------

def test_create_persists_due_date(repo, seeded_user):
    task_id = str(uuid.uuid4())
    due = date(2026, 12, 31)
    task = repo.create(user_id=seeded_user, task_id=task_id, title="Task", due_date=due)
    assert task.due_date is not None
    # SQLite stores as datetime; compare date portion
    if isinstance(task.due_date, datetime):
        assert task.due_date.date() == due
    else:
        assert task.due_date == due


def test_create_due_date_defaults_to_none(repo, seeded_user):
    task_id = str(uuid.uuid4())
    task = repo.create(user_id=seeded_user, task_id=task_id, title="No date")
    assert task.due_date is None


def test_create_due_date_none_explicit(repo, seeded_user):
    task_id = str(uuid.uuid4())
    task = repo.create(user_id=seeded_user, task_id=task_id, title="Explicit none", due_date=None)
    assert task.due_date is None


# ---------------------------------------------------------------------------
# list_by_user — fallback to created_at DESC when sort_by=None
# ---------------------------------------------------------------------------

def test_list_by_user_fallback_created_at_desc(repo, seeded_user, db_session):
    from app.models.task import Task
    t1_id = str(uuid.uuid4())
    t2_id = str(uuid.uuid4())
    t3_id = str(uuid.uuid4())

    db_session.add(Task(
        id=t1_id, userId=seeded_user, title="Oldest",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.add(Task(
        id=t2_id, userId=seeded_user, title="Middle",
        completed=False, created_at=datetime(2026, 1, 1, 11, 0, 0)
    ))
    db_session.add(Task(
        id=t3_id, userId=seeded_user, title="Newest",
        completed=False, created_at=datetime(2026, 1, 1, 12, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, sort_by=None)
    assert result[0].title == "Newest"
    assert result[1].title == "Middle"
    assert result[2].title == "Oldest"


# ---------------------------------------------------------------------------
# list_by_user — sort_by="due_date" ASC (nullslast)
# ---------------------------------------------------------------------------

def test_list_by_user_sort_due_date_asc_tasks_with_dates_before_null(repo, seeded_user, db_session):
    """Tasks with a due_date appear before tasks with NULL in ASC order."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="No date",
        completed=False, created_at=datetime(2026, 1, 1, 12, 0, 0), due_date=None
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Late date",
        completed=False, created_at=datetime(2026, 1, 1, 11, 0, 0),
        due_date=datetime(2026, 12, 1)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Early date",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0),
        due_date=datetime(2026, 6, 1)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, sort_by="due_date", sort_dir="asc")

    titles = [t.title for t in result]
    # "Early date" (Jun 2026) first, "Late date" (Dec 2026) second, "No date" (NULL) last
    assert titles[0] == "Early date"
    assert titles[1] == "Late date"
    assert titles[2] == "No date"


def test_list_by_user_sort_due_date_asc_null_tasks_last(repo, seeded_user, db_session):
    """NULL due_date tasks must be last in ASC order."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="With date",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0),
        due_date=datetime(2026, 5, 1)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="No date",
        completed=False, created_at=datetime(2026, 1, 1, 11, 0, 0), due_date=None
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, sort_by="due_date", sort_dir="asc")
    assert result[-1].title == "No date"
    assert result[0].title == "With date"


# ---------------------------------------------------------------------------
# list_by_user — sort_by="due_date" DESC (nullslast)
# ---------------------------------------------------------------------------

def test_list_by_user_sort_due_date_desc_latest_first(repo, seeded_user, db_session):
    """In DESC order, latest due_date first, NULLs last."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="No date",
        completed=False, created_at=datetime(2026, 1, 1, 12, 0, 0), due_date=None
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Early date",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0),
        due_date=datetime(2026, 3, 1)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Late date",
        completed=False, created_at=datetime(2026, 1, 1, 11, 0, 0),
        due_date=datetime(2026, 9, 1)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, sort_by="due_date", sort_dir="desc")

    titles = [t.title for t in result]
    assert titles[0] == "Late date"   # Sep 2026 - latest
    assert titles[1] == "Early date"  # Mar 2026
    assert titles[2] == "No date"     # NULL - last


def test_list_by_user_sort_due_date_desc_null_tasks_last(repo, seeded_user, db_session):
    """NULL due_date tasks must be last in DESC order too."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="With date",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0),
        due_date=datetime(2026, 5, 1)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="No date",
        completed=False, created_at=datetime(2026, 1, 1, 11, 0, 0), due_date=None
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None, sort_by="due_date", sort_dir="desc")
    assert result[-1].title == "No date"
    assert result[0].title == "With date"


# ---------------------------------------------------------------------------
# list_by_user — sort_by=None still uses created_at DESC (regression)
# ---------------------------------------------------------------------------

def test_list_by_user_without_sort_params_uses_created_at_desc(repo, seeded_user, db_session):
    """list_by_user with no new params behaves as before (created_at DESC)."""
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="First",
        completed=False, created_at=datetime(2026, 1, 1, 8, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Second",
        completed=False, created_at=datetime(2026, 1, 1, 9, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None)
    assert result[0].title == "Second"
    assert result[1].title == "First"
