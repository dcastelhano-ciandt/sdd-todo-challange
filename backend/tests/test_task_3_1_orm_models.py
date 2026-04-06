"""
Tests for task 3.1: SQLAlchemy ORM models and get_db dependency.

Covers:
- User ORM model with correct columns and constraints
- Task ORM model with correct columns, defaults, and FK cascade
- TokenBlacklist ORM model
- get_db dependency yields a Session and closes it
"""
import importlib
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_in_memory_engine():
    """Create an in-memory SQLite engine with all tables."""
    from app.models.base import Base
    # Import models to register them on Base.metadata
    import app.models.user  # noqa: F401
    import app.models.task  # noqa: F401
    import app.models.token_blacklist  # noqa: F401

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


# ---------------------------------------------------------------------------
# Module importability
# ---------------------------------------------------------------------------

def test_user_model_module_importable():
    mod = importlib.import_module("app.models.user")
    assert mod is not None


def test_task_model_module_importable():
    mod = importlib.import_module("app.models.task")
    assert mod is not None


def test_token_blacklist_model_module_importable():
    mod = importlib.import_module("app.models.token_blacklist")
    assert mod is not None


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------

def test_user_model_has_correct_tablename():
    from app.models.user import User
    assert User.__tablename__ == "users"


def test_user_model_has_id_column():
    from app.models.user import User
    assert hasattr(User, "id")


def test_user_model_has_email_column():
    from app.models.user import User
    assert hasattr(User, "email")


def test_user_model_has_hashed_password_column():
    from app.models.user import User
    assert hasattr(User, "hashed_password")


def test_user_model_can_be_instantiated():
    from app.models.user import User
    user = User(id="abc-123", email="test@example.com", hashed_password="hashed")
    assert user.id == "abc-123"
    assert user.email == "test@example.com"
    assert user.hashed_password == "hashed"


def test_user_id_is_varchar36():
    from app.models.user import User
    from sqlalchemy import VARCHAR
    col = User.__table__.c["id"]
    assert isinstance(col.type, VARCHAR)
    assert col.type.length == 36


def test_user_email_is_varchar255():
    from app.models.user import User
    from sqlalchemy import VARCHAR
    col = User.__table__.c["email"]
    assert isinstance(col.type, VARCHAR)
    assert col.type.length == 255


def test_user_email_not_nullable():
    from app.models.user import User
    col = User.__table__.c["email"]
    assert col.nullable is False


def test_user_hashed_password_not_nullable():
    from app.models.user import User
    col = User.__table__.c["hashed_password"]
    assert col.nullable is False


def test_user_persisted_and_retrieved():
    engine = make_in_memory_engine()
    from app.models.user import User
    with Session(engine) as session:
        user = User(id="u1", email="a@b.com", hashed_password="hashed_pw")
        session.add(user)
        session.commit()
        found = session.get(User, "u1")
        assert found is not None
        assert found.email == "a@b.com"


# ---------------------------------------------------------------------------
# Task model
# ---------------------------------------------------------------------------

def test_task_model_has_correct_tablename():
    from app.models.task import Task
    assert Task.__tablename__ == "tasks"


def test_task_model_has_id_column():
    from app.models.task import Task
    assert hasattr(Task, "id")


def test_task_model_has_userId_column():
    from app.models.task import Task
    assert hasattr(Task, "userId")


def test_task_model_has_title_column():
    from app.models.task import Task
    assert hasattr(Task, "title")


def test_task_model_has_completed_column():
    from app.models.task import Task
    assert hasattr(Task, "completed")


def test_task_model_has_created_at_column():
    from app.models.task import Task
    assert hasattr(Task, "created_at")


def test_task_id_is_varchar36():
    from app.models.task import Task
    from sqlalchemy import VARCHAR
    col = Task.__table__.c["id"]
    assert isinstance(col.type, VARCHAR)
    assert col.type.length == 36


def test_task_userId_is_varchar36():
    from app.models.task import Task
    from sqlalchemy import VARCHAR
    col = Task.__table__.c["userId"]
    assert isinstance(col.type, VARCHAR)
    assert col.type.length == 36


def test_task_title_is_varchar255():
    from app.models.task import Task
    from sqlalchemy import VARCHAR
    col = Task.__table__.c["title"]
    assert isinstance(col.type, VARCHAR)
    assert col.type.length == 255


def test_task_title_not_nullable():
    from app.models.task import Task
    col = Task.__table__.c["title"]
    assert col.nullable is False


def test_task_completed_not_nullable():
    from app.models.task import Task
    col = Task.__table__.c["completed"]
    assert col.nullable is False


def test_task_completed_defaults_false():
    """completed has server_default=False (0) so it is not null when inserted without it."""
    engine = make_in_memory_engine()
    from app.models.user import User
    from app.models.task import Task
    with Session(engine) as session:
        user = User(id="u2", email="c@d.com", hashed_password="hashed")
        session.add(user)
        session.flush()
        task = Task(id="t1", userId="u2", title="A task")
        session.add(task)
        session.commit()
        found = session.get(Task, "t1")
        assert found is not None
        assert found.completed is False or found.completed == 0


def test_task_created_at_has_server_default():
    from app.models.task import Task
    col = Task.__table__.c["created_at"]
    assert col.server_default is not None


def test_task_userId_has_fk_to_users():
    from app.models.task import Task
    col = Task.__table__.c["userId"]
    fks = list(col.foreign_keys)
    assert len(fks) == 1
    assert "users.id" in str(fks[0].target_fullname)


def test_task_fk_cascade_delete():
    """Deleting a user cascades and deletes their tasks."""
    from sqlalchemy import create_engine, event
    from app.models.base import Base
    import app.models.user  # noqa: F401
    import app.models.task  # noqa: F401
    import app.models.token_blacklist  # noqa: F401

    # Create a fresh engine with FK enforcement for this test only
    fk_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    @event.listens_for(fk_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(fk_engine)

    from app.models.user import User
    from app.models.task import Task
    with Session(fk_engine) as session:
        user = User(id="u3", email="e@f.com", hashed_password="hashed")
        session.add(user)
        session.flush()
        task = Task(id="t2", userId="u3", title="Cascade me")
        session.add(task)
        session.commit()
        session.delete(user)
        session.commit()
        assert session.get(Task, "t2") is None


def test_task_model_can_be_instantiated():
    from app.models.task import Task
    task = Task(id="t3", userId="u1", title="Hello")
    assert task.title == "Hello"


# ---------------------------------------------------------------------------
# TokenBlacklist model
# ---------------------------------------------------------------------------

def test_token_blacklist_model_has_correct_tablename():
    from app.models.token_blacklist import TokenBlacklist
    assert TokenBlacklist.__tablename__ == "token_blacklist"


def test_token_blacklist_has_jti_column():
    from app.models.token_blacklist import TokenBlacklist
    assert hasattr(TokenBlacklist, "jti")


def test_token_blacklist_has_expires_at_column():
    from app.models.token_blacklist import TokenBlacklist
    assert hasattr(TokenBlacklist, "expires_at")


def test_token_blacklist_jti_is_varchar36():
    from app.models.token_blacklist import TokenBlacklist
    from sqlalchemy import VARCHAR
    col = TokenBlacklist.__table__.c["jti"]
    assert isinstance(col.type, VARCHAR)
    assert col.type.length == 36


def test_token_blacklist_expires_at_not_nullable():
    from app.models.token_blacklist import TokenBlacklist
    col = TokenBlacklist.__table__.c["expires_at"]
    assert col.nullable is False


def test_token_blacklist_can_be_persisted():
    from datetime import datetime
    engine = make_in_memory_engine()
    from app.models.token_blacklist import TokenBlacklist
    with Session(engine) as session:
        entry = TokenBlacklist(jti="jti-001", expires_at=datetime(2026, 1, 1, 12, 0, 0))
        session.add(entry)
        session.commit()
        found = session.get(TokenBlacklist, "jti-001")
        assert found is not None
        assert found.jti == "jti-001"


# ---------------------------------------------------------------------------
# get_db dependency
# ---------------------------------------------------------------------------

def test_get_db_importable():
    mod = importlib.import_module("app.dependencies")
    assert hasattr(mod, "get_db")


def test_get_db_yields_session():
    from app.dependencies import get_db
    engine = make_in_memory_engine()
    # Patch the engine used by get_db
    import app.dependencies as deps
    original = deps.engine
    deps.engine = engine
    try:
        gen = get_db()
        session = next(gen)
        assert isinstance(session, Session)
        try:
            next(gen)
        except StopIteration:
            pass
    finally:
        deps.engine = original


def test_get_db_closes_session_after_use():
    """get_db generator must close the session after the request context ends."""
    from app.dependencies import get_db
    import app.dependencies as deps

    engine = make_in_memory_engine()
    original = deps.engine
    deps.engine = engine
    closed_sessions = []

    try:
        gen = get_db()
        session = next(gen)
        # Monkey-patch to track close
        original_close = session.close
        def tracked_close():
            closed_sessions.append(True)
            original_close()
        session.close = tracked_close

        try:
            next(gen)
        except StopIteration:
            pass
        assert len(closed_sessions) == 1
    finally:
        deps.engine = original
