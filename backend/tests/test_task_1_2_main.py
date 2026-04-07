"""
Tests for task 1.2: Bootstrap the FastAPI application with CORS, exception handlers,
and lifespan.
Covers:
  - FastAPI app instance creation
  - CORSMiddleware allowing only the configured Angular origin
  - Global exception handlers for domain exceptions → HTTP status codes
  - Routers mounted at /api/v1/auth and /api/v1/tasks
  - OpenAPI spec accessible at /docs
"""
import os
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# App import
# ---------------------------------------------------------------------------

def test_main_module_importable():
    import app.main  # noqa: F401


def test_app_is_fastapi_instance():
    from fastapi import FastAPI
    from app.main import app
    assert isinstance(app, FastAPI)


# ---------------------------------------------------------------------------
# OpenAPI / docs
# ---------------------------------------------------------------------------

def test_docs_endpoint_accessible():
    from app.main import app
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_json_accessible():
    from app.main import app
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

def test_cors_allows_configured_origin(monkeypatch):
    monkeypatch.setenv("CORS_ORIGIN", "https://sdd-todo-challange.vercel.app")
    # Re-import to pick up env override (or use the default which is already 4200)
    from app.main import app
    client = TestClient(app)
    response = client.options(
        "/api/v1/auth/register",
        headers={
            "Origin": "https://sdd-todo-challange.vercel.app",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "https://sdd-todo-challange.vercel.app"


def test_cors_does_not_allow_arbitrary_origin():
    from app.main import app
    client = TestClient(app)
    response = client.options(
        "/api/v1/auth/register",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    # Should not echo back the evil origin
    allow_origin = response.headers.get("access-control-allow-origin", "")
    assert allow_origin != "http://evil.example.com"


# ---------------------------------------------------------------------------
# Exception handlers → HTTP status codes
# ---------------------------------------------------------------------------

def test_authentication_error_returns_401():
    from app.main import app
    from app.core.exceptions import AuthenticationError
    from fastapi import APIRouter
    from fastapi.testclient import TestClient

    # Temporarily add a test route that raises AuthenticationError
    test_router = APIRouter()

    @test_router.get("/_test/auth-error")
    def raise_auth_error():
        raise AuthenticationError("test")

    app.include_router(test_router)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/_test/auth-error")
    assert response.status_code == 401


def test_conflict_error_returns_409():
    from app.main import app
    from app.core.exceptions import ConflictError
    from fastapi import APIRouter

    test_router = APIRouter()

    @test_router.get("/_test/conflict-error")
    def raise_conflict():
        raise ConflictError("test")

    app.include_router(test_router)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/_test/conflict-error")
    assert response.status_code == 409


def test_not_found_error_returns_404():
    from app.main import app
    from app.core.exceptions import NotFoundError
    from fastapi import APIRouter

    test_router = APIRouter()

    @test_router.get("/_test/not-found-error")
    def raise_not_found():
        raise NotFoundError("test")

    app.include_router(test_router)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/_test/not-found-error")
    assert response.status_code == 404


def test_forbidden_error_returns_403():
    from app.main import app
    from app.core.exceptions import ForbiddenError
    from fastapi import APIRouter

    test_router = APIRouter()

    @test_router.get("/_test/forbidden-error")
    def raise_forbidden():
        raise ForbiddenError("test")

    app.include_router(test_router)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/_test/forbidden-error")
    assert response.status_code == 403


def test_validation_error_returns_422():
    from app.main import app
    from app.core.exceptions import ValidationError
    from fastapi import APIRouter

    test_router = APIRouter()

    @test_router.get("/_test/validation-error")
    def raise_validation():
        raise ValidationError("test")

    app.include_router(test_router)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/_test/validation-error")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Router mounts
# ---------------------------------------------------------------------------

def test_auth_router_prefix_mounted():
    from app.main import app
    routes = [r.path for r in app.routes]  # type: ignore[attr-defined]
    auth_routes = [r for r in routes if r.startswith("/api/v1/auth")]
    assert len(auth_routes) > 0, "No routes found under /api/v1/auth"


def test_tasks_router_prefix_mounted():
    from app.main import app
    routes = [r.path for r in app.routes]  # type: ignore[attr-defined]
    task_routes = [r for r in routes if r.startswith("/api/v1/tasks")]
    assert len(task_routes) > 0, "No routes found under /api/v1/tasks"
