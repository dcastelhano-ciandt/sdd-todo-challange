"""
Tests for task 6.2: Task router — Pydantic schemas + HTTP endpoints.

Covers:
POST /api/v1/tasks
- 201 + TaskResponse on valid creation
- 422 on missing title
- 422 on empty title (min_length=1)
- 401 when not authenticated

GET /api/v1/tasks
- 200 + TaskListResponse with tasks owned by the user
- Tasks from other users are not included
- ?status=pending filters only incomplete tasks
- ?status=completed filters only completed tasks
- 401 when not authenticated

PUT /api/v1/tasks/{task_id}
- 200 + TaskResponse on successful update
- 422 on empty title
- 403 when task not owned by user
- 404 when task does not exist
- 401 when not authenticated

PATCH /api/v1/tasks/{task_id}/toggle
- 200 + TaskResponse after toggling
- 403 when task not owned by user
- 404 when task does not exist
- 401 when not authenticated

DELETE /api/v1/tasks/{task_id}
- 200 + MessageResponse on success
- 403 when task not owned by user
- 404 when task does not exist
- 401 when not authenticated

UUID validation:
- 422 when task_id is not a valid UUID format

Pydantic schemas:
- CreateTaskRequest: title min_length=1
- UpdateTaskRequest: title min_length=1
- TaskResponse: id, userId, title, completed fields
- TaskListResponse: tasks list field
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models.base import Base
import app.models  # noqa: F401 — registers all ORM models


# ---------------------------------------------------------------------------
# App + client fixtures using an in-memory SQLite database
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def client(test_engine):
    """TestClient wired to an in-memory database via dependency override."""
    from app.main import app
    from app.dependencies import get_db

    def override_get_db():
        session = Session(test_engine)
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# URL constants
# ---------------------------------------------------------------------------

_REGISTER_URL = "/api/v1/auth/register"
_TASKS_URL = "/api/v1/tasks"
_VALID_PASSWORD = "secret123"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_and_get_token(client, email: str) -> str:
    resp = client.post(_REGISTER_URL, json={"email": email, "password": _VALID_PASSWORD})
    assert resp.status_code == 201, resp.json()
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _task_url(task_id: str) -> str:
    return f"{_TASKS_URL}/{task_id}"


def _toggle_url(task_id: str) -> str:
    return f"{_TASKS_URL}/{task_id}/toggle"


# ---------------------------------------------------------------------------
# Pydantic schema: CreateTaskRequest validation
# ---------------------------------------------------------------------------

def test_create_task_422_on_missing_title(client):
    token = _register_and_get_token(client, "schema_create_6@example.com")
    resp = client.post(_TASKS_URL, json={}, headers=_auth_headers(token))
    assert resp.status_code == 422


def test_create_task_422_on_empty_title(client):
    token = _register_and_get_token(client, "schema_empty_6@example.com")
    resp = client.post(_TASKS_URL, json={"title": ""}, headers=_auth_headers(token))
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/tasks — success
# ---------------------------------------------------------------------------

def test_create_task_returns_201(client):
    token = _register_and_get_token(client, "create6@example.com")
    resp = client.post(_TASKS_URL, json={"title": "Buy groceries"}, headers=_auth_headers(token))
    assert resp.status_code == 201


def test_create_task_response_has_id(client):
    token = _register_and_get_token(client, "create6b@example.com")
    resp = client.post(_TASKS_URL, json={"title": "Task A"}, headers=_auth_headers(token))
    body = resp.json()
    assert "id" in body
    assert isinstance(body["id"], str)
    assert len(body["id"]) > 0


def test_create_task_response_has_title(client):
    token = _register_and_get_token(client, "create6c@example.com")
    resp = client.post(_TASKS_URL, json={"title": "My task"}, headers=_auth_headers(token))
    assert resp.json()["title"] == "My task"


def test_create_task_response_has_completed_false(client):
    token = _register_and_get_token(client, "create6d@example.com")
    resp = client.post(_TASKS_URL, json={"title": "Not done yet"}, headers=_auth_headers(token))
    assert resp.json()["completed"] is False


def test_create_task_response_has_user_id(client):
    token = _register_and_get_token(client, "create6e@example.com")
    resp = client.post(_TASKS_URL, json={"title": "Task for user"}, headers=_auth_headers(token))
    body = resp.json()
    assert "userId" in body
    assert isinstance(body["userId"], str)


# ---------------------------------------------------------------------------
# POST /api/v1/tasks — unauthenticated
# ---------------------------------------------------------------------------

def test_create_task_401_without_token(client):
    resp = client.post(_TASKS_URL, json={"title": "Unauthorized"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/tasks — success
# ---------------------------------------------------------------------------

def test_list_tasks_returns_200(client):
    token = _register_and_get_token(client, "list6@example.com")
    resp = client.get(_TASKS_URL, headers=_auth_headers(token))
    assert resp.status_code == 200


def test_list_tasks_response_has_tasks_field(client):
    token = _register_and_get_token(client, "list6b@example.com")
    resp = client.get(_TASKS_URL, headers=_auth_headers(token))
    body = resp.json()
    assert "tasks" in body
    assert isinstance(body["tasks"], list)


def test_list_tasks_returns_only_user_tasks(client):
    """User A tasks must not appear in User B's task list."""
    token_a = _register_and_get_token(client, "list6_userA@example.com")
    token_b = _register_and_get_token(client, "list6_userB@example.com")

    client.post(_TASKS_URL, json={"title": "User A task"}, headers=_auth_headers(token_a))

    resp = client.get(_TASKS_URL, headers=_auth_headers(token_b))
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "User A task" not in titles


def test_list_tasks_includes_own_tasks(client):
    token = _register_and_get_token(client, "list6_own@example.com")
    client.post(_TASKS_URL, json={"title": "My own task"}, headers=_auth_headers(token))
    resp = client.get(_TASKS_URL, headers=_auth_headers(token))
    titles = [t["title"] for t in resp.json()["tasks"]]
    assert "My own task" in titles


def test_list_tasks_empty_list_for_new_user(client):
    token = _register_and_get_token(client, "list6_new@example.com")
    resp = client.get(_TASKS_URL, headers=_auth_headers(token))
    assert resp.json()["tasks"] == []


# ---------------------------------------------------------------------------
# GET /api/v1/tasks?status= — filtering
# ---------------------------------------------------------------------------

def test_list_tasks_filter_pending(client):
    token = _register_and_get_token(client, "filter6_pending@example.com")
    # Create two tasks; complete one
    r1 = client.post(_TASKS_URL, json={"title": "Pending task"}, headers=_auth_headers(token))
    r2 = client.post(_TASKS_URL, json={"title": "Done task"}, headers=_auth_headers(token))
    task_id_done = r2.json()["id"]
    client.patch(_toggle_url(task_id_done), headers=_auth_headers(token))

    resp = client.get(f"{_TASKS_URL}?status=pending", headers=_auth_headers(token))
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "Pending task" in titles
    assert "Done task" not in titles


def test_list_tasks_filter_completed(client):
    token = _register_and_get_token(client, "filter6_completed@example.com")
    r1 = client.post(_TASKS_URL, json={"title": "Still pending"}, headers=_auth_headers(token))
    r2 = client.post(_TASKS_URL, json={"title": "Already done"}, headers=_auth_headers(token))
    task_id_done = r2.json()["id"]
    client.patch(_toggle_url(task_id_done), headers=_auth_headers(token))

    resp = client.get(f"{_TASKS_URL}?status=completed", headers=_auth_headers(token))
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "Already done" in titles
    assert "Still pending" not in titles


def test_list_tasks_no_filter_returns_all(client):
    token = _register_and_get_token(client, "filter6_all@example.com")
    r1 = client.post(_TASKS_URL, json={"title": "Pending one"}, headers=_auth_headers(token))
    r2 = client.post(_TASKS_URL, json={"title": "Completed one"}, headers=_auth_headers(token))
    task_id_done = r2.json()["id"]
    client.patch(_toggle_url(task_id_done), headers=_auth_headers(token))

    resp = client.get(_TASKS_URL, headers=_auth_headers(token))
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "Pending one" in titles
    assert "Completed one" in titles


# ---------------------------------------------------------------------------
# GET /api/v1/tasks — unauthenticated
# ---------------------------------------------------------------------------

def test_list_tasks_401_without_token(client):
    resp = client.get(_TASKS_URL)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/v1/tasks/{task_id} — success
# ---------------------------------------------------------------------------

def test_update_task_returns_200(client):
    token = _register_and_get_token(client, "update6@example.com")
    task_id = client.post(_TASKS_URL, json={"title": "Old title"}, headers=_auth_headers(token)).json()["id"]
    resp = client.put(_task_url(task_id), json={"title": "New title"}, headers=_auth_headers(token))
    assert resp.status_code == 200


def test_update_task_response_has_updated_title(client):
    token = _register_and_get_token(client, "update6b@example.com")
    task_id = client.post(_TASKS_URL, json={"title": "Before"}, headers=_auth_headers(token)).json()["id"]
    resp = client.put(_task_url(task_id), json={"title": "After"}, headers=_auth_headers(token))
    assert resp.json()["title"] == "After"


def test_update_task_response_preserves_id(client):
    token = _register_and_get_token(client, "update6c@example.com")
    task_id = client.post(_TASKS_URL, json={"title": "Keep my id"}, headers=_auth_headers(token)).json()["id"]
    resp = client.put(_task_url(task_id), json={"title": "Updated"}, headers=_auth_headers(token))
    assert resp.json()["id"] == task_id


# ---------------------------------------------------------------------------
# PUT /api/v1/tasks/{task_id} — validation errors
# ---------------------------------------------------------------------------

def test_update_task_422_on_empty_title(client):
    token = _register_and_get_token(client, "update6_empty@example.com")
    task_id = client.post(_TASKS_URL, json={"title": "Has title"}, headers=_auth_headers(token)).json()["id"]
    resp = client.put(_task_url(task_id), json={"title": ""}, headers=_auth_headers(token))
    assert resp.status_code in (422,)


def test_update_task_422_on_missing_title(client):
    token = _register_and_get_token(client, "update6_missing@example.com")
    task_id = client.post(_TASKS_URL, json={"title": "Has title"}, headers=_auth_headers(token)).json()["id"]
    resp = client.put(_task_url(task_id), json={}, headers=_auth_headers(token))
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/v1/tasks/{task_id} — authorization and not found
# ---------------------------------------------------------------------------

def test_update_task_403_when_not_owner(client):
    token_owner = _register_and_get_token(client, "update6_owner@example.com")
    token_other = _register_and_get_token(client, "update6_other@example.com")
    task_id = client.post(
        _TASKS_URL, json={"title": "Owner's task"}, headers=_auth_headers(token_owner)
    ).json()["id"]
    resp = client.put(_task_url(task_id), json={"title": "Hijacked"}, headers=_auth_headers(token_other))
    assert resp.status_code == 403


def test_update_task_404_when_not_found(client):
    token = _register_and_get_token(client, "update6_notfound@example.com")
    missing_id = str(uuid.uuid4())
    resp = client.put(_task_url(missing_id), json={"title": "Ghost"}, headers=_auth_headers(token))
    assert resp.status_code == 404


def test_update_task_401_without_token(client):
    resp = client.put(_task_url(str(uuid.uuid4())), json={"title": "Unauth"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /api/v1/tasks/{task_id}/toggle — success
# ---------------------------------------------------------------------------

def test_toggle_task_returns_200(client):
    token = _register_and_get_token(client, "toggle6@example.com")
    task_id = client.post(_TASKS_URL, json={"title": "Toggleable"}, headers=_auth_headers(token)).json()["id"]
    resp = client.patch(_toggle_url(task_id), headers=_auth_headers(token))
    assert resp.status_code == 200


def test_toggle_task_flips_completed_to_true(client):
    token = _register_and_get_token(client, "toggle6b@example.com")
    task_id = client.post(_TASKS_URL, json={"title": "Not done"}, headers=_auth_headers(token)).json()["id"]
    resp = client.patch(_toggle_url(task_id), headers=_auth_headers(token))
    assert resp.json()["completed"] is True


def test_toggle_task_flips_completed_back_to_false(client):
    token = _register_and_get_token(client, "toggle6c@example.com")
    task_id = client.post(_TASKS_URL, json={"title": "Toggle twice"}, headers=_auth_headers(token)).json()["id"]
    client.patch(_toggle_url(task_id), headers=_auth_headers(token))
    resp = client.patch(_toggle_url(task_id), headers=_auth_headers(token))
    assert resp.json()["completed"] is False


def test_toggle_task_response_has_task_fields(client):
    token = _register_and_get_token(client, "toggle6d@example.com")
    task_id = client.post(_TASKS_URL, json={"title": "Fields check"}, headers=_auth_headers(token)).json()["id"]
    resp = client.patch(_toggle_url(task_id), headers=_auth_headers(token))
    body = resp.json()
    assert "id" in body
    assert "title" in body
    assert "completed" in body
    assert "userId" in body


# ---------------------------------------------------------------------------
# PATCH /api/v1/tasks/{task_id}/toggle — authorization and not found
# ---------------------------------------------------------------------------

def test_toggle_task_403_when_not_owner(client):
    token_owner = _register_and_get_token(client, "toggle6_owner@example.com")
    token_other = _register_and_get_token(client, "toggle6_other@example.com")
    task_id = client.post(
        _TASKS_URL, json={"title": "Owner toggle"}, headers=_auth_headers(token_owner)
    ).json()["id"]
    resp = client.patch(_toggle_url(task_id), headers=_auth_headers(token_other))
    assert resp.status_code == 403


def test_toggle_task_404_when_not_found(client):
    token = _register_and_get_token(client, "toggle6_notfound@example.com")
    resp = client.patch(_toggle_url(str(uuid.uuid4())), headers=_auth_headers(token))
    assert resp.status_code == 404


def test_toggle_task_401_without_token(client):
    resp = client.patch(_toggle_url(str(uuid.uuid4())))
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /api/v1/tasks/{task_id} — success
# ---------------------------------------------------------------------------

def test_delete_task_returns_200(client):
    token = _register_and_get_token(client, "delete6@example.com")
    task_id = client.post(_TASKS_URL, json={"title": "To delete"}, headers=_auth_headers(token)).json()["id"]
    resp = client.delete(_task_url(task_id), headers=_auth_headers(token))
    assert resp.status_code == 200


def test_delete_task_response_has_message(client):
    token = _register_and_get_token(client, "delete6b@example.com")
    task_id = client.post(_TASKS_URL, json={"title": "Delete me"}, headers=_auth_headers(token)).json()["id"]
    resp = client.delete(_task_url(task_id), headers=_auth_headers(token))
    body = resp.json()
    assert "message" in body
    assert isinstance(body["message"], str)


def test_delete_task_removes_task_from_list(client):
    token = _register_and_get_token(client, "delete6c@example.com")
    task_id = client.post(_TASKS_URL, json={"title": "Gone task"}, headers=_auth_headers(token)).json()["id"]
    client.delete(_task_url(task_id), headers=_auth_headers(token))
    resp = client.get(_TASKS_URL, headers=_auth_headers(token))
    ids = [t["id"] for t in resp.json()["tasks"]]
    assert task_id not in ids


# ---------------------------------------------------------------------------
# DELETE /api/v1/tasks/{task_id} — authorization and not found
# ---------------------------------------------------------------------------

def test_delete_task_403_when_not_owner(client):
    token_owner = _register_and_get_token(client, "delete6_owner@example.com")
    token_other = _register_and_get_token(client, "delete6_other@example.com")
    task_id = client.post(
        _TASKS_URL, json={"title": "Owner's item"}, headers=_auth_headers(token_owner)
    ).json()["id"]
    resp = client.delete(_task_url(task_id), headers=_auth_headers(token_other))
    assert resp.status_code == 403


def test_delete_task_404_when_not_found(client):
    token = _register_and_get_token(client, "delete6_notfound@example.com")
    resp = client.delete(_task_url(str(uuid.uuid4())), headers=_auth_headers(token))
    assert resp.status_code == 404


def test_delete_task_401_without_token(client):
    resp = client.delete(_task_url(str(uuid.uuid4())))
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# UUID format validation for task_id
# ---------------------------------------------------------------------------

def test_put_task_422_for_non_uuid_task_id(client):
    token = _register_and_get_token(client, "uuid_put6@example.com")
    resp = client.put(_task_url("not-a-uuid"), json={"title": "x"}, headers=_auth_headers(token))
    assert resp.status_code == 422


def test_patch_toggle_422_for_non_uuid_task_id(client):
    token = _register_and_get_token(client, "uuid_patch6@example.com")
    resp = client.patch(_toggle_url("not-a-uuid"), headers=_auth_headers(token))
    assert resp.status_code == 422


def test_delete_task_422_for_non_uuid_task_id(client):
    token = _register_and_get_token(client, "uuid_delete6@example.com")
    resp = client.delete(_task_url("not-a-uuid"), headers=_auth_headers(token))
    assert resp.status_code == 422
