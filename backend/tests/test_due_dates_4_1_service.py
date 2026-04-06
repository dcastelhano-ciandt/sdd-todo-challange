"""
Tests for tasks 4.1, 4.2: TaskService with due_date and sort parameters.

Covers:
- create_task forwards due_date to repository
- update_task forwards due_date to repository; due_date=None clears the field
- list_tasks forwards sort_by and sort_dir to repository
- list_tasks raises ValidationError on unknown sort_by value
- list_tasks raises ValidationError on unknown sort_dir value
- list_tasks accepts valid sort_by values (None, "due_date")
- list_tasks accepts valid sort_dir values ("asc", "desc")
"""
from datetime import date
import pytest
from unittest.mock import MagicMock, patch


def _make_service(mock_repo=None):
    from app.services.task_service import TaskService
    if mock_repo is None:
        mock_repo = MagicMock()
    return TaskService(task_repo=mock_repo), mock_repo


# ---------------------------------------------------------------------------
# create_task with due_date
# ---------------------------------------------------------------------------

def test_create_task_forwards_due_date_to_repository():
    service, mock_repo = _make_service()
    due = date(2026, 8, 15)
    mock_repo.create.return_value = MagicMock(id="t1", userId="u1", title="T", completed=False, due_date=due)

    service.create_task(user_id="u1", title="Task", due_date=due)

    call_kwargs = mock_repo.create.call_args
    assert call_kwargs.kwargs.get("due_date") == due or (
        len(call_kwargs.args) > 3 and call_kwargs.args[3] == due
    )


def test_create_task_forwards_none_due_date_to_repository():
    service, mock_repo = _make_service()
    mock_repo.create.return_value = MagicMock(id="t1", userId="u1", title="T", completed=False, due_date=None)

    service.create_task(user_id="u1", title="Task", due_date=None)

    call_kwargs = mock_repo.create.call_args
    # due_date should be None (or not provided, falling back to None default)
    kwarg_due = call_kwargs.kwargs.get("due_date")
    assert kwarg_due is None


def test_create_task_due_date_defaults_to_none():
    service, mock_repo = _make_service()
    mock_repo.create.return_value = MagicMock(id="t1", userId="u1", title="T", completed=False, due_date=None)

    service.create_task(user_id="u1", title="Task")

    call_kwargs = mock_repo.create.call_args
    kwarg_due = call_kwargs.kwargs.get("due_date")
    assert kwarg_due is None


# ---------------------------------------------------------------------------
# update_task with due_date
# ---------------------------------------------------------------------------

def test_update_task_sets_due_date_on_task_object():
    service, mock_repo = _make_service()
    due = date(2026, 10, 1)

    task = MagicMock()
    task.userId = "u1"
    mock_repo.get_by_id.return_value = task
    mock_repo.update.return_value = task

    service.update_task(task_id="t1", user_id="u1", title="Updated", due_date=due)

    assert task.due_date == due


def test_update_task_clears_due_date_when_none():
    service, mock_repo = _make_service()

    task = MagicMock()
    task.userId = "u1"
    task.due_date = date(2026, 5, 1)  # Existing due date
    mock_repo.get_by_id.return_value = task
    mock_repo.update.return_value = task

    service.update_task(task_id="t1", user_id="u1", title="Updated", due_date=None)

    assert task.due_date is None


def test_update_task_due_date_defaults_to_none():
    """When called without due_date, existing due_date is set to None."""
    service, mock_repo = _make_service()

    task = MagicMock()
    task.userId = "u1"
    mock_repo.get_by_id.return_value = task
    mock_repo.update.return_value = task

    service.update_task(task_id="t1", user_id="u1", title="Updated")

    assert task.due_date is None


# ---------------------------------------------------------------------------
# list_tasks with sort parameters
# ---------------------------------------------------------------------------

def test_list_tasks_forwards_sort_by_due_date_to_repository():
    service, mock_repo = _make_service()
    mock_repo.list_by_user.return_value = []

    service.list_tasks(user_id="u1", sort_by="due_date", sort_dir="asc")

    call_kwargs = mock_repo.list_by_user.call_args
    assert call_kwargs.kwargs.get("sort_by") == "due_date"
    assert call_kwargs.kwargs.get("sort_dir") == "asc"


def test_list_tasks_forwards_sort_dir_desc_to_repository():
    service, mock_repo = _make_service()
    mock_repo.list_by_user.return_value = []

    service.list_tasks(user_id="u1", sort_by="due_date", sort_dir="desc")

    call_kwargs = mock_repo.list_by_user.call_args
    assert call_kwargs.kwargs.get("sort_dir") == "desc"


def test_list_tasks_forwards_none_sort_by_to_repository():
    service, mock_repo = _make_service()
    mock_repo.list_by_user.return_value = []

    service.list_tasks(user_id="u1", sort_by=None)

    call_kwargs = mock_repo.list_by_user.call_args
    assert call_kwargs.kwargs.get("sort_by") is None


def test_list_tasks_raises_validation_error_on_unknown_sort_by():
    from app.core.exceptions import ValidationError
    service, mock_repo = _make_service()

    with pytest.raises(ValidationError):
        service.list_tasks(user_id="u1", sort_by="unknown_column")


def test_list_tasks_raises_validation_error_on_unknown_sort_dir():
    from app.core.exceptions import ValidationError
    service, mock_repo = _make_service()

    with pytest.raises(ValidationError):
        service.list_tasks(user_id="u1", sort_by="due_date", sort_dir="random")


def test_list_tasks_accepts_sort_by_none():
    service, mock_repo = _make_service()
    mock_repo.list_by_user.return_value = []

    # Should not raise
    service.list_tasks(user_id="u1", sort_by=None, sort_dir="asc")
    assert mock_repo.list_by_user.called


def test_list_tasks_accepts_sort_by_due_date():
    service, mock_repo = _make_service()
    mock_repo.list_by_user.return_value = []

    # Should not raise
    service.list_tasks(user_id="u1", sort_by="due_date", sort_dir="asc")
    assert mock_repo.list_by_user.called


def test_list_tasks_accepts_sort_dir_asc():
    service, mock_repo = _make_service()
    mock_repo.list_by_user.return_value = []

    service.list_tasks(user_id="u1", sort_dir="asc")
    assert mock_repo.list_by_user.called


def test_list_tasks_accepts_sort_dir_desc():
    service, mock_repo = _make_service()
    mock_repo.list_by_user.return_value = []

    service.list_tasks(user_id="u1", sort_dir="desc")
    assert mock_repo.list_by_user.called
