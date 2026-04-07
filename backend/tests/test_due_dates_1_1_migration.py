"""
Tests for task 1.1: Alembic migration 002_add_due_date.

Covers:
- After upgrade head: tasks table has due_date DATETIME NULL column
- After upgrade head: ix_tasks_userId_due_date index exists
- After downgrade: due_date column is removed
- After downgrade: ix_tasks_userId_due_date index is removed
"""
import pytest
from sqlalchemy import create_engine, inspect, text
from alembic.config import Config
from alembic import command
import os


def _get_alembic_cfg(db_url: str) -> Config:
    """Return an Alembic Config pointed at the backend alembic directory."""
    backend_dir = os.path.join(os.path.dirname(__file__), "..")
    cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


@pytest.fixture
def migration_engine(tmp_path):
    """Create a fresh SQLite database in a temp file for migration tests."""
    db_file = tmp_path / "test_migration.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    yield engine, db_url
    engine.dispose()


def test_migration_002_adds_due_date_column(migration_engine):
    """After alembic upgrade head, tasks.due_date column must exist."""
    engine, db_url = migration_engine
    cfg = _get_alembic_cfg(db_url)
    command.upgrade(cfg, "head")

    inspector = inspect(engine)
    columns = {col["name"]: col for col in inspector.get_columns("tasks")}

    assert "due_date" in columns, "due_date column not found after upgrade"
    assert columns["due_date"]["nullable"] is True, "due_date must be nullable"


def test_migration_002_due_date_column_is_datetime(migration_engine):
    """due_date column should be of DATETIME type (or compatible)."""
    engine, db_url = migration_engine
    cfg = _get_alembic_cfg(db_url)
    command.upgrade(cfg, "head")

    inspector = inspect(engine)
    columns = {col["name"]: col for col in inspector.get_columns("tasks")}

    assert "due_date" in columns
    col_type = str(columns["due_date"]["type"]).upper()
    assert "DATETIME" in col_type or "DATE" in col_type, (
        f"Expected DATETIME type, got: {col_type}"
    )


def test_migration_002_adds_ix_tasks_userid_due_date_index(migration_engine):
    """After upgrade head, ix_tasks_userId_due_date index must exist on tasks."""
    engine, db_url = migration_engine
    cfg = _get_alembic_cfg(db_url)
    command.upgrade(cfg, "head")

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("tasks")}

    assert "ix_tasks_userId_due_date" in indexes, (
        f"ix_tasks_userId_due_date index not found. Found: {indexes}"
    )


def test_migration_002_downgrade_removes_due_date_column(migration_engine):
    """After downgrade -1 from head, due_date column must be absent."""
    engine, db_url = migration_engine
    cfg = _get_alembic_cfg(db_url)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "-1")

    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("tasks")}

    assert "due_date" not in columns, (
        "due_date column should be removed after downgrade"
    )


def test_migration_002_downgrade_removes_index(migration_engine):
    """After downgrade -1 from head, ix_tasks_userId_due_date index must be absent."""
    engine, db_url = migration_engine
    cfg = _get_alembic_cfg(db_url)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "-1")

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("tasks")}

    assert "ix_tasks_userId_due_date" not in indexes, (
        "ix_tasks_userId_due_date index should be removed after downgrade"
    )


def test_migration_002_existing_rows_get_null_due_date(migration_engine):
    """Existing tasks rows must have due_date=NULL after migration (no default)."""
    engine, db_url = migration_engine
    cfg = _get_alembic_cfg(db_url)

    # Upgrade only to 001 first, insert a task, then upgrade to 002
    command.upgrade(cfg, "001")

    with engine.connect() as conn:
        conn.execute(text(
            "INSERT INTO users (id, email, hashed_password) VALUES "
            "('u1', 'a@b.com', 'hash')"
        ))
        conn.execute(text(
            "INSERT INTO tasks (id, userId, title, completed) VALUES "
            "('t1', 'u1', 'Old task', 0)"
        ))
        conn.commit()

    command.upgrade(cfg, "002")

    with engine.connect() as conn:
        row = conn.execute(text("SELECT due_date FROM tasks WHERE id='t1'")).fetchone()
        assert row[0] is None, f"Expected NULL due_date for existing row, got: {row[0]}"
