"""
Tests for task 5.1: TaskService — create_task and list_tasks.

Covers:
- create_task: valid title → persists task with UUID id, completed=False, correct userId
- create_task: empty title → raises ValidationError
- create_task: whitespace-only title → raises ValidationError
- create_task: UUID is generated at the service layer (not database)
- list_tasks: delegates to repository and returns tasks ordered by created_at DESC
- list_tasks: optional status filter (pending / completed / None)
- list_tasks: returns only tasks owned by the authenticated user
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
    engine.dispose()


@pytest.fixture
def user_id(db):
    """Insert a user and return its id."""
    from app.models.user import User
    uid = str(uuid.uuid4())
    user = User(id=uid, email="owner@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    return uid


@pytest.fixture
def other_user_id(db):
    """Insert a second user and return its id."""
    from app.models.user import User
    uid = str(uuid.uuid4())
    user = User(id=uid, email="other@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    return uid


@pytest.fixture
def task_service(db):
    from app.services.task_service import TaskService
    from app.repositories.task_repository import TaskRepository
    return TaskService(task_repo=TaskRepository(db))


# ---------------------------------------------------------------------------
# Module importability
# ---------------------------------------------------------------------------

def test_task_service_module_importable():
    import importlib
    mod = importlib.import_module("app.services.task_service")
    assert mod is not None


def test_task_service_class_exists():
    from app.services.task_service import TaskService
    assert TaskService is not None


# ---------------------------------------------------------------------------
# create_task — success
# ---------------------------------------------------------------------------

def test_create_task_returns_task_object(task_service, user_id):
    task = task_service.create_task(user_id=user_id, title="Buy groceries")
    assert task is not None


def test_create_task_sets_correct_user_id(task_service, user_id):
    task = task_service.create_task(user_id=user_id, title="My task")
    assert task.userId == user_id


def test_create_task_sets_correct_title(task_service, user_id):
    task = task_service.create_task(user_id=user_id, title="Write tests")
    assert task.title == "Write tests"


def test_create_task_sets_completed_false_by_default(task_service, user_id):
    task = task_service.create_task(user_id=user_id, title="New task")
    assert task.completed is False or task.completed == 0


def test_create_task_assigns_uuid_id(task_service, user_id):
    task = task_service.create_task(user_id=user_id, title="UUID test")
    # id must be a valid UUID string
    parsed = uuid.UUID(task.id)
    assert str(parsed) == task.id


def test_create_task_generates_unique_ids_for_each_task(task_service, user_id):
    task1 = task_service.create_task(user_id=user_id, title="First")
    task2 = task_service.create_task(user_id=user_id, title="Second")
    assert task1.id != task2.id


def test_create_task_persists_to_database(task_service, user_id, db):
    task = task_service.create_task(user_id=user_id, title="Persistent task")
    from app.models.task import Task
    found = db.get(Task, task.id)
    assert found is not None
    assert found.title == "Persistent task"


# ---------------------------------------------------------------------------
# create_task — validation
# ---------------------------------------------------------------------------

def test_create_task_raises_validation_error_for_empty_title(task_service, user_id):
    from app.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        task_service.create_task(user_id=user_id, title="")


def test_create_task_raises_validation_error_for_whitespace_only_title(task_service, user_id):
    from app.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        task_service.create_task(user_id=user_id, title="   ")


# ---------------------------------------------------------------------------
# list_tasks — basic delegation
# ---------------------------------------------------------------------------

def test_list_tasks_returns_list(task_service, user_id):
    result = task_service.list_tasks(user_id=user_id)
    assert isinstance(result, list)


def test_list_tasks_returns_empty_list_for_new_user(task_service, user_id):
    result = task_service.list_tasks(user_id=user_id)
    assert result == []


def test_list_tasks_returns_tasks_for_user(task_service, user_id):
    task_service.create_task(user_id=user_id, title="Task A")
    task_service.create_task(user_id=user_id, title="Task B")
    result = task_service.list_tasks(user_id=user_id)
    assert len(result) == 2


def test_list_tasks_does_not_return_other_users_tasks(task_service, user_id, other_user_id):
    task_service.create_task(user_id=user_id, title="My task")
    task_service.create_task(user_id=other_user_id, title="Their task")
    result = task_service.list_tasks(user_id=user_id)
    assert len(result) == 1
    assert result[0].title == "My task"


# ---------------------------------------------------------------------------
# list_tasks — status filter
# ---------------------------------------------------------------------------

def test_list_tasks_filter_pending_returns_only_incomplete(task_service, user_id, db):
    from app.models.task import Task
    from datetime import datetime

    db.add(Task(
        id=str(uuid.uuid4()), userId=user_id, title="Done",
        completed=True, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db.add(Task(
        id=str(uuid.uuid4()), userId=user_id, title="Pending",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 1)
    ))
    db.commit()

    result = task_service.list_tasks(user_id=user_id, status="pending")
    assert len(result) == 1
    assert result[0].title == "Pending"


def test_list_tasks_filter_completed_returns_only_complete(task_service, user_id, db):
    from app.models.task import Task
    from datetime import datetime

    db.add(Task(
        id=str(uuid.uuid4()), userId=user_id, title="Done",
        completed=True, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db.add(Task(
        id=str(uuid.uuid4()), userId=user_id, title="Pending",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 1)
    ))
    db.commit()

    result = task_service.list_tasks(user_id=user_id, status="completed")
    assert len(result) == 1
    assert result[0].title == "Done"


def test_list_tasks_no_filter_returns_all_tasks(task_service, user_id, db):
    from app.models.task import Task
    from datetime import datetime

    db.add(Task(
        id=str(uuid.uuid4()), userId=user_id, title="Done",
        completed=True, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db.add(Task(
        id=str(uuid.uuid4()), userId=user_id, title="Pending",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 1)
    ))
    db.commit()

    result = task_service.list_tasks(user_id=user_id, status=None)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# list_tasks — ordering
# ---------------------------------------------------------------------------

def test_list_tasks_ordered_by_created_at_desc(task_service, user_id, db):
    from app.models.task import Task
    from datetime import datetime

    db.add(Task(
        id=str(uuid.uuid4()), userId=user_id, title="Oldest",
        completed=False, created_at=datetime(2026, 1, 1, 10, 0, 0)
    ))
    db.add(Task(
        id=str(uuid.uuid4()), userId=user_id, title="Middle",
        completed=False, created_at=datetime(2026, 1, 1, 11, 0, 0)
    ))
    db.add(Task(
        id=str(uuid.uuid4()), userId=user_id, title="Newest",
        completed=False, created_at=datetime(2026, 1, 1, 12, 0, 0)
    ))
    db.commit()

    result = task_service.list_tasks(user_id=user_id)
    assert result[0].title == "Newest"
    assert result[1].title == "Middle"
    assert result[2].title == "Oldest"
