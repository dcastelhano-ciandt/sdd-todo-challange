"""
TaskService — business logic for task management.

Responsibilities:
- Task creation: generate UUID, validate title, set defaults, delegate to repository
- Task listing: delegate to repository with optional status filter
- Task mutation (update, toggle, delete): fetch task, verify ownership, mutate, persist

All mutations verify that task.userId == current user_id before proceeding.
UUIDs for new tasks are generated here, not by the database.
"""
import uuid
from typing import List, Optional

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.task import Task
from app.repositories.task_repository import TaskRepository


class TaskService:
    def __init__(self, task_repo: TaskRepository) -> None:
        self.task_repo = task_repo

    # -----------------------------------------------------------------------
    # create_task
    # -----------------------------------------------------------------------

    def create_task(self, user_id: str, title: str) -> Task:
        """Create a new task owned by user_id.

        Raises ValidationError if title is empty or whitespace-only.
        """
        if not title or not title.strip():
            raise ValidationError("Task title must not be empty.")

        task_id = str(uuid.uuid4())
        return self.task_repo.create(user_id=user_id, task_id=task_id, title=title)

    # -----------------------------------------------------------------------
    # list_tasks
    # -----------------------------------------------------------------------

    def list_tasks(
        self,
        user_id: str,
        status: Optional[str] = None,
        q: Optional[str] = None,
    ) -> List[Task]:
        """Return tasks owned by user_id, ordered by created_at DESC.

        status: "pending" → completed=False filter
                "completed" → completed=True filter
                None → no filter

        q: optional search keyword for case-insensitive title filter.
           Whitespace-only or empty values are treated as no filter (None).
        """
        completed_filter: Optional[bool] = None
        if status == "pending":
            completed_filter = False
        elif status == "completed":
            completed_filter = True

        # Normalize keyword: strip whitespace; treat empty/whitespace-only as None
        cleaned_q: Optional[str] = q.strip() if q else None
        if cleaned_q == "":
            cleaned_q = None

        return self.task_repo.list_by_user(
            user_id=user_id, status=completed_filter, q=cleaned_q
        )

    # -----------------------------------------------------------------------
    # update_task
    # -----------------------------------------------------------------------

    def update_task(self, task_id: str, user_id: str, title: str) -> Task:
        """Update the title of a task owned by user_id.

        Raises NotFoundError if the task does not exist.
        Raises ForbiddenError if the task is not owned by user_id.
        Raises ValidationError if the new title is empty or whitespace-only.
        """
        task = self._get_owned_task(task_id=task_id, user_id=user_id)

        if not title or not title.strip():
            raise ValidationError("Task title must not be empty.")

        task.title = title
        return self.task_repo.update(task)

    # -----------------------------------------------------------------------
    # toggle_completion
    # -----------------------------------------------------------------------

    def toggle_completion(self, task_id: str, user_id: str) -> Task:
        """Flip the completed boolean for a task owned by user_id.

        Raises NotFoundError if the task does not exist.
        Raises ForbiddenError if the task is not owned by user_id.
        """
        task = self._get_owned_task(task_id=task_id, user_id=user_id)
        task.completed = not task.completed
        return self.task_repo.update(task)

    # -----------------------------------------------------------------------
    # delete_task
    # -----------------------------------------------------------------------

    def delete_task(self, task_id: str, user_id: str) -> None:
        """Permanently remove a task owned by user_id.

        Raises NotFoundError if the task does not exist.
        Raises ForbiddenError if the task is not owned by user_id.
        """
        task = self._get_owned_task(task_id=task_id, user_id=user_id)
        self.task_repo.delete(task)

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _get_owned_task(self, task_id: str, user_id: str) -> Task:
        """Fetch a task by id and verify ownership.

        Raises NotFoundError if the task does not exist.
        Raises ForbiddenError if task.userId != user_id.
        Ownership check always precedes mutation — never update then check.
        """
        task = self.task_repo.get_by_id(task_id)
        if task is None:
            raise NotFoundError(f"Task {task_id!r} not found.")
        if task.userId != user_id:
            raise ForbiddenError("You do not own this task.")
        return task
