"""
Tests for task 3.3: TaskRepository implementation.

Covers:
- create: persists a task with user_id, task_id, title; completed=False; created_at set
- list_by_user: returns tasks for a user ordered by created_at DESC
- list_by_user: optional completed filter (True/False)
- list_by_user: does NOT return tasks owned by other users
- get_by_id: returns task when found, None when not found
- update: persists mutated task fields
- delete: removes the task from the database
"""
import importlib
import time
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
    """Insert a user directly and return its id."""
    from app.models.user import User
    user = User(id="user-001", email="owner@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    return "user-001"


@pytest.fixture
def other_user(db_session):
    """Insert a second user and return its id."""
    from app.models.user import User
    user = User(id="user-002", email="other@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    return "user-002"


# ---------------------------------------------------------------------------
# Module importability
# ---------------------------------------------------------------------------

def test_task_repository_module_importable():
    mod = importlib.import_module("app.repositories.task_repository")
    assert mod is not None


def test_task_repository_class_exists():
    from app.repositories.task_repository import TaskRepository
    assert TaskRepository is not None


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

def test_create_returns_task_with_correct_fields(repo, seeded_user):
    import uuid
    task_id = str(uuid.uuid4())
    task = repo.create(user_id=seeded_user, task_id=task_id, title="Buy milk")
    assert task.id == task_id
    assert task.userId == seeded_user
    assert task.title == "Buy milk"


def test_create_sets_completed_false_by_default(repo, seeded_user):
    import uuid
    task = repo.create(user_id=seeded_user, task_id=str(uuid.uuid4()), title="New task")
    assert task.completed is False or task.completed == 0


def test_create_sets_created_at(repo, seeded_user):
    import uuid
    task = repo.create(user_id=seeded_user, task_id=str(uuid.uuid4()), title="With timestamp")
    assert task.created_at is not None


def test_create_persists_to_database(repo, seeded_user, db_session):
    import uuid
    task_id = str(uuid.uuid4())
    repo.create(user_id=seeded_user, task_id=task_id, title="Persisted task")
    from app.models.task import Task
    found = db_session.get(Task, task_id)
    assert found is not None
    assert found.title == "Persisted task"


# ---------------------------------------------------------------------------
# list_by_user
# ---------------------------------------------------------------------------

def test_list_by_user_returns_empty_for_new_user(repo, seeded_user):
    result = repo.list_by_user(user_id=seeded_user, status=None)
    assert result == []


def test_list_by_user_returns_tasks_for_user(repo, seeded_user):
    import uuid
    repo.create(user_id=seeded_user, task_id=str(uuid.uuid4()), title="Task A")
    repo.create(user_id=seeded_user, task_id=str(uuid.uuid4()), title="Task B")
    result = repo.list_by_user(user_id=seeded_user, status=None)
    assert len(result) == 2


def test_list_by_user_does_not_return_other_users_tasks(repo, seeded_user, other_user):
    import uuid
    repo.create(user_id=seeded_user, task_id=str(uuid.uuid4()), title="My task")
    repo.create(user_id=other_user, task_id=str(uuid.uuid4()), title="Their task")
    result = repo.list_by_user(user_id=seeded_user, status=None)
    assert len(result) == 1
    assert result[0].title == "My task"


def test_list_by_user_ordered_by_created_at_desc(repo, seeded_user, db_session):
    """Tasks should be returned newest first."""
    import uuid
    from app.models.task import Task
    from datetime import datetime

    t1_id = str(uuid.uuid4())
    t2_id = str(uuid.uuid4())
    t3_id = str(uuid.uuid4())

    # Insert with explicit created_at values to control ordering
    db_session.add(Task(
        id=t1_id, userId=seeded_user, title="Oldest", completed=False,
        created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.add(Task(
        id=t2_id, userId=seeded_user, title="Middle", completed=False,
        created_at=datetime(2026, 1, 1, 11, 0, 0)
    ))
    db_session.add(Task(
        id=t3_id, userId=seeded_user, title="Newest", completed=False,
        created_at=datetime(2026, 1, 1, 12, 0, 0)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None)
    assert len(result) == 3
    assert result[0].title == "Newest"
    assert result[1].title == "Middle"
    assert result[2].title == "Oldest"


def test_list_by_user_filter_completed_true(repo, seeded_user, db_session):
    import uuid
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Done",
        completed=True, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Pending",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 1)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=True)
    assert len(result) == 1
    assert result[0].title == "Done"


def test_list_by_user_filter_completed_false(repo, seeded_user, db_session):
    import uuid
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Done",
        completed=True, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Pending",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 1)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=False)
    assert len(result) == 1
    assert result[0].title == "Pending"


def test_list_by_user_no_filter_returns_all(repo, seeded_user, db_session):
    import uuid
    from app.models.task import Task

    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Done",
        completed=True, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db_session.add(Task(
        id=str(uuid.uuid4()), userId=seeded_user, title="Pending",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 1)
    ))
    db_session.commit()

    result = repo.list_by_user(user_id=seeded_user, status=None)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

def test_get_by_id_returns_none_when_not_found(repo):
    result = repo.get_by_id("nonexistent-task-id")
    assert result is None


def test_get_by_id_returns_task_when_found(repo, seeded_user):
    import uuid
    task_id = str(uuid.uuid4())
    repo.create(user_id=seeded_user, task_id=task_id, title="Find me")
    result = repo.get_by_id(task_id)
    assert result is not None
    assert result.id == task_id
    assert result.title == "Find me"


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

def test_update_persists_title_change(repo, seeded_user):
    import uuid
    task_id = str(uuid.uuid4())
    task = repo.create(user_id=seeded_user, task_id=task_id, title="Original")
    task.title = "Updated title"
    updated = repo.update(task)
    assert updated.title == "Updated title"


def test_update_persists_completed_change(repo, seeded_user):
    import uuid
    task_id = str(uuid.uuid4())
    task = repo.create(user_id=seeded_user, task_id=task_id, title="Toggle me")
    task.completed = True
    updated = repo.update(task)
    assert updated.completed is True


def test_update_change_is_persisted_after_refetch(repo, seeded_user, db_session):
    import uuid
    task_id = str(uuid.uuid4())
    task = repo.create(user_id=seeded_user, task_id=task_id, title="Before")
    task.title = "After"
    repo.update(task)
    db_session.expire_all()
    refetched = repo.get_by_id(task_id)
    assert refetched.title == "After"


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_removes_task_from_database(repo, seeded_user):
    import uuid
    task_id = str(uuid.uuid4())
    task = repo.create(user_id=seeded_user, task_id=task_id, title="Delete me")
    repo.delete(task)
    assert repo.get_by_id(task_id) is None


def test_delete_does_not_affect_other_tasks(repo, seeded_user):
    import uuid
    t1_id = str(uuid.uuid4())
    t2_id = str(uuid.uuid4())
    t1 = repo.create(user_id=seeded_user, task_id=t1_id, title="Keep")
    t2 = repo.create(user_id=seeded_user, task_id=t2_id, title="Remove")
    repo.delete(t2)
    assert repo.get_by_id(t1_id) is not None
    assert repo.get_by_id(t2_id) is None
