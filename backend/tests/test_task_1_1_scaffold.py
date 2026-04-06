"""
Tests for task 1.1: Scaffold the backend directory layout and install dependencies.
Covers: core settings module, domain exceptions module, directory structure.
"""
import os
import importlib
import pytest


# ---------------------------------------------------------------------------
# Directory structure
# ---------------------------------------------------------------------------

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_directory_app_exists():
    assert os.path.isdir(os.path.join(BACKEND_DIR, "app"))


def test_directory_routers_exists():
    assert os.path.isdir(os.path.join(BACKEND_DIR, "app", "routers"))


def test_directory_services_exists():
    assert os.path.isdir(os.path.join(BACKEND_DIR, "app", "services"))


def test_directory_repositories_exists():
    assert os.path.isdir(os.path.join(BACKEND_DIR, "app", "repositories"))


def test_directory_models_exists():
    assert os.path.isdir(os.path.join(BACKEND_DIR, "app", "models"))


def test_directory_schemas_exists():
    assert os.path.isdir(os.path.join(BACKEND_DIR, "app", "schemas"))


def test_directory_core_exists():
    assert os.path.isdir(os.path.join(BACKEND_DIR, "app", "core"))


def test_requirements_txt_exists():
    assert os.path.isfile(os.path.join(BACKEND_DIR, "requirements.txt"))


# ---------------------------------------------------------------------------
# requirements.txt content
# ---------------------------------------------------------------------------

def _read_requirements():
    path = os.path.join(BACKEND_DIR, "requirements.txt")
    with open(path) as f:
        return f.read().lower()


def test_requirements_contains_fastapi():
    assert "fastapi" in _read_requirements()


def test_requirements_contains_sqlalchemy():
    assert "sqlalchemy" in _read_requirements()


def test_requirements_contains_alembic():
    assert "alembic" in _read_requirements()


def test_requirements_contains_python_jose():
    assert "python-jose" in _read_requirements()


def test_requirements_contains_passlib():
    assert "passlib" in _read_requirements()


def test_requirements_contains_email_validator():
    assert "email-validator" in _read_requirements()


# ---------------------------------------------------------------------------
# Settings module (app/core/config.py)
# ---------------------------------------------------------------------------

def test_settings_module_importable():
    mod = importlib.import_module("app.core.config")
    assert mod is not None


def test_settings_has_secret_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-32-characters-ok")
    importlib.invalidate_caches()
    import importlib as il
    import app.core.config as cfg
    il.reload(cfg)
    settings = cfg.Settings()
    assert settings.SECRET_KEY == "test-secret-key-32-characters-ok"


def test_settings_has_access_token_expire_minutes(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-32-characters-ok")
    import app.core.config as cfg
    importlib.reload(cfg)
    settings = cfg.Settings()
    assert hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES")
    assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)


def test_settings_has_database_url(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-32-characters-ok")
    import app.core.config as cfg
    importlib.reload(cfg)
    settings = cfg.Settings()
    assert hasattr(settings, "DATABASE_URL")
    assert isinstance(settings.DATABASE_URL, str)


def test_settings_has_cors_origin(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-32-characters-ok")
    import app.core.config as cfg
    importlib.reload(cfg)
    settings = cfg.Settings()
    assert hasattr(settings, "CORS_ORIGIN")
    assert isinstance(settings.CORS_ORIGIN, str)


# ---------------------------------------------------------------------------
# Exceptions module (app/core/exceptions.py)
# ---------------------------------------------------------------------------

def test_exceptions_module_importable():
    mod = importlib.import_module("app.core.exceptions")
    assert mod is not None


def test_authentication_error_exists():
    from app.core.exceptions import AuthenticationError
    assert issubclass(AuthenticationError, Exception)


def test_conflict_error_exists():
    from app.core.exceptions import ConflictError
    assert issubclass(ConflictError, Exception)


def test_not_found_error_exists():
    from app.core.exceptions import NotFoundError
    assert issubclass(NotFoundError, Exception)


def test_forbidden_error_exists():
    from app.core.exceptions import ForbiddenError
    assert issubclass(ForbiddenError, Exception)


def test_validation_error_exists():
    from app.core.exceptions import ValidationError
    assert issubclass(ValidationError, Exception)


def test_authentication_error_can_be_raised():
    from app.core.exceptions import AuthenticationError
    with pytest.raises(AuthenticationError):
        raise AuthenticationError("invalid token")


def test_conflict_error_can_be_raised():
    from app.core.exceptions import ConflictError
    with pytest.raises(ConflictError):
        raise ConflictError("email already in use")


def test_not_found_error_can_be_raised():
    from app.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        raise NotFoundError("task not found")


def test_forbidden_error_can_be_raised():
    from app.core.exceptions import ForbiddenError
    with pytest.raises(ForbiddenError):
        raise ForbiddenError("access denied")


def test_validation_error_can_be_raised():
    from app.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        raise ValidationError("title is empty")


def test_all_exceptions_are_distinct():
    from app.core.exceptions import (
        AuthenticationError,
        ConflictError,
        NotFoundError,
        ForbiddenError,
        ValidationError,
    )
    classes = {AuthenticationError, ConflictError, NotFoundError, ForbiddenError, ValidationError}
    assert len(classes) == 5
