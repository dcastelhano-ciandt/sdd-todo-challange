"""
Tests for search task 2.1: TaskService — keyword normalization before passing to repository.

Covers:
- Whitespace-only keyword → passes q=None to repository (no title filter)
- Non-empty keyword after stripping → forwarded unchanged to repository
- No keyword (None) → passes q=None to repository (backward-compatible)

Requirements: 3.1, 3.2, 3.3
"""
import uuid
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repo():
    """A mock TaskRepository that records calls to list_by_user."""
    repo = MagicMock()
    repo.list_by_user.return_value = []
    return repo


@pytest.fixture
def task_service(mock_repo):
    from app.services.task_service import TaskService
    return TaskService(task_repo=mock_repo)


# ---------------------------------------------------------------------------
# Requirement 3.3: None keyword → passes q=None to repository
# ---------------------------------------------------------------------------

def test_list_tasks_with_no_keyword_passes_none_to_repo(task_service, mock_repo):
    """Calling list_tasks without q passes q=None to the repository."""
    task_service.list_tasks(user_id="user-1")

    mock_repo.list_by_user.assert_called_once()
    call_kwargs = mock_repo.list_by_user.call_args.kwargs
    assert call_kwargs.get("q") is None


def test_list_tasks_with_none_keyword_passes_none_to_repo(task_service, mock_repo):
    """Calling list_tasks with q=None explicitly passes q=None to the repository."""
    task_service.list_tasks(user_id="user-1", q=None)

    mock_repo.list_by_user.assert_called_once()
    call_kwargs = mock_repo.list_by_user.call_args.kwargs
    assert call_kwargs.get("q") is None


# ---------------------------------------------------------------------------
# Requirement 3.3: Whitespace-only keyword → passes q=None to repository
# ---------------------------------------------------------------------------

def test_list_tasks_with_whitespace_only_keyword_passes_none_to_repo(task_service, mock_repo):
    """Whitespace-only keyword is normalized to None before being passed to the repository."""
    task_service.list_tasks(user_id="user-1", q="   ")

    mock_repo.list_by_user.assert_called_once()
    call_kwargs = mock_repo.list_by_user.call_args.kwargs
    assert call_kwargs.get("q") is None


def test_list_tasks_with_tab_only_keyword_passes_none_to_repo(task_service, mock_repo):
    """Tab-only keyword is normalized to None."""
    task_service.list_tasks(user_id="user-1", q="\t")

    mock_repo.list_by_user.assert_called_once()
    call_kwargs = mock_repo.list_by_user.call_args.kwargs
    assert call_kwargs.get("q") is None


def test_list_tasks_with_empty_string_keyword_passes_none_to_repo(task_service, mock_repo):
    """Empty string keyword is normalized to None."""
    task_service.list_tasks(user_id="user-1", q="")

    mock_repo.list_by_user.assert_called_once()
    call_kwargs = mock_repo.list_by_user.call_args.kwargs
    assert call_kwargs.get("q") is None


# ---------------------------------------------------------------------------
# Requirement 3.2: Non-empty keyword forwarded unchanged
# ---------------------------------------------------------------------------

def test_list_tasks_with_valid_keyword_forwards_keyword_to_repo(task_service, mock_repo):
    """Non-empty keyword after stripping is forwarded to the repository unchanged."""
    task_service.list_tasks(user_id="user-1", q="Meeting")

    mock_repo.list_by_user.assert_called_once()
    call_kwargs = mock_repo.list_by_user.call_args.kwargs
    assert call_kwargs.get("q") == "Meeting"


def test_list_tasks_with_lowercase_keyword_forwards_keyword_to_repo(task_service, mock_repo):
    """Lowercase keyword is forwarded unchanged (no case transformation at service layer)."""
    task_service.list_tasks(user_id="user-1", q="report")

    mock_repo.list_by_user.assert_called_once()
    call_kwargs = mock_repo.list_by_user.call_args.kwargs
    assert call_kwargs.get("q") == "report"


def test_list_tasks_with_padded_keyword_strips_and_forwards(task_service, mock_repo):
    """Keyword with surrounding whitespace is stripped before being forwarded."""
    task_service.list_tasks(user_id="user-1", q="  groceries  ")

    mock_repo.list_by_user.assert_called_once()
    call_kwargs = mock_repo.list_by_user.call_args.kwargs
    assert call_kwargs.get("q") == "groceries"


# ---------------------------------------------------------------------------
# Requirement 3.1: status filter still propagated alongside q
# ---------------------------------------------------------------------------

def test_list_tasks_with_keyword_and_status_passes_both_to_repo(task_service, mock_repo):
    """Both status and q are passed to the repository when both are provided."""
    task_service.list_tasks(user_id="user-1", status="pending", q="buy")

    mock_repo.list_by_user.assert_called_once()
    call_kwargs = mock_repo.list_by_user.call_args.kwargs
    assert call_kwargs.get("status") is False  # "pending" → completed=False
    assert call_kwargs.get("q") == "buy"


def test_list_tasks_with_keyword_and_completed_status_passes_both_to_repo(task_service, mock_repo):
    """Both completed status and q are passed to the repository."""
    task_service.list_tasks(user_id="user-1", status="completed", q="report")

    mock_repo.list_by_user.assert_called_once()
    call_kwargs = mock_repo.list_by_user.call_args.kwargs
    assert call_kwargs.get("status") is True  # "completed" → completed=True
    assert call_kwargs.get("q") == "report"
