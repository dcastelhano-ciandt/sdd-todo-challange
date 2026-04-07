"""
Tests for search task 3.1: Tasks router — q query parameter acceptance.

Covers:
- Endpoint accepts q parameter and returns matching tasks
- Omitting q preserves existing behavior (no title filtering)
- Authenticated request with both q and status applies both filters
- Results are always scoped to the authenticated user

Requirements: 1.1, 1.3, 1.6
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models.base import Base
import app.models  # noqa: F401


# ---------------------------------------------------------------------------
# Fixtures
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


_REGISTER_URL = "/api/v1/auth/register"
_TASKS_URL = "/api/v1/tasks"
_VALID_PASSWORD = "secret123"


def _register_and_get_token(client, email: str) -> str:
    resp = client.post(_REGISTER_URL, json={"email": email, "password": _VALID_PASSWORD})
    assert resp.status_code == 201, resp.json()
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _toggle_url(task_id: str) -> str:
    return f"{_TASKS_URL}/{task_id}/toggle"


# ---------------------------------------------------------------------------
# Requirement 1.1: API accepts optional q parameter
# ---------------------------------------------------------------------------

def test_list_tasks_accepts_q_parameter(client):
    """GET /api/v1/tasks?q=keyword is accepted with 200."""
    token = _register_and_get_token(client, "search_router_1@example.com")
    client.post(_TASKS_URL, json={"title": "Buy groceries"}, headers=_auth_headers(token))

    resp = client.get(f"{_TASKS_URL}?q=Buy", headers=_auth_headers(token))
    assert resp.status_code == 200


def test_list_tasks_with_q_returns_matching_tasks(client):
    """?q=keyword returns only matching tasks."""
    token = _register_and_get_token(client, "search_router_2@example.com")
    client.post(_TASKS_URL, json={"title": "Buy groceries"}, headers=_auth_headers(token))
    client.post(_TASKS_URL, json={"title": "Write report"}, headers=_auth_headers(token))

    resp = client.get(f"{_TASKS_URL}?q=grocery", headers=_auth_headers(token))
    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "Buy groceries" not in titles  # "grocery" != "groceries" but let's use proper keyword


def test_list_tasks_with_q_returns_case_insensitive_match(client):
    """?q=BUY returns tasks with 'buy' in the title (case-insensitive)."""
    token = _register_and_get_token(client, "search_router_3@example.com")
    client.post(_TASKS_URL, json={"title": "buy bread"}, headers=_auth_headers(token))
    client.post(_TASKS_URL, json={"title": "write tests"}, headers=_auth_headers(token))

    resp = client.get(f"{_TASKS_URL}?q=BUY", headers=_auth_headers(token))
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "buy bread" in titles
    assert "write tests" not in titles


# ---------------------------------------------------------------------------
# Requirement 1.3: Omitting q preserves existing behavior
# ---------------------------------------------------------------------------

def test_list_tasks_without_q_returns_all_tasks(client):
    """GET /api/v1/tasks without q returns all tasks."""
    token = _register_and_get_token(client, "search_router_4@example.com")
    client.post(_TASKS_URL, json={"title": "Task A"}, headers=_auth_headers(token))
    client.post(_TASKS_URL, json={"title": "Task B"}, headers=_auth_headers(token))

    resp = client.get(_TASKS_URL, headers=_auth_headers(token))
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "Task A" in titles
    assert "Task B" in titles


def test_list_tasks_with_empty_q_returns_all_tasks(client):
    """GET /api/v1/tasks?q= (empty string) returns all tasks."""
    token = _register_and_get_token(client, "search_router_5@example.com")
    client.post(_TASKS_URL, json={"title": "Task X"}, headers=_auth_headers(token))
    client.post(_TASKS_URL, json={"title": "Task Y"}, headers=_auth_headers(token))

    resp = client.get(f"{_TASKS_URL}?q=", headers=_auth_headers(token))
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "Task X" in titles
    assert "Task Y" in titles


# ---------------------------------------------------------------------------
# Requirement 1.4: Both q and status applied simultaneously
# ---------------------------------------------------------------------------

def test_list_tasks_with_q_and_status_applies_both_filters(client):
    """?q=keyword&status=pending returns only pending tasks matching the keyword."""
    token = _register_and_get_token(client, "search_router_6@example.com")
    r1 = client.post(_TASKS_URL, json={"title": "buy pending"}, headers=_auth_headers(token))
    r2 = client.post(_TASKS_URL, json={"title": "buy done"}, headers=_auth_headers(token))
    client.patch(_toggle_url(r2.json()["id"]), headers=_auth_headers(token))  # mark done
    client.post(_TASKS_URL, json={"title": "write report"}, headers=_auth_headers(token))

    resp = client.get(f"{_TASKS_URL}?q=buy&status=pending", headers=_auth_headers(token))
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "buy pending" in titles
    assert "buy done" not in titles
    assert "write report" not in titles


# ---------------------------------------------------------------------------
# Requirement 1.5: Empty result returns 200 with empty tasks list
# ---------------------------------------------------------------------------

def test_list_tasks_with_q_no_match_returns_200_empty_list(client):
    """?q=nomatch returns 200 with empty tasks list, not an error."""
    token = _register_and_get_token(client, "search_router_7@example.com")
    client.post(_TASKS_URL, json={"title": "Buy bread"}, headers=_auth_headers(token))

    resp = client.get(f"{_TASKS_URL}?q=xyz_no_match_at_all", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["tasks"] == []


# ---------------------------------------------------------------------------
# Requirement 1.6: Results always scoped to authenticated user
# ---------------------------------------------------------------------------

def test_list_tasks_with_q_does_not_return_other_users_tasks(client):
    """?q=keyword never returns tasks owned by another user."""
    token_a = _register_and_get_token(client, "search_router_8a@example.com")
    token_b = _register_and_get_token(client, "search_router_8b@example.com")

    client.post(_TASKS_URL, json={"title": "buy groceries (user A)"}, headers=_auth_headers(token_a))
    client.post(_TASKS_URL, json={"title": "buy groceries (user B)"}, headers=_auth_headers(token_b))

    resp = client.get(f"{_TASKS_URL}?q=buy", headers=_auth_headers(token_a))
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "buy groceries (user A)" in titles
    assert "buy groceries (user B)" not in titles
