"""
TaskRepository — persistence operations for the tasks table.

Operations:
- create(user_id, task_id, title, due_date) -> Task
- list_by_user(user_id, status, sort_by, sort_dir) -> list[Task]
- get_by_id(task_id) -> Task | None
- update(task) -> Task
- delete(task) -> None

list_by_user:
  - Filters WHERE userId = :user_id
  - Optional completed filter when status is True or False (not None)
  - When sort_by="due_date": orders by due_date ASC/DESC nullslast
  - Otherwise: orders by created_at DESC
"""
from datetime import date
from typing import List, Optional

from sqlalchemy import asc, desc, nullslast
from sqlalchemy.orm import Session

from app.models.task import Task


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        user_id: str,
        task_id: str,
        title: str,
        due_date: Optional[date] = None,
    ) -> Task:
        """Persist a new Task and return it."""
        task = Task(
            id=task_id,
            userId=user_id,
            title=title,
            due_date=due_date,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def list_by_user(
        self,
        user_id: str,
        status: Optional[bool],
        sort_by: Optional[str] = None,
        sort_dir: str = "asc",
    ) -> List[Task]:
        """Return tasks for user_id, optionally filtered by completed status.

        When sort_by="due_date": ordered by due_date (direction per sort_dir),
        with NULL values last (nullslast).
        Otherwise: ordered by created_at DESC (newest first).
        """
        query = (
            self.db.query(Task)
            .filter(Task.userId == user_id)
        )
        if status is not None:
            query = query.filter(Task.completed == status)

        if sort_by == "due_date":
            if sort_dir == "desc":
                order_clause = nullslast(desc(Task.due_date))
            else:
                order_clause = nullslast(asc(Task.due_date))
            query = query.order_by(order_clause)
        else:
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
