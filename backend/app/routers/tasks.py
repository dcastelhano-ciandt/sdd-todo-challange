"""
Tasks router — HTTP endpoints for task CRUD and completion toggle.

Endpoints:
  POST   /api/v1/tasks                        → 201 TaskResponse
  GET    /api/v1/tasks?status=pending|completed → 200 TaskListResponse
  PUT    /api/v1/tasks/{task_id}              → 200 TaskResponse
  PATCH  /api/v1/tasks/{task_id}/toggle       → 200 TaskResponse
  DELETE /api/v1/tasks/{task_id}             → 200 MessageResponse

All endpoints require a valid Bearer token (injected via get_current_user).
The user_id is always sourced from the validated JWT, never from the request body.
UUID format validation for task_id is enforced at the router level.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import UserContext, get_auth_service, get_current_user
from app.repositories.task_repository import TaskRepository
from app.schemas.auth import MessageResponse
from app.schemas.tasks import (
    CreateTaskRequest,
    TaskListResponse,
    TaskResponse,
    UpdateTaskRequest,
)
from app.services.task_service import TaskService
from sqlalchemy.orm import Session
from app.dependencies import get_db

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency: TaskService factory
# ---------------------------------------------------------------------------

def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    """Provide a TaskService instance wired to the current request session."""
    return TaskService(task_repo=TaskRepository(db))


# ---------------------------------------------------------------------------
# Helper: validate UUID path parameter
# ---------------------------------------------------------------------------

def _validate_uuid(task_id: str) -> str:
    """Validate that task_id is a well-formed UUID.

    Raises HTTPException(422) if the value is not a valid UUID.
    """
    try:
        uuid.UUID(task_id)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {task_id!r}",
        )
    return task_id


# ---------------------------------------------------------------------------
# POST /api/v1/tasks
# ---------------------------------------------------------------------------

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    body: CreateTaskRequest,
    current_user: UserContext = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Create a new task for the authenticated user.

    Raises 422 if the title is missing or empty.
    """
    task = task_service.create_task(user_id=current_user.user_id, title=body.title)
    return TaskResponse.model_validate(task)


# ---------------------------------------------------------------------------
# GET /api/v1/tasks
# ---------------------------------------------------------------------------

@router.get("", response_model=TaskListResponse, status_code=status.HTTP_200_OK)
def list_tasks(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: UserContext = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TaskListResponse:
    """List tasks for the authenticated user, with optional status filter.

    ?status=pending   — only incomplete tasks
    ?status=completed — only completed tasks
    (no param)        — all tasks
    """
    tasks = task_service.list_tasks(user_id=current_user.user_id, status=status_filter)
    return TaskListResponse(tasks=[TaskResponse.model_validate(t) for t in tasks])


# ---------------------------------------------------------------------------
# PUT /api/v1/tasks/{task_id}
# ---------------------------------------------------------------------------

@router.put("/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def update_task(
    task_id: str,
    body: UpdateTaskRequest,
    current_user: UserContext = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Update the title of a task owned by the authenticated user.

    Raises 422 on invalid UUID format or empty title.
    Raises 403 if the user does not own the task.
    Raises 404 if the task does not exist.
    """
    _validate_uuid(task_id)
    task = task_service.update_task(
        task_id=task_id, user_id=current_user.user_id, title=body.title
    )
    return TaskResponse.model_validate(task)


# ---------------------------------------------------------------------------
# PATCH /api/v1/tasks/{task_id}/toggle
# ---------------------------------------------------------------------------

@router.patch("/{task_id}/toggle", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def toggle_task(
    task_id: str,
    current_user: UserContext = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Toggle the completed status of a task owned by the authenticated user.

    Raises 422 on invalid UUID format.
    Raises 403 if the user does not own the task.
    Raises 404 if the task does not exist.
    """
    _validate_uuid(task_id)
    task = task_service.toggle_completion(task_id=task_id, user_id=current_user.user_id)
    return TaskResponse.model_validate(task)


# ---------------------------------------------------------------------------
# DELETE /api/v1/tasks/{task_id}
# ---------------------------------------------------------------------------

@router.delete("/{task_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def delete_task(
    task_id: str,
    current_user: UserContext = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> MessageResponse:
    """Permanently delete a task owned by the authenticated user.

    Raises 422 on invalid UUID format.
    Raises 403 if the user does not own the task.
    Raises 404 if the task does not exist.
    """
    _validate_uuid(task_id)
    task_service.delete_task(task_id=task_id, user_id=current_user.user_id)
    return MessageResponse(message="Task deleted successfully.")
