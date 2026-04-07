"""
Tests for tasks 5.1, 5.2: TaskRouter — query params and due_date body forwarding.

Uses mock TaskService (bypasses DB and auth) to focus on router-level concerns.

Covers:
- GET /api/v1/tasks accepts sort_by=due_date query param
- GET /api/v1/tasks accepts sort_dir=asc|desc query param
- GET /api/v1/tasks rejects invalid sort_by (422)
- GET /api/v1/tasks rejects invalid sort_dir (422)
- GET /api/v1/tasks forwards sort_by and sort_dir to TaskService
- POST /api/v1/tasks forwards due_date from body to TaskService
- PUT /api/v1/tasks/{id} forwards due_date from body to TaskService
- POST /api/v1/tasks with invalid due_date → 422
- PUT /api/v1/tasks/{id} with invalid due_date → 422
"""
import uuid
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock
from fastapi.testclient import TestClient


def _make_mock_task(task_id=None, due_date=None):
    task = MagicMock()
    task.id = task_id or str(uuid.uuid4())
    task.userId = "user-mock"
    task.title = "Test Task"
    task.completed = False
    task.due_date = due_date
    return task


@pytest.fixture
def client_with_mocks():
    """TestClient with mocked auth + TaskService."""
    from app.main import app
    from app.dependencies import get_current_user
    from app.routers.tasks import get_task_service
    from app.dependencies import UserContext

    mock_user = UserContext(user_id="user-mock", jti="mock-jti")
    mock_service = MagicMock()

    def override_auth():
        return mock_user

    def override_service():
        return mock_service

    app.dependency_overrides[get_current_user] = override_auth
    app.dependency_overrides[get_task_service] = override_service

    with TestClient(app) as c:
        yield c, mock_service

    app.dependency_overrides.clear()


_TASKS_URL = "/api/v1/tasks"


def _task_url(task_id: str) -> str:
    return f"{_TASKS_URL}/{task_id}"


# ---------------------------------------------------------------------------
# GET /api/v1/tasks — sort query params
# ---------------------------------------------------------------------------

def test_list_tasks_accepts_sort_by_due_date(client_with_mocks):
    client, mock_service = client_with_mocks
    mock_service.list_tasks.return_value = []

    resp = client.get(f"{_TASKS_URL}?sort_by=due_date&sort_dir=asc")
    assert resp.status_code == 200


def test_list_tasks_accepts_sort_dir_desc(client_with_mocks):
    client, mock_service = client_with_mocks
    mock_service.list_tasks.return_value = []

    resp = client.get(f"{_TASKS_URL}?sort_by=due_date&sort_dir=desc")
    assert resp.status_code == 200


def test_list_tasks_rejects_invalid_sort_by(client_with_mocks):
    client, mock_service = client_with_mocks

    resp = client.get(f"{_TASKS_URL}?sort_by=some_column")
    assert resp.status_code == 422


def test_list_tasks_rejects_invalid_sort_dir(client_with_mocks):
    client, mock_service = client_with_mocks

    resp = client.get(f"{_TASKS_URL}?sort_by=due_date&sort_dir=random")
    assert resp.status_code == 422


def test_list_tasks_without_sort_params_returns_200(client_with_mocks):
    client, mock_service = client_with_mocks
    mock_service.list_tasks.return_value = []

    resp = client.get(_TASKS_URL)
    assert resp.status_code == 200


def test_list_tasks_forwards_sort_by_to_service(client_with_mocks):
    client, mock_service = client_with_mocks
    mock_service.list_tasks.return_value = []

    client.get(f"{_TASKS_URL}?sort_by=due_date&sort_dir=asc")

    call_kwargs = mock_service.list_tasks.call_args.kwargs
    assert call_kwargs.get("sort_by") == "due_date"
    assert call_kwargs.get("sort_dir") == "asc"


def test_list_tasks_forwards_sort_dir_desc_to_service(client_with_mocks):
    client, mock_service = client_with_mocks
    mock_service.list_tasks.return_value = []

    client.get(f"{_TASKS_URL}?sort_by=due_date&sort_dir=desc")

    call_kwargs = mock_service.list_tasks.call_args.kwargs
    assert call_kwargs.get("sort_dir") == "desc"


def test_list_tasks_no_sort_forwards_none_to_service(client_with_mocks):
    client, mock_service = client_with_mocks
    mock_service.list_tasks.return_value = []

    client.get(_TASKS_URL)

    call_kwargs = mock_service.list_tasks.call_args.kwargs
    assert call_kwargs.get("sort_by") is None


# ---------------------------------------------------------------------------
# POST /api/v1/tasks — due_date in request body
# ---------------------------------------------------------------------------

def test_create_task_with_due_date_returns_201(client_with_mocks):
    client, mock_service = client_with_mocks
    mock_service.create_task.return_value = _make_mock_task(due_date=date(2026, 8, 15))

    resp = client.post(
        _TASKS_URL,
        json={"title": "Task with date", "due_date": "2026-08-15"},
    )
    assert resp.status_code == 201


def test_create_task_response_includes_due_date(client_with_mocks):
    client, mock_service = client_with_mocks
    mock_service.create_task.return_value = _make_mock_task(due_date=date(2026, 9, 1))

    resp = client.post(
        _TASKS_URL,
        json={"title": "Dated task", "due_date": "2026-09-01"},
    )
    assert resp.status_code == 201
    assert "due_date" in resp.json()
    assert resp.json()["due_date"] == "2026-09-01"


def test_create_task_forwards_due_date_to_service(client_with_mocks):
    client, mock_service = client_with_mocks
    mock_service.create_task.return_value = _make_mock_task(due_date=date(2026, 8, 15))

    client.post(
        _TASKS_URL,
        json={"title": "Task", "due_date": "2026-08-15"},
    )

    call_kwargs = mock_service.create_task.call_args.kwargs
    assert call_kwargs.get("due_date") == date(2026, 8, 15)


def test_create_task_with_null_due_date_returns_201(client_with_mocks):
    client, mock_service = client_with_mocks
    mock_service.create_task.return_value = _make_mock_task(due_date=None)

    resp = client.post(
        _TASKS_URL,
        json={"title": "No date task", "due_date": None},
    )
    assert resp.status_code == 201
    assert resp.json()["due_date"] is None


def test_create_task_without_due_date_returns_201(client_with_mocks):
    client, mock_service = client_with_mocks
    mock_service.create_task.return_value = _make_mock_task(due_date=None)

    resp = client.post(_TASKS_URL, json={"title": "Simple task"})
    assert resp.status_code == 201
    assert resp.json()["due_date"] is None


def test_create_task_with_malformed_due_date_returns_422(client_with_mocks):
    client, mock_service = client_with_mocks

    resp = client.post(
        _TASKS_URL,
        json={"title": "Bad date", "due_date": "not-a-date"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/v1/tasks/{id} — due_date in request body
# ---------------------------------------------------------------------------

def test_update_task_with_due_date_returns_200(client_with_mocks):
    client, mock_service = client_with_mocks
    task_id = str(uuid.uuid4())
    mock_service.update_task.return_value = _make_mock_task(task_id=task_id, due_date=date(2026, 12, 31))

    resp = client.put(
        _task_url(task_id),
        json={"title": "Updated", "due_date": "2026-12-31"},
    )
    assert resp.status_code == 200
    assert resp.json()["due_date"] == "2026-12-31"


def test_update_task_forwards_due_date_to_service(client_with_mocks):
    client, mock_service = client_with_mocks
    task_id = str(uuid.uuid4())
    mock_service.update_task.return_value = _make_mock_task(task_id=task_id, due_date=date(2026, 12, 31))

    client.put(
        _task_url(task_id),
        json={"title": "Updated", "due_date": "2026-12-31"},
    )

    call_kwargs = mock_service.update_task.call_args.kwargs
    assert call_kwargs.get("due_date") == date(2026, 12, 31)


def test_update_task_clears_due_date_with_null(client_with_mocks):
    client, mock_service = client_with_mocks
    task_id = str(uuid.uuid4())
    mock_service.update_task.return_value = _make_mock_task(task_id=task_id, due_date=None)

    resp = client.put(
        _task_url(task_id),
        json={"title": "No date", "due_date": None},
    )
    assert resp.status_code == 200
    assert resp.json()["due_date"] is None


def test_update_task_with_malformed_due_date_returns_422(client_with_mocks):
    client, mock_service = client_with_mocks
    task_id = str(uuid.uuid4())

    resp = client.put(
        _task_url(task_id),
        json={"title": "Updated", "due_date": "bad-date"},
    )
    assert resp.status_code == 422
