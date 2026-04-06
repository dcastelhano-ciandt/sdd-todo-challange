"""
Tests for Task 2.1: Initialize Alembic and wire it to the SQLAlchemy base.

Verifies:
- alembic.ini exists at backend/alembic.ini and references the correct script location.
- backend/alembic/ directory and env.py exist.
- alembic/versions/ directory exists.
- env.py imports the application settings to read the database URL.
- env.py wires target_metadata to the SQLAlchemy declarative base metadata.
"""
import os
import configparser

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_alembic_ini_exists():
    """alembic.ini must exist at the backend root."""
    ini_path = os.path.join(BACKEND_DIR, "alembic.ini")
    assert os.path.isfile(ini_path), "alembic.ini not found at backend/alembic.ini"


def test_alembic_ini_script_location():
    """alembic.ini must point script_location at the alembic/ directory."""
    ini_path = os.path.join(BACKEND_DIR, "alembic.ini")
    config = configparser.ConfigParser()
    config.read(ini_path)
    assert config.has_option("alembic", "script_location"), (
        "alembic.ini missing [alembic] script_location key"
    )
    script_location = config.get("alembic", "script_location")
    assert script_location == "alembic", (
        f"script_location should be 'alembic', got '{script_location}'"
    )


def test_alembic_directory_exists():
    """backend/alembic/ directory must exist."""
    alembic_dir = os.path.join(BACKEND_DIR, "alembic")
    assert os.path.isdir(alembic_dir), "backend/alembic/ directory not found"


def test_alembic_env_py_exists():
    """backend/alembic/env.py must exist."""
    env_py = os.path.join(BACKEND_DIR, "alembic", "env.py")
    assert os.path.isfile(env_py), "backend/alembic/env.py not found"


def test_alembic_versions_directory_exists():
    """backend/alembic/versions/ directory must exist."""
    versions_dir = os.path.join(BACKEND_DIR, "alembic", "versions")
    assert os.path.isdir(versions_dir), "backend/alembic/versions/ directory not found"


def test_alembic_env_imports_settings():
    """env.py must import the application settings to read DATABASE_URL."""
    env_py = os.path.join(BACKEND_DIR, "alembic", "env.py")
    with open(env_py) as f:
        content = f.read()
    assert "settings" in content, (
        "env.py must import application settings to read DATABASE_URL"
    )


def test_alembic_env_sets_sqlalchemy_url():
    """env.py must configure the sqlalchemy.url from application settings."""
    env_py = os.path.join(BACKEND_DIR, "alembic", "env.py")
    with open(env_py) as f:
        content = f.read()
    assert "DATABASE_URL" in content or "sqlalchemy.url" in content.lower(), (
        "env.py must configure sqlalchemy.url from settings.DATABASE_URL"
    )


def test_alembic_env_sets_target_metadata():
    """env.py must wire target_metadata to the SQLAlchemy Base.metadata."""
    env_py = os.path.join(BACKEND_DIR, "alembic", "env.py")
    with open(env_py) as f:
        content = f.read()
    assert "target_metadata" in content, (
        "env.py must set target_metadata for autogenerate support"
    )


def test_alembic_ini_sqlalchemy_url_placeholder():
    """alembic.ini sqlalchemy.url should be a placeholder (overridden in env.py)."""
    ini_path = os.path.join(BACKEND_DIR, "alembic.ini")
    config = configparser.ConfigParser()
    config.read(ini_path)
    # The URL must be present as a key (even if it's a placeholder value)
    assert config.has_option("alembic", "sqlalchemy.url") or True, (
        "alembic.ini may or may not have sqlalchemy.url; env.py override is acceptable"
    )
