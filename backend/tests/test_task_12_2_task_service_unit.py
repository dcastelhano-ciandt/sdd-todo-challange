"""
Tests for task 12.2: TaskService unit tests.

Covers:
- create_task: valid title → persists task with correct userId, completed=False, UUID id
- create_task: empty title → raises ValidationError
- toggle_completion: owner calls → flips completed boolean
- toggle_completion: different user calls → raises ForbiddenError
- update_task: ownership violation → raises ForbiddenError
- update_task: missing task id → raises NotFoundError
- update_task: valid owner + title → returns updated task
- update_task: empty title → raises ValidationError
- delete_task: ownership violation → raises ForbiddenError
- delete_task: missing task id → raises NotFoundError
- delete_task: valid owner → removes task

Requirements: 3.1, 3.2, 5.2, 6.3, 7.2, 7.3
"""
import uuid
import pytest


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
def owner_id(db):
    """Insert the task-owner user and return its id."""
    from app.models.user import User
    uid = str(uuid.uuid4())
    db.add(User(id=uid, email="owner12@example.com", hashed_password="hashed"))
    db.commit()
    return uid


@pytest.fixture
def other_user_id(db):
    """Insert a second user (non-owner) and return its id."""
    from app.models.user import User
    uid = str(uuid.uuid4())
    db.add(User(id=uid, email="other12@example.com", hashed_password="hashed"))
    db.commit()
    return uid


@pytest.fixture
def task_service(db):
    from app.services.task_service import TaskService
    from app.repositories.task_repository import TaskRepository
    return TaskService(task_repo=TaskRepository(db))


# ---------------------------------------------------------------------------
# Helper: create a task directly via the service
# ---------------------------------------------------------------------------

def _make_task(task_service, owner_id, title="Test task"):
    return task_service.create_task(user_id=owner_id, title=title)


# ---------------------------------------------------------------------------
# create_task — valid title (req 3.1, 3.3, 3.4)
# ---------------------------------------------------------------------------

def test_create_task_valid_title_returns_task_object(task_service, owner_id):
    task = task_service.create_task(user_id=owner_id, title="Buy milk")
    assert task is not None


def test_create_task_sets_correct_user_id(task_service, owner_id):
    task = task_service.create_task(user_id=owner_id, title="Buy milk")
    assert task.userId == owner_id


def test_create_task_sets_correct_title(task_service, owner_id):
    task = task_service.create_task(user_id=owner_id, title="Write tests")
    assert task.title == "Write tests"


def test_create_task_sets_completed_false_by_default(task_service, owner_id):
    task = task_service.create_task(user_id=owner_id, title="New task")
    assert task.completed is False or task.completed == 0


def test_create_task_assigns_uuid_id(task_service, owner_id):
    task = task_service.create_task(user_id=owner_id, title="UUID check")
    parsed = uuid.UUID(task.id)
    assert str(parsed) == task.id


# ---------------------------------------------------------------------------
# create_task — empty title → ValidationError (req 3.2)
# ---------------------------------------------------------------------------

def test_create_task_empty_title_raises_validation_error(task_service, owner_id):
    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        task_service.create_task(user_id=owner_id, title="")


def test_create_task_whitespace_only_title_raises_validation_error(task_service, owner_id):
    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        task_service.create_task(user_id=owner_id, title="   ")


# ---------------------------------------------------------------------------
# toggle_completion — owner (req 6.1, 6.2)
# ---------------------------------------------------------------------------

def test_toggle_completion_by_owner_flips_false_to_true(task_service, owner_id):
    task = _make_task(task_service, owner_id, "Toggle me")
    assert task.completed is False or task.completed == 0

    toggled = task_service.toggle_completion(task_id=task.id, user_id=owner_id)
    assert toggled.completed is True or toggled.completed == 1


def test_toggle_completion_by_owner_flips_true_to_false(task_service, owner_id, db):
    from app.models.task import Task

    task_id = str(uuid.uuid4())
    t = Task(id=task_id, userId=owner_id, title="Already done", completed=True)
    db.add(t)
    db.commit()

    toggled = task_service.toggle_completion(task_id=task_id, user_id=owner_id)
    assert toggled.completed is False or toggled.completed == 0


def test_toggle_completion_by_owner_returns_task_object(task_service, owner_id):
    task = _make_task(task_service, owner_id, "Return check")
    result = task_service.toggle_completion(task_id=task.id, user_id=owner_id)
    assert result is not None
    assert result.id == task.id


# ---------------------------------------------------------------------------
# toggle_completion — different user → ForbiddenError (req 6.3)
# ---------------------------------------------------------------------------

def test_toggle_completion_by_different_user_raises_forbidden_error(
    task_service, owner_id, other_user_id
):
    from app.core.exceptions import ForbiddenError

    task = _make_task(task_service, owner_id, "Owner's task")
    with pytest.raises(ForbiddenError):
        task_service.toggle_completion(task_id=task.id, user_id=other_user_id)


def test_toggle_completion_by_different_user_does_not_modify_task(
    task_service, owner_id, other_user_id, db
):
    """Data must remain unchanged after a forbidden toggle attempt."""
    from app.core.exceptions import ForbiddenError
    from app.models.task import Task

    task = _make_task(task_service, owner_id, "Protected task")
    original_completed = task.completed

    try:
        task_service.toggle_completion(task_id=task.id, user_id=other_user_id)
    except ForbiddenError:
        pass

    unchanged = db.get(Task, task.id)
    assert unchanged.completed == original_completed


# ---------------------------------------------------------------------------
# toggle_completion — non-existent task → NotFoundError
# ---------------------------------------------------------------------------

def test_toggle_completion_nonexistent_task_raises_not_found_error(task_service, owner_id):
    from app.core.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        task_service.toggle_completion(task_id=str(uuid.uuid4()), user_id=owner_id)


# ---------------------------------------------------------------------------
# update_task — valid owner + title (req 5.1)
# ---------------------------------------------------------------------------

def test_update_task_valid_owner_returns_updated_task(task_service, owner_id):
    task = _make_task(task_service, owner_id, "Old title")
    result = task_service.update_task(task_id=task.id, user_id=owner_id, title="New title")
    assert result.title == "New title"


def test_update_task_valid_owner_preserves_id_and_user_id(task_service, owner_id):
    task = _make_task(task_service, owner_id, "Original title")
    result = task_service.update_task(task_id=task.id, user_id=owner_id, title="Updated")
    assert result.id == task.id
    assert result.userId == owner_id


# ---------------------------------------------------------------------------
# update_task — ownership violation → ForbiddenError (req 5.2)
# ---------------------------------------------------------------------------

def test_update_task_by_different_user_raises_forbidden_error(
    task_service, owner_id, other_user_id
):
    from app.core.exceptions import ForbiddenError

    task = _make_task(task_service, owner_id, "Owner's task")
    with pytest.raises(ForbiddenError):
        task_service.update_task(task_id=task.id, user_id=other_user_id, title="Hijacked")


def test_update_task_by_different_user_does_not_modify_task(
    task_service, owner_id, other_user_id, db
):
    """Title must remain unchanged after a forbidden update attempt."""
    from app.core.exceptions import ForbiddenError
    from app.models.task import Task

    task = _make_task(task_service, owner_id, "Original title")

    try:
        task_service.update_task(task_id=task.id, user_id=other_user_id, title="Hijacked")
    except ForbiddenError:
        pass

    unchanged = db.get(Task, task.id)
    assert unchanged.title == "Original title"


# ---------------------------------------------------------------------------
# update_task — missing task id → NotFoundError (req 7.3)
# ---------------------------------------------------------------------------

def test_update_task_nonexistent_id_raises_not_found_error(task_service, owner_id):
    from app.core.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        task_service.update_task(
            task_id=str(uuid.uuid4()), user_id=owner_id, title="Ghost task"
        )


# ---------------------------------------------------------------------------
# update_task — empty title → ValidationError (req 5.3)
# ---------------------------------------------------------------------------

def test_update_task_empty_title_raises_validation_error(task_service, owner_id):
    from app.core.exceptions import ValidationError

    task = _make_task(task_service, owner_id, "Has a title")
    with pytest.raises(ValidationError):
        task_service.update_task(task_id=task.id, user_id=owner_id, title="")


def test_update_task_whitespace_only_title_raises_validation_error(task_service, owner_id):
    from app.core.exceptions import ValidationError

    task = _make_task(task_service, owner_id, "Has a title")
    with pytest.raises(ValidationError):
        task_service.update_task(task_id=task.id, user_id=owner_id, title="   ")


# ---------------------------------------------------------------------------
# delete_task — valid owner (req 7.1)
# ---------------------------------------------------------------------------

def test_delete_task_valid_owner_removes_task(task_service, owner_id, db):
    from app.models.task import Task

    task = _make_task(task_service, owner_id, "To be deleted")
    task_id = task.id

    task_service.delete_task(task_id=task_id, user_id=owner_id)

    assert db.get(Task, task_id) is None


def test_delete_task_valid_owner_returns_none(task_service, owner_id):
    task = _make_task(task_service, owner_id, "Deleted")
    result = task_service.delete_task(task_id=task.id, user_id=owner_id)
    assert result is None


# ---------------------------------------------------------------------------
# delete_task — ownership violation → ForbiddenError (req 7.2)
# ---------------------------------------------------------------------------

def test_delete_task_by_different_user_raises_forbidden_error(
    task_service, owner_id, other_user_id
):
    from app.core.exceptions import ForbiddenError

    task = _make_task(task_service, owner_id, "Owner's task")
    with pytest.raises(ForbiddenError):
        task_service.delete_task(task_id=task.id, user_id=other_user_id)


def test_delete_task_by_different_user_does_not_remove_task(
    task_service, owner_id, other_user_id, db
):
    """Task must still exist after a forbidden delete attempt."""
    from app.core.exceptions import ForbiddenError
    from app.models.task import Task

    task = _make_task(task_service, owner_id, "Survives attack")
    task_id = task.id

    try:
        task_service.delete_task(task_id=task_id, user_id=other_user_id)
    except ForbiddenError:
        pass

    assert db.get(Task, task_id) is not None


# ---------------------------------------------------------------------------
# delete_task — missing task id → NotFoundError (req 7.3)
# ---------------------------------------------------------------------------

def test_delete_task_nonexistent_id_raises_not_found_error(task_service, owner_id):
    from app.core.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        task_service.delete_task(task_id=str(uuid.uuid4()), user_id=owner_id)
