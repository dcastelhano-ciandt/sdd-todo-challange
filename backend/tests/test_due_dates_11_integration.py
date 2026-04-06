"""
Backend integration tests for tasks 11.1–11.5: due date and sort feature.

Uses mock auth/service to test the full router+service+repository stack
without the bcrypt user registration issue.

Covers:
- 11.1: POST /api/v1/tasks with valid due_date → 201 with due_date; 422 on malformed
- 11.2: PUT /api/v1/tasks/{id} with due_date=null → response has due_date: null
- 11.3: GET /api/v1/tasks?sort_by=due_date&sort_dir=asc → earliest first, nulls last
- 11.4: GET /api/v1/tasks?sort_by=due_date&sort_dir=desc → latest first, nulls last
- 11.5: GET /api/v1/tasks?sort_by=unknown → 422 response
"""
import uuid
import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models.base import Base
import app.models  # noqa: F401


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
    from app.dependencies import get_current_user, UserContext, get_db

    def override_auth():
        return UserContext(user_id="integration-user", jti="mock-jti")

    def override_get_db():
        session = Session(test_engine)
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_current_user] = override_auth
    app.dependency_overrides[get_db] = override_get_db

    # Also insert the mock user into the DB so FK constraints pass
    session = Session(test_engine)
    from app.models.user import User
    if not session.get(User, "integration-user"):
        session.add(User(
            id="integration-user",
            email="integration@test.com",
            hashed_password="$2b$12$FAKEHASHEDFORTHITEST0000000000000000",
        ))
        session.commit()
    session.close()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


_TASKS_URL = "/api/v1/tasks"


def _task_url(task_id: str) -> str:
    return f"{_TASKS_URL}/{task_id}"


# ---------------------------------------------------------------------------
# 11.1 — POST /api/v1/tasks with valid due_date
# ---------------------------------------------------------------------------

def test_11_1_create_task_with_valid_due_date_returns_201(client):
    resp = client.post(_TASKS_URL, json={"title": "Task with date", "due_date": "2026-08-15"})
    assert resp.status_code == 201


def test_11_1_create_task_response_includes_due_date(client):
    resp = client.post(_TASKS_URL, json={"title": "Dated task", "due_date": "2026-09-01"})
    assert resp.status_code == 201
    body = resp.json()
    assert "due_date" in body
    assert body["due_date"] == "2026-09-01"


def test_11_1_create_task_with_malformed_date_returns_422(client):
    resp = client.post(_TASKS_URL, json={"title": "Bad date", "due_date": "not-a-date"})
    assert resp.status_code == 422


def test_11_1_create_task_without_due_date_has_null_in_response(client):
    resp = client.post(_TASKS_URL, json={"title": "No date"})
    assert resp.status_code == 201
    assert resp.json()["due_date"] is None


# ---------------------------------------------------------------------------
# 11.2 — PUT /api/v1/tasks/{id} with due_date=null → response has due_date: null
# ---------------------------------------------------------------------------

def test_11_2_update_task_with_null_clears_due_date(client):
    # Create with a due date first
    create_resp = client.post(
        _TASKS_URL, json={"title": "Has date", "due_date": "2026-06-01"}
    )
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    # Update with null to clear
    update_resp = client.put(
        _task_url(task_id),
        json={"title": "No date now", "due_date": None},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["due_date"] is None


def test_11_2_update_task_with_new_due_date(client):
    create_resp = client.post(_TASKS_URL, json={"title": "Update date test"})
    task_id = create_resp.json()["id"]

    update_resp = client.put(
        _task_url(task_id),
        json={"title": "Updated", "due_date": "2026-12-31"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["due_date"] == "2026-12-31"


# ---------------------------------------------------------------------------
# 11.3 — GET /api/v1/tasks?sort_by=due_date&sort_dir=asc → earliest first, nulls last
# ---------------------------------------------------------------------------

def test_11_3_sort_by_due_date_asc_earliest_first(client, test_engine):
    """Create 3 tasks with specific due dates and verify ordering."""
    # Use a fresh user for isolation
    user_id = "sort-test-user-asc"
    from app.models.user import User
    from app.dependencies import get_current_user, UserContext, get_db
    from app.main import app

    session = Session(test_engine)
    if not session.get(User, user_id):
        session.add(User(id=user_id, email="sort_asc@test.com", hashed_password="hash"))
        session.commit()
    session.close()

    def override_auth_asc():
        return UserContext(user_id=user_id, jti="mock")
    def override_db():
        s = Session(test_engine)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_current_user] = override_auth_asc
    app.dependency_overrides[get_db] = override_db

    with TestClient(app) as c:
        c.post(_TASKS_URL, json={"title": "Late", "due_date": "2026-12-01"})
        c.post(_TASKS_URL, json={"title": "Early", "due_date": "2026-03-01"})
        c.post(_TASKS_URL, json={"title": "No date"})

        resp = c.get(f"{_TASKS_URL}?sort_by=due_date&sort_dir=asc")

    app.dependency_overrides[get_current_user] = lambda: UserContext(user_id="integration-user", jti="mock-jti")
    app.dependency_overrides[get_db] = override_db

    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    titled = [t["title"] for t in tasks]
    assert titled.index("Early") < titled.index("Late")
    assert titled.index("Late") < titled.index("No date")


# ---------------------------------------------------------------------------
# 11.4 — GET /api/v1/tasks?sort_by=due_date&sort_dir=desc → latest first, nulls last
# ---------------------------------------------------------------------------

def test_11_4_sort_by_due_date_desc_latest_first(client, test_engine):
    """Verify DESC ordering: latest due date first, NULL last."""
    user_id = "sort-test-user-desc"
    from app.models.user import User
    from app.dependencies import get_current_user, UserContext, get_db
    from app.main import app

    session = Session(test_engine)
    if not session.get(User, user_id):
        session.add(User(id=user_id, email="sort_desc@test.com", hashed_password="hash"))
        session.commit()
    session.close()

    def override_auth_desc():
        return UserContext(user_id=user_id, jti="mock")
    def override_db():
        s = Session(test_engine)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_current_user] = override_auth_desc
    app.dependency_overrides[get_db] = override_db

    with TestClient(app) as c:
        c.post(_TASKS_URL, json={"title": "Early", "due_date": "2026-03-01"})
        c.post(_TASKS_URL, json={"title": "Late", "due_date": "2026-12-01"})
        c.post(_TASKS_URL, json={"title": "No date"})

        resp = c.get(f"{_TASKS_URL}?sort_by=due_date&sort_dir=desc")

    app.dependency_overrides[get_current_user] = lambda: UserContext(user_id="integration-user", jti="mock-jti")
    app.dependency_overrides[get_db] = override_db

    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    titled = [t["title"] for t in tasks]
    assert titled.index("Late") < titled.index("Early")
    assert titled.index("Early") < titled.index("No date")


# ---------------------------------------------------------------------------
# 11.5 — GET /api/v1/tasks?sort_by=unknown → 422 response
# ---------------------------------------------------------------------------

def test_11_5_sort_by_unknown_returns_422(client):
    resp = client.get(f"{_TASKS_URL}?sort_by=unknown_column")
    assert resp.status_code == 422


def test_11_5_sort_dir_unknown_returns_422(client):
    resp = client.get(f"{_TASKS_URL}?sort_by=due_date&sort_dir=random")
    assert resp.status_code == 422
