"""
Tests for task 2.1: Pydantic schemas with due_date field.

Covers:
- CreateTaskRequest accepts optional due_date as date
- CreateTaskRequest rejects malformed date strings (422)
- UpdateTaskRequest accepts optional due_date as date
- UpdateTaskRequest rejects malformed date strings (422)
- TaskResponse serializes due_date as "YYYY-MM-DD" string
- TaskResponse accepts due_date=None
"""
from datetime import date
import pytest
from pydantic import ValidationError


def test_create_task_request_accepts_valid_due_date():
    from app.schemas.tasks import CreateTaskRequest
    req = CreateTaskRequest(title="Task", due_date=date(2026, 5, 1))
    assert req.due_date == date(2026, 5, 1)


def test_create_task_request_due_date_defaults_to_none():
    from app.schemas.tasks import CreateTaskRequest
    req = CreateTaskRequest(title="Task")
    assert req.due_date is None


def test_create_task_request_accepts_none_due_date():
    from app.schemas.tasks import CreateTaskRequest
    req = CreateTaskRequest(title="Task", due_date=None)
    assert req.due_date is None


def test_create_task_request_accepts_iso_date_string():
    from app.schemas.tasks import CreateTaskRequest
    req = CreateTaskRequest(title="Task", due_date="2026-05-01")
    assert req.due_date == date(2026, 5, 1)


def test_create_task_request_rejects_malformed_date():
    from app.schemas.tasks import CreateTaskRequest
    with pytest.raises(ValidationError):
        CreateTaskRequest(title="Task", due_date="not-a-date")


def test_create_task_request_rejects_invalid_date():
    from app.schemas.tasks import CreateTaskRequest
    with pytest.raises(ValidationError):
        CreateTaskRequest(title="Task", due_date="2026-13-01")


def test_update_task_request_accepts_valid_due_date():
    from app.schemas.tasks import UpdateTaskRequest
    req = UpdateTaskRequest(title="Task", due_date=date(2026, 12, 31))
    assert req.due_date == date(2026, 12, 31)


def test_update_task_request_due_date_defaults_to_none():
    from app.schemas.tasks import UpdateTaskRequest
    req = UpdateTaskRequest(title="Task")
    assert req.due_date is None


def test_update_task_request_accepts_none_due_date():
    from app.schemas.tasks import UpdateTaskRequest
    req = UpdateTaskRequest(title="Task", due_date=None)
    assert req.due_date is None


def test_update_task_request_rejects_malformed_date():
    from app.schemas.tasks import UpdateTaskRequest
    with pytest.raises(ValidationError):
        UpdateTaskRequest(title="Task", due_date="bad-date")


def test_task_response_includes_due_date_field():
    from app.schemas.tasks import TaskResponse
    resp = TaskResponse(
        id="abc",
        userId="user-1",
        title="Test",
        completed=False,
        due_date=date(2026, 6, 15),
    )
    assert resp.due_date == date(2026, 6, 15)


def test_task_response_due_date_defaults_to_none():
    from app.schemas.tasks import TaskResponse
    resp = TaskResponse(id="abc", userId="user-1", title="Test", completed=False)
    assert resp.due_date is None


def test_task_response_due_date_serializes_as_iso_string():
    from app.schemas.tasks import TaskResponse
    resp = TaskResponse(
        id="abc",
        userId="user-1",
        title="Test",
        completed=False,
        due_date=date(2026, 6, 15),
    )
    data = resp.model_dump(mode="json")
    assert data["due_date"] == "2026-06-15"


def test_task_response_due_date_none_serializes_as_null():
    from app.schemas.tasks import TaskResponse
    resp = TaskResponse(id="abc", userId="user-1", title="Test", completed=False, due_date=None)
    data = resp.model_dump(mode="json")
    assert data["due_date"] is None
