"""
Tests for task 5.2: TaskService — update_task, toggle_completion, delete_task.

Covers:
- update_task: valid title + ownership → persists and returns updated task
- update_task: empty title → raises ValidationError (never modifies task)
- update_task: whitespace-only title → raises ValidationError
- update_task: task not found → raises NotFoundError
- update_task: task owned by different user → raises ForbiddenError
- update_task: ownership check precedes mutation (task unchanged on ForbiddenError)

- toggle_completion: owner toggles pending task → completed becomes True
- toggle_completion: owner toggles completed task → completed becomes False
- toggle_completion: task not found → raises NotFoundError
- toggle_completion: task owned by different user → raises ForbiddenError

- delete_task: owner deletes task → task removed from database
- delete_task: task not found → raises NotFoundError
- delete_task: task owned by different user → raises ForbiddenError
- delete_task: ownership check precedes deletion (task intact on ForbiddenError)
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
    from app.models.user import User
    uid = str(uuid.uuid4())
    db.add(User(id=uid, email="owner@example.com", hashed_password="hashed"))
    db.commit()
    return uid


@pytest.fixture
def other_user_id(db):
    from app.models.user import User
    uid = str(uuid.uuid4())
    db.add(User(id=uid, email="other@example.com", hashed_password="hashed"))
    db.commit()
    return uid


@pytest.fixture
def task_service(db):
    from app.services.task_service import TaskService
    from app.repositories.task_repository import TaskRepository
    return TaskService(task_repo=TaskRepository(db))


@pytest.fixture
def existing_task(task_service, user_id):
    """Create and return a pending task owned by user_id."""
    return task_service.create_task(user_id=user_id, title="Original title")


@pytest.fixture
def completed_task(task_service, user_id):
    """Create and return a completed task owned by user_id."""
    task = task_service.create_task(user_id=user_id, title="Already done")
    return task_service.toggle_completion(task_id=task.id, user_id=user_id)


# ---------------------------------------------------------------------------
# update_task — success
# ---------------------------------------------------------------------------

def test_update_task_returns_updated_task(task_service, user_id, existing_task):
    updated = task_service.update_task(
        task_id=existing_task.id, user_id=user_id, title="New title"
    )
    assert updated is not None


def test_update_task_changes_title(task_service, user_id, existing_task):
    updated = task_service.update_task(
        task_id=existing_task.id, user_id=user_id, title="Updated title"
    )
    assert updated.title == "Updated title"


def test_update_task_preserves_other_fields(task_service, user_id, existing_task):
    """update_task must not alter userId, id, or completed."""
    original_id = existing_task.id
    original_user_id = existing_task.userId
    original_completed = existing_task.completed

    updated = task_service.update_task(
        task_id=existing_task.id, user_id=user_id, title="Changed title"
    )
    assert updated.id == original_id
    assert updated.userId == original_user_id
    assert updated.completed == original_completed


def test_update_task_persists_change_to_database(task_service, user_id, existing_task, db):
    task_service.update_task(
        task_id=existing_task.id, user_id=user_id, title="Persisted title"
    )
    from app.models.task import Task
    db.expire_all()
    found = db.get(Task, existing_task.id)
    assert found.title == "Persisted title"


# ---------------------------------------------------------------------------
# update_task — validation errors
# ---------------------------------------------------------------------------

def test_update_task_raises_validation_error_for_empty_title(task_service, user_id, existing_task):
    from app.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        task_service.update_task(task_id=existing_task.id, user_id=user_id, title="")


def test_update_task_raises_validation_error_for_whitespace_title(task_service, user_id, existing_task):
    from app.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        task_service.update_task(task_id=existing_task.id, user_id=user_id, title="   ")


def test_update_task_does_not_modify_task_on_validation_error(task_service, user_id, existing_task, db):
    from app.core.exceptions import ValidationError
    original_title = existing_task.title

    with pytest.raises(ValidationError):
        task_service.update_task(task_id=existing_task.id, user_id=user_id, title="")

    from app.models.task import Task
    db.expire_all()
    found = db.get(Task, existing_task.id)
    assert found.title == original_title


# ---------------------------------------------------------------------------
# update_task — not found
# ---------------------------------------------------------------------------

def test_update_task_raises_not_found_for_missing_task(task_service, user_id):
    from app.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        task_service.update_task(
            task_id=str(uuid.uuid4()), user_id=user_id, title="New title"
        )


# ---------------------------------------------------------------------------
# update_task — ownership enforcement
# ---------------------------------------------------------------------------

def test_update_task_raises_forbidden_for_wrong_user(task_service, user_id, other_user_id, existing_task):
    from app.core.exceptions import ForbiddenError
    with pytest.raises(ForbiddenError):
        task_service.update_task(
            task_id=existing_task.id, user_id=other_user_id, title="Hijacked title"
        )


def test_update_task_does_not_modify_task_on_forbidden(task_service, user_id, other_user_id, existing_task, db):
    """Ownership check precedes mutation; task must be unchanged on ForbiddenError."""
    from app.core.exceptions import ForbiddenError
    original_title = existing_task.title

    with pytest.raises(ForbiddenError):
        task_service.update_task(
            task_id=existing_task.id, user_id=other_user_id, title="Should not apply"
        )

    from app.models.task import Task
    db.expire_all()
    found = db.get(Task, existing_task.id)
    assert found.title == original_title


# ---------------------------------------------------------------------------
# toggle_completion — success
# ---------------------------------------------------------------------------

def test_toggle_completion_flips_false_to_true(task_service, user_id, existing_task):
    assert existing_task.completed is False or existing_task.completed == 0
    toggled = task_service.toggle_completion(task_id=existing_task.id, user_id=user_id)
    assert toggled.completed is True or toggled.completed == 1


def test_toggle_completion_flips_true_to_false(task_service, user_id, completed_task):
    assert completed_task.completed is True or completed_task.completed == 1
    toggled = task_service.toggle_completion(task_id=completed_task.id, user_id=user_id)
    assert toggled.completed is False or toggled.completed == 0


def test_toggle_completion_returns_updated_task(task_service, user_id, existing_task):
    result = task_service.toggle_completion(task_id=existing_task.id, user_id=user_id)
    assert result is not None
    assert result.id == existing_task.id


def test_toggle_completion_persists_to_database(task_service, user_id, existing_task, db):
    task_service.toggle_completion(task_id=existing_task.id, user_id=user_id)
    from app.models.task import Task
    db.expire_all()
    found = db.get(Task, existing_task.id)
    assert found.completed is True or found.completed == 1


def test_toggle_completion_twice_restores_original_state(task_service, user_id, existing_task):
    task_service.toggle_completion(task_id=existing_task.id, user_id=user_id)
    toggled_back = task_service.toggle_completion(task_id=existing_task.id, user_id=user_id)
    assert toggled_back.completed is False or toggled_back.completed == 0


# ---------------------------------------------------------------------------
# toggle_completion — not found
# ---------------------------------------------------------------------------

def test_toggle_completion_raises_not_found_for_missing_task(task_service, user_id):
    from app.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        task_service.toggle_completion(task_id=str(uuid.uuid4()), user_id=user_id)


# ---------------------------------------------------------------------------
# toggle_completion — ownership enforcement
# ---------------------------------------------------------------------------

def test_toggle_completion_raises_forbidden_for_wrong_user(task_service, user_id, other_user_id, existing_task):
    from app.core.exceptions import ForbiddenError
    with pytest.raises(ForbiddenError):
        task_service.toggle_completion(task_id=existing_task.id, user_id=other_user_id)


def test_toggle_completion_does_not_change_task_on_forbidden(task_service, user_id, other_user_id, existing_task, db):
    """Ownership check precedes mutation; task must be unchanged on ForbiddenError."""
    from app.core.exceptions import ForbiddenError
    original_completed = existing_task.completed

    with pytest.raises(ForbiddenError):
        task_service.toggle_completion(task_id=existing_task.id, user_id=other_user_id)

    from app.models.task import Task
    db.expire_all()
    found = db.get(Task, existing_task.id)
    assert found.completed == original_completed


# ---------------------------------------------------------------------------
# delete_task — success
# ---------------------------------------------------------------------------

def test_delete_task_removes_task_from_database(task_service, user_id, existing_task, db):
    task_service.delete_task(task_id=existing_task.id, user_id=user_id)
    from app.models.task import Task
    db.expire_all()
    assert db.get(Task, existing_task.id) is None


def test_delete_task_returns_none(task_service, user_id, existing_task):
    result = task_service.delete_task(task_id=existing_task.id, user_id=user_id)
    assert result is None


def test_delete_task_does_not_affect_other_tasks(task_service, user_id, db):
    from app.models.task import Task

    task1 = task_service.create_task(user_id=user_id, title="Keep this")
    task2 = task_service.create_task(user_id=user_id, title="Delete this")

    task_service.delete_task(task_id=task2.id, user_id=user_id)

    db.expire_all()
    assert db.get(Task, task1.id) is not None
    assert db.get(Task, task2.id) is None


# ---------------------------------------------------------------------------
# delete_task — not found
# ---------------------------------------------------------------------------

def test_delete_task_raises_not_found_for_missing_task(task_service, user_id):
    from app.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        task_service.delete_task(task_id=str(uuid.uuid4()), user_id=user_id)


# ---------------------------------------------------------------------------
# delete_task — ownership enforcement
# ---------------------------------------------------------------------------

def test_delete_task_raises_forbidden_for_wrong_user(task_service, user_id, other_user_id, existing_task):
    from app.core.exceptions import ForbiddenError
    with pytest.raises(ForbiddenError):
        task_service.delete_task(task_id=existing_task.id, user_id=other_user_id)


def test_delete_task_does_not_delete_on_forbidden(task_service, user_id, other_user_id, existing_task, db):
    """Ownership check precedes deletion; task must remain on ForbiddenError."""
    from app.core.exceptions import ForbiddenError
    with pytest.raises(ForbiddenError):
        task_service.delete_task(task_id=existing_task.id, user_id=other_user_id)

    from app.models.task import Task
    db.expire_all()
    assert db.get(Task, existing_task.id) is not None
