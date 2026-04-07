"""
Tests for task 12.3: Backend integration tests against an in-memory SQLite database.

Covers:
- Full register → login → create task → list tasks flow through the HTTP API
- Cross-user task ownership: create task as user A, attempt update and delete as
  user B — expect 403
- Token expiry: issue a token with zero TTL (exp in the past), make an authenticated
  request — expect 401
- Alembic migration: run upgrade head against an empty database and verify all three
  tables exist with the correct columns

Requirements: 1.1, 1.5, 2.1, 2.3, 3.1, 4.1, 5.2, 7.2, 12.1, 12.2, 12.3, 12.4
"""
import uuid
import pytest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.models.base import Base
import app.models  # noqa: F401 — registers all ORM models


# ---------------------------------------------------------------------------
# Shared in-memory database and TestClient
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_engine():
    """A single in-memory SQLite engine shared across all tests in this module."""
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
    """FastAPI TestClient wired to the in-memory database via dependency override."""
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
# Helpers
# ---------------------------------------------------------------------------

_REGISTER_URL = "/api/v1/auth/register"
_LOGIN_URL = "/api/v1/auth/login"
_LOGOUT_URL = "/api/v1/auth/logout"
_TASKS_URL = "/api/v1/tasks"


def _register(client, email, password="password12"):
    resp = client.post(_REGISTER_URL, json={"email": email, "password": password})
    assert resp.status_code == 201, resp.json()
    return resp.json()["access_token"]


def _login(client, email, password="password12"):
    resp = client.post(_LOGIN_URL, json={"email": email, "password": password})
    assert resp.status_code == 200, resp.json()
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Full register → login → create task → list tasks flow
# ---------------------------------------------------------------------------

def test_full_flow_register_returns_201_and_token(client):
    resp = client.post(
        _REGISTER_URL, json={"email": "flow12a@example.com", "password": "password12"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_full_flow_login_with_registered_credentials_returns_200(client):
    client.post(_REGISTER_URL, json={"email": "flow12b@example.com", "password": "password12"})
    resp = client.post(_LOGIN_URL, json={"email": "flow12b@example.com", "password": "password12"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_full_flow_create_task_returns_201_with_task_fields(client):
    token = _register(client, "flow12c@example.com")
    resp = client.post(
        _TASKS_URL,
        json={"title": "Integration task"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    assert body["title"] == "Integration task"
    assert body["completed"] is False
    assert "userId" in body


def test_full_flow_list_tasks_returns_created_task(client):
    token = _register(client, "flow12d@example.com")

    # Create two tasks
    client.post(_TASKS_URL, json={"title": "Task One"}, headers=_auth_headers(token))
    client.post(_TASKS_URL, json={"title": "Task Two"}, headers=_auth_headers(token))

    resp = client.get(_TASKS_URL, headers=_auth_headers(token))
    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "Task One" in titles
    assert "Task Two" in titles


def test_full_flow_list_tasks_only_returns_own_tasks(client):
    """A user must only see their own tasks — not those of other users."""
    token_a = _register(client, "flow12e_a@example.com")
    token_b = _register(client, "flow12e_b@example.com")

    client.post(_TASKS_URL, json={"title": "A's task"}, headers=_auth_headers(token_a))
    client.post(_TASKS_URL, json={"title": "B's task"}, headers=_auth_headers(token_b))

    resp = client.get(_TASKS_URL, headers=_auth_headers(token_a))
    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "A's task" in titles
    # B's task must NOT appear in A's list
    assert "B's task" not in titles


def test_full_flow_register_then_login_then_create_then_list_end_to_end(client):
    """Complete round-trip: register, login with that token, create a task, list it."""
    email = "e2e12@example.com"
    reg_token = _register(client, email)

    # Login should also work and give a valid token
    login_token = _login(client, email)

    # Create a task with the login token
    create_resp = client.post(
        _TASKS_URL,
        json={"title": "E2E task"},
        headers=_auth_headers(login_token),
    )
    assert create_resp.status_code == 201
    created_id = create_resp.json()["id"]

    # List should include the created task
    list_resp = client.get(_TASKS_URL, headers=_auth_headers(login_token))
    assert list_resp.status_code == 200
    ids = [t["id"] for t in list_resp.json()["tasks"]]
    assert created_id in ids


# ---------------------------------------------------------------------------
# Cross-user task ownership: create as user A, attempt update/delete as user B
# ---------------------------------------------------------------------------

def test_cross_user_update_returns_403(client):
    token_a = _register(client, "cross12a@example.com")
    token_b = _register(client, "cross12b@example.com")

    create_resp = client.post(
        _TASKS_URL, json={"title": "A's protected task"}, headers=_auth_headers(token_a)
    )
    task_id = create_resp.json()["id"]

    # User B attempts to update user A's task
    resp = client.put(
        f"{_TASKS_URL}/{task_id}",
        json={"title": "Hijacked"},
        headers=_auth_headers(token_b),
    )
    assert resp.status_code == 403


def test_cross_user_update_does_not_modify_task(client):
    """Task title must be unchanged after the forbidden update."""
    token_a = _register(client, "cross12c@example.com")
    token_b = _register(client, "cross12d@example.com")

    create_resp = client.post(
        _TASKS_URL, json={"title": "Original title"}, headers=_auth_headers(token_a)
    )
    task_id = create_resp.json()["id"]

    client.put(
        f"{_TASKS_URL}/{task_id}",
        json={"title": "Hijacked"},
        headers=_auth_headers(token_b),
    )

    # Verify title still unchanged using user A's token
    list_resp = client.get(_TASKS_URL, headers=_auth_headers(token_a))
    tasks = {t["id"]: t for t in list_resp.json()["tasks"]}
    assert tasks[task_id]["title"] == "Original title"


def test_cross_user_delete_returns_403(client):
    token_a = _register(client, "cross12e@example.com")
    token_b = _register(client, "cross12f@example.com")

    create_resp = client.post(
        _TASKS_URL, json={"title": "A's deletable task"}, headers=_auth_headers(token_a)
    )
    task_id = create_resp.json()["id"]

    # User B attempts to delete user A's task
    resp = client.delete(
        f"{_TASKS_URL}/{task_id}",
        headers=_auth_headers(token_b),
    )
    assert resp.status_code == 403


def test_cross_user_delete_does_not_remove_task(client):
    """Task must still exist after a forbidden delete attempt."""
    token_a = _register(client, "cross12g@example.com")
    token_b = _register(client, "cross12h@example.com")

    create_resp = client.post(
        _TASKS_URL, json={"title": "Should survive"}, headers=_auth_headers(token_a)
    )
    task_id = create_resp.json()["id"]

    client.delete(f"{_TASKS_URL}/{task_id}", headers=_auth_headers(token_b))

    # Verify task still accessible by user A
    list_resp = client.get(_TASKS_URL, headers=_auth_headers(token_a))
    ids = [t["id"] for t in list_resp.json()["tasks"]]
    assert task_id in ids


# ---------------------------------------------------------------------------
# Token expiry: issue a token with exp in the past → 401 on authenticated request
# ---------------------------------------------------------------------------

def test_expired_token_on_create_task_returns_401(client):
    """A token with exp already in the past must be rejected with 401."""
    from jose import jwt as jose_jwt
    from app.core.config import settings

    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(uuid.uuid4()),
        "exp": now - timedelta(seconds=1),  # already expired
        "iat": now - timedelta(minutes=30),
        "jti": str(uuid.uuid4()),
    }
    expired_token = jose_jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")

    resp = client.post(
        _TASKS_URL,
        json={"title": "Should be rejected"},
        headers=_auth_headers(expired_token),
    )
    assert resp.status_code == 401


def test_expired_token_on_list_tasks_returns_401(client):
    from jose import jwt as jose_jwt
    from app.core.config import settings

    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(uuid.uuid4()),
        "exp": now - timedelta(seconds=10),
        "iat": now - timedelta(minutes=31),
        "jti": str(uuid.uuid4()),
    }
    expired_token = jose_jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")

    resp = client.get(_TASKS_URL, headers=_auth_headers(expired_token))
    assert resp.status_code == 401


def test_zero_ttl_token_returns_401(client):
    """A token issued with zero TTL (exp <= now) must be rejected."""
    from jose import jwt as jose_jwt
    from app.core.config import settings

    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(uuid.uuid4()),
        "exp": now - timedelta(seconds=1),
        "iat": now,
        "jti": str(uuid.uuid4()),
    }
    zero_ttl_token = jose_jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")

    resp = client.post(
        _TASKS_URL,
        json={"title": "Blocked"},
        headers=_auth_headers(zero_ttl_token),
    )
    assert resp.status_code == 401


def test_blacklisted_token_after_logout_returns_401(client):
    """After logout, the same token must be rejected on subsequent requests."""
    token = _register(client, "expiry12x@example.com")

    # Logout (blacklists jti)
    logout_resp = client.post(_LOGOUT_URL, headers=_auth_headers(token))
    assert logout_resp.status_code == 200

    # Any subsequent authenticated request must return 401
    resp = client.get(_TASKS_URL, headers=_auth_headers(token))
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Alembic migration: upgrade head → verify tables and columns exist
# ---------------------------------------------------------------------------

def test_alembic_upgrade_head_creates_users_table():
    """Running alembic upgrade head on an empty DB must create the users table."""
    import os
    import sys
    from alembic.config import Config
    from alembic import command

    # Create a fresh empty in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Build Alembic config pointing to the backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), "..")
    alembic_ini = os.path.join(backend_dir, "alembic.ini")
    cfg = Config(alembic_ini)
    cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))

    # Inject the engine connection so Alembic uses our in-memory DB
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection

        # Patch env.py to use the provided connection
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory

        script = ScriptDirectory.from_config(cfg)

        def run_upgrade(rev, context):
            return script._upgrade_revs("head", rev)

        migration_ctx = MigrationContext.configure(
            connection,
            opts={"target_metadata": Base.metadata},
        )
        # Run via alembic command with DATABASE_URL override
        cfg.set_main_option("sqlalchemy.url", "sqlite://")

    # Alternatively: apply migrations by running upgrade directly via env DATABASE_URL
    # Use the direct approach: set DATABASE_URL env and call alembic upgrade
    import tempfile

    # Create a temp file database so we don't need to handle in-memory connection sharing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        tmp_url = f"sqlite:///{tmp_path}"
        os.environ["DATABASE_URL"] = tmp_url

        cfg2 = Config(alembic_ini)
        cfg2.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
        cfg2.set_main_option("sqlalchemy.url", tmp_url)

        command.upgrade(cfg2, "head")

        # Inspect the resulting schema
        tmp_engine = create_engine(tmp_url)
        inspector = inspect(tmp_engine)
        table_names = inspector.get_table_names()

        assert "users" in table_names, f"users table missing; got: {table_names}"
    finally:
        del os.environ["DATABASE_URL"]
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def test_alembic_upgrade_head_creates_tasks_table():
    """Running alembic upgrade head must create the tasks table."""
    import os
    import tempfile

    from alembic.config import Config
    from alembic import command

    backend_dir = os.path.join(os.path.dirname(__file__), "..")
    alembic_ini = os.path.join(backend_dir, "alembic.ini")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        tmp_url = f"sqlite:///{tmp_path}"
        os.environ["DATABASE_URL"] = tmp_url

        cfg = Config(alembic_ini)
        cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
        cfg.set_main_option("sqlalchemy.url", tmp_url)

        command.upgrade(cfg, "head")

        tmp_engine = create_engine(tmp_url)
        inspector = inspect(tmp_engine)
        table_names = inspector.get_table_names()

        assert "tasks" in table_names, f"tasks table missing; got: {table_names}"
    finally:
        del os.environ["DATABASE_URL"]
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def test_alembic_upgrade_head_creates_token_blacklist_table():
    """Running alembic upgrade head must create the token_blacklist table."""
    import os
    import tempfile

    from alembic.config import Config
    from alembic import command

    backend_dir = os.path.join(os.path.dirname(__file__), "..")
    alembic_ini = os.path.join(backend_dir, "alembic.ini")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        tmp_url = f"sqlite:///{tmp_path}"
        os.environ["DATABASE_URL"] = tmp_url

        cfg = Config(alembic_ini)
        cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
        cfg.set_main_option("sqlalchemy.url", tmp_url)

        command.upgrade(cfg, "head")

        tmp_engine = create_engine(tmp_url)
        inspector = inspect(tmp_engine)
        table_names = inspector.get_table_names()

        assert "token_blacklist" in table_names, f"token_blacklist missing; got: {table_names}"
    finally:
        del os.environ["DATABASE_URL"]
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def test_alembic_migration_users_table_has_correct_columns():
    """users table must have columns: id, email, hashed_password."""
    import os
    import tempfile

    from alembic.config import Config
    from alembic import command

    backend_dir = os.path.join(os.path.dirname(__file__), "..")
    alembic_ini = os.path.join(backend_dir, "alembic.ini")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        tmp_url = f"sqlite:///{tmp_path}"
        os.environ["DATABASE_URL"] = tmp_url

        cfg = Config(alembic_ini)
        cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
        cfg.set_main_option("sqlalchemy.url", tmp_url)

        command.upgrade(cfg, "head")

        tmp_engine = create_engine(tmp_url)
        inspector = inspect(tmp_engine)
        columns = {col["name"] for col in inspector.get_columns("users")}

        assert "id" in columns
        assert "email" in columns
        assert "hashed_password" in columns
    finally:
        del os.environ["DATABASE_URL"]
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def test_alembic_migration_tasks_table_has_correct_columns():
    """tasks table must have columns: id, userId, title, completed, created_at."""
    import os
    import tempfile

    from alembic.config import Config
    from alembic import command

    backend_dir = os.path.join(os.path.dirname(__file__), "..")
    alembic_ini = os.path.join(backend_dir, "alembic.ini")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        tmp_url = f"sqlite:///{tmp_path}"
        os.environ["DATABASE_URL"] = tmp_url

        cfg = Config(alembic_ini)
        cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
        cfg.set_main_option("sqlalchemy.url", tmp_url)

        command.upgrade(cfg, "head")

        tmp_engine = create_engine(tmp_url)
        inspector = inspect(tmp_engine)
        columns = {col["name"] for col in inspector.get_columns("tasks")}

        assert "id" in columns
        assert "userId" in columns
        assert "title" in columns
        assert "completed" in columns
        assert "created_at" in columns
    finally:
        del os.environ["DATABASE_URL"]
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def test_alembic_migration_token_blacklist_table_has_correct_columns():
    """token_blacklist table must have columns: jti, expires_at."""
    import os
    import tempfile

    from alembic.config import Config
    from alembic import command

    backend_dir = os.path.join(os.path.dirname(__file__), "..")
    alembic_ini = os.path.join(backend_dir, "alembic.ini")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        tmp_url = f"sqlite:///{tmp_path}"
        os.environ["DATABASE_URL"] = tmp_url

        cfg = Config(alembic_ini)
        cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
        cfg.set_main_option("sqlalchemy.url", tmp_url)

        command.upgrade(cfg, "head")

        tmp_engine = create_engine(tmp_url)
        inspector = inspect(tmp_engine)
        columns = {col["name"] for col in inspector.get_columns("token_blacklist")}

        assert "jti" in columns
        assert "expires_at" in columns
    finally:
        del os.environ["DATABASE_URL"]
        try:
            os.remove(tmp_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Task 7.1: Search endpoint integration tests
# Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
# ---------------------------------------------------------------------------

def test_search_q_returns_matching_tasks_case_insensitive(client):
    """GET /api/v1/tasks?q=<keyword> returns only tasks whose title contains the keyword,
    and the match is case-insensitive (uppercase query finds lowercase title)."""
    token = _register(client, "search71a@example.com")
    client.post(_TASKS_URL, json={"title": "buy groceries"}, headers=_auth_headers(token))
    client.post(_TASKS_URL, json={"title": "write report"}, headers=_auth_headers(token))

    # lowercase query
    resp_lower = client.get(f"{_TASKS_URL}?q=buy", headers=_auth_headers(token))
    assert resp_lower.status_code == 200
    titles_lower = [t["title"] for t in resp_lower.json()["tasks"]]
    assert "buy groceries" in titles_lower
    assert "write report" not in titles_lower

    # UPPERCASE query — must return the same result (case-insensitive)
    resp_upper = client.get(f"{_TASKS_URL}?q=BUY", headers=_auth_headers(token))
    assert resp_upper.status_code == 200
    titles_upper = [t["title"] for t in resp_upper.json()["tasks"]]
    assert titles_upper == titles_lower


def test_search_q_with_status_applies_both_filters(client):
    """GET /api/v1/tasks?q=<keyword>&status=pending returns only pending tasks
    that also match the keyword."""
    token = _register(client, "search71b@example.com")

    r_pending = client.post(
        _TASKS_URL, json={"title": "buy bread (pending)"}, headers=_auth_headers(token)
    )
    r_done = client.post(
        _TASKS_URL, json={"title": "buy milk (done)"}, headers=_auth_headers(token)
    )
    # Toggle r_done → completed
    client.patch(
        f"{_TASKS_URL}/{r_done.json()['id']}/toggle", headers=_auth_headers(token)
    )
    client.post(
        _TASKS_URL, json={"title": "unrelated pending task"}, headers=_auth_headers(token)
    )

    resp = client.get(
        f"{_TASKS_URL}?q=buy&status=pending", headers=_auth_headers(token)
    )
    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "buy bread (pending)" in titles
    assert "buy milk (done)" not in titles
    assert "unrelated pending task" not in titles


def test_search_q_no_match_returns_200_empty_list(client):
    """GET /api/v1/tasks?q=nomatch returns HTTP 200 with an empty tasks list
    when no tasks match the keyword."""
    token = _register(client, "search71c@example.com")
    client.post(_TASKS_URL, json={"title": "Buy apples"}, headers=_auth_headers(token))

    resp = client.get(
        f"{_TASKS_URL}?q=xyzzy_no_match_at_all_123", headers=_auth_headers(token)
    )
    assert resp.status_code == 200
    assert resp.json()["tasks"] == []


def test_search_q_empty_string_returns_all_tasks(client):
    """GET /api/v1/tasks?q= (empty string) returns all tasks for the user,
    identical to calling without any q parameter."""
    token = _register(client, "search71d@example.com")
    client.post(_TASKS_URL, json={"title": "Task Alpha"}, headers=_auth_headers(token))
    client.post(_TASKS_URL, json={"title": "Task Beta"}, headers=_auth_headers(token))

    resp_no_q = client.get(_TASKS_URL, headers=_auth_headers(token))
    resp_empty_q = client.get(f"{_TASKS_URL}?q=", headers=_auth_headers(token))

    assert resp_no_q.status_code == 200
    assert resp_empty_q.status_code == 200

    titles_no_q = sorted(t["title"] for t in resp_no_q.json()["tasks"])
    titles_empty_q = sorted(t["title"] for t in resp_empty_q.json()["tasks"])
    assert titles_no_q == titles_empty_q


def test_search_q_results_scoped_to_authenticated_user(client):
    """GET /api/v1/tasks?q=<keyword> never returns matching tasks owned by another user."""
    token_a = _register(client, "search71e_a@example.com")
    token_b = _register(client, "search71e_b@example.com")

    client.post(
        _TASKS_URL, json={"title": "shared keyword userA"}, headers=_auth_headers(token_a)
    )
    client.post(
        _TASKS_URL, json={"title": "shared keyword userB"}, headers=_auth_headers(token_b)
    )

    resp = client.get(f"{_TASKS_URL}?q=shared+keyword", headers=_auth_headers(token_a))
    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    titles = [t["title"] for t in tasks]
    assert "shared keyword userA" in titles
    assert "shared keyword userB" not in titles
