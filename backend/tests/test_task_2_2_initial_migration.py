"""
Tests for Task 2.2: Write the initial migration script for all three tables.

Verifies:
- 001_initial_schema.py exists in backend/alembic/versions/.
- upgrade() creates users, tasks, and token_blacklist tables with correct columns.
- upgrade() creates the required indexes.
- downgrade() drops the three tables in reverse dependency order.
- Running alembic upgrade head against an in-memory SQLite database produces
  the correct schema (users, tasks, token_blacklist with all expected columns).
"""
import os
import sys
import sqlite3
import tempfile

import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSIONS_DIR = os.path.join(BACKEND_DIR, "alembic", "versions")


# ---------------------------------------------------------------------------
# Helper: build an Alembic config pointed at a specific DB file
# ---------------------------------------------------------------------------

def _make_alembic_cfg(db_url: str):
    """Return an Alembic Config object wired to the given SQLite URL."""
    import alembic.config

    cfg = alembic.config.Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


# ---------------------------------------------------------------------------
# Static / file-level tests
# ---------------------------------------------------------------------------

def test_initial_migration_file_exists():
    """001_initial_schema.py must exist inside alembic/versions/."""
    migration_path = os.path.join(VERSIONS_DIR, "001_initial_schema.py")
    assert os.path.isfile(migration_path), (
        "001_initial_schema.py not found in backend/alembic/versions/"
    )


def test_migration_has_upgrade_function():
    """001_initial_schema.py must define an upgrade() function."""
    migration_path = os.path.join(VERSIONS_DIR, "001_initial_schema.py")
    with open(migration_path) as f:
        content = f.read()
    assert "def upgrade()" in content, (
        "001_initial_schema.py must define an upgrade() function"
    )


def test_migration_has_downgrade_function():
    """001_initial_schema.py must define a downgrade() function."""
    migration_path = os.path.join(VERSIONS_DIR, "001_initial_schema.py")
    with open(migration_path) as f:
        content = f.read()
    assert "def downgrade()" in content, (
        "001_initial_schema.py must define a downgrade() function"
    )


def test_migration_creates_users_table():
    """upgrade() must create the users table."""
    migration_path = os.path.join(VERSIONS_DIR, "001_initial_schema.py")
    with open(migration_path) as f:
        content = f.read()
    assert "users" in content, (
        "001_initial_schema.py upgrade() must reference the 'users' table"
    )


def test_migration_creates_tasks_table():
    """upgrade() must create the tasks table."""
    migration_path = os.path.join(VERSIONS_DIR, "001_initial_schema.py")
    with open(migration_path) as f:
        content = f.read()
    assert "tasks" in content, (
        "001_initial_schema.py upgrade() must reference the 'tasks' table"
    )


def test_migration_creates_token_blacklist_table():
    """upgrade() must create the token_blacklist table."""
    migration_path = os.path.join(VERSIONS_DIR, "001_initial_schema.py")
    with open(migration_path) as f:
        content = f.read()
    assert "token_blacklist" in content, (
        "001_initial_schema.py upgrade() must reference the 'token_blacklist' table"
    )


def test_migration_references_indexes():
    """upgrade() must create indexes on tasks(userId) and token_blacklist(expires_at)."""
    migration_path = os.path.join(VERSIONS_DIR, "001_initial_schema.py")
    with open(migration_path) as f:
        content = f.read()
    assert "create_index" in content or "Index" in content, (
        "001_initial_schema.py must create indexes (create_index or op.create_index)"
    )


def test_migration_downgrade_drops_tables():
    """downgrade() must drop tables."""
    migration_path = os.path.join(VERSIONS_DIR, "001_initial_schema.py")
    with open(migration_path) as f:
        content = f.read()
    assert "drop_table" in content or "drop_index" in content, (
        "001_initial_schema.py downgrade() must drop tables"
    )


# ---------------------------------------------------------------------------
# Functional test helpers
# ---------------------------------------------------------------------------

def _get_table_info(conn: sqlite3.Connection, table_name: str):
    """Return list of (cid, name, type, notnull, dflt_value, pk) for a table."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()


def _get_tables(conn: sqlite3.Connection):
    """Return set of table names in the database (excluding alembic_version)."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return {row[0] for row in cursor.fetchall()}


def _get_indexes(conn: sqlite3.Connection, table_name: str):
    """Return list of index names for a given table."""
    cursor = conn.execute(f"PRAGMA index_list({table_name})")
    return [row[1] for row in cursor.fetchall()]


def _run_upgrade(db_path: str) -> None:
    """Run alembic upgrade head against the given SQLite file path."""
    import alembic.command

    db_url = f"sqlite:///{db_path}"
    cfg = _make_alembic_cfg(db_url)
    alembic.command.upgrade(cfg, "head")


# ---------------------------------------------------------------------------
# Functional test: run alembic upgrade head against a temp SQLite file
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def migrated_db():
    """
    Run alembic upgrade head against a temporary SQLite file and return a
    sqlite3 connection for schema inspection.

    The fixture restores any previously set DATABASE_URL on teardown to
    avoid cross-test contamination.
    """
    prior_db_url = os.environ.get("DATABASE_URL")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    db_url = f"sqlite:///{db_path}"
    os.environ["DATABASE_URL"] = db_url

    _run_upgrade(db_path)

    conn = sqlite3.connect(db_path)
    yield conn

    conn.close()
    try:
        os.unlink(db_path)
    except OSError:
        pass

    # Restore prior value (or remove key) so other tests are not affected.
    if prior_db_url is not None:
        os.environ["DATABASE_URL"] = prior_db_url
    else:
        os.environ.pop("DATABASE_URL", None)


def test_upgrade_creates_users_table(migrated_db):
    """After upgrade head, users table must exist."""
    tables = _get_tables(migrated_db)
    assert "users" in tables, f"users table not found. Tables: {tables}"


def test_upgrade_creates_tasks_table(migrated_db):
    """After upgrade head, tasks table must exist."""
    tables = _get_tables(migrated_db)
    assert "tasks" in tables, f"tasks table not found. Tables: {tables}"


def test_upgrade_creates_token_blacklist_table(migrated_db):
    """After upgrade head, token_blacklist table must exist."""
    tables = _get_tables(migrated_db)
    assert "token_blacklist" in tables, f"token_blacklist table not found. Tables: {tables}"


def test_users_table_columns(migrated_db):
    """users table must have id, email, hashed_password columns."""
    columns = {row[1] for row in _get_table_info(migrated_db, "users")}
    assert "id" in columns, "users.id column missing"
    assert "email" in columns, "users.email column missing"
    assert "hashed_password" in columns, "users.hashed_password column missing"


def test_tasks_table_columns(migrated_db):
    """tasks table must have id, userId, title, completed, created_at columns."""
    columns = {row[1] for row in _get_table_info(migrated_db, "tasks")}
    assert "id" in columns, "tasks.id column missing"
    assert "userId" in columns, "tasks.userId column missing"
    assert "title" in columns, "tasks.title column missing"
    assert "completed" in columns, "tasks.completed column missing"
    assert "created_at" in columns, "tasks.created_at column missing"


def test_token_blacklist_table_columns(migrated_db):
    """token_blacklist table must have jti and expires_at columns."""
    columns = {row[1] for row in _get_table_info(migrated_db, "token_blacklist")}
    assert "jti" in columns, "token_blacklist.jti column missing"
    assert "expires_at" in columns, "token_blacklist.expires_at column missing"


def test_tasks_userid_index_exists(migrated_db):
    """tasks table must have an index on userId."""
    indexes = _get_indexes(migrated_db, "tasks")
    userid_indexes = [idx for idx in indexes if "userid" in idx.lower() or "user" in idx.lower()]
    assert len(userid_indexes) >= 1, (
        f"No index on tasks(userId) found. Indexes: {indexes}"
    )


def test_token_blacklist_expires_at_index_exists(migrated_db):
    """token_blacklist table must have an index on expires_at."""
    indexes = _get_indexes(migrated_db, "token_blacklist")
    expires_indexes = [idx for idx in indexes if "expires" in idx.lower()]
    assert len(expires_indexes) >= 1, (
        f"No index on token_blacklist(expires_at) found. Indexes: {indexes}"
    )


def test_downgrade_removes_tables():
    """After downgrade -1, the three tables must be gone."""
    import alembic.command

    prior_db_url = os.environ.get("DATABASE_URL")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    db_url = f"sqlite:///{db_path}"
    os.environ["DATABASE_URL"] = db_url

    try:
        cfg = _make_alembic_cfg(db_url)
        # Apply then revert
        alembic.command.upgrade(cfg, "head")
        alembic.command.downgrade(cfg, "-1")

        conn = sqlite3.connect(db_path)
        tables = _get_tables(conn)
        conn.close()
    finally:
        try:
            os.unlink(db_path)
        except OSError:
            pass
        # Always restore prior DATABASE_URL value
        if prior_db_url is not None:
            os.environ["DATABASE_URL"] = prior_db_url
        else:
            os.environ.pop("DATABASE_URL", None)

    assert "users" not in tables, "users table should not exist after downgrade"
    assert "tasks" not in tables, "tasks table should not exist after downgrade"
    assert "token_blacklist" not in tables, "token_blacklist table should not exist after downgrade"
