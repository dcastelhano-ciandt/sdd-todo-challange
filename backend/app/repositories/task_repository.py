"""
TaskRepository — persistence operations for the tasks table.

Operations:
- create(user_id, task_id, title) -> Task
- list_by_user(user_id, status) -> list[Task]
- get_by_id(task_id) -> Task | None
- update(task) -> Task
- delete(task) -> None

list_by_user:
  - Filters WHERE userId = :user_id
  - Optional completed filter when status is True or False (not None)
  - Orders by created_at DESC
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.task import Task


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user_id: str, task_id: str, title: str) -> Task:
        """Persist a new Task and return it."""
        task = Task(
            id=task_id,
            userId=user_id,
            title=title,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def list_by_user(self, user_id: str, status: Optional[bool]) -> List[Task]:
        """Return tasks for user_id, optionally filtered by completed status.

        Results are ordered by created_at DESC (newest first).
        """
        query = (
            self.db.query(Task)
            .filter(Task.userId == user_id)
        )
        if status is not None:
            query = query.filter(Task.completed == status)
        query = query.order_by(Task.created_at.desc())
        return query.all()

    def get_by_id(self, task_id: str) -> Optional[Task]:
        """Return the Task with the given id, or None if not found."""
        return self.db.get(Task, task_id)

    def update(self, task: Task) -> Task:
        """Persist changes to an existing task and return it."""
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task: Task) -> None:
        """Permanently remove a task from the database."""
        self.db.delete(task)
        self.db.commit()
