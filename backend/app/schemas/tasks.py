"""
Pydantic request/response schemas for the tasks router.

CreateTaskRequest   — title (min_length=1), optional due_date
UpdateTaskRequest   — title (min_length=1), optional due_date
TaskResponse        — id, userId, title, completed, due_date
TaskListResponse    — tasks: list[TaskResponse]
"""
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, field_validator


class CreateTaskRequest(BaseModel):
    title: str
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or len(v) == 0:
            raise ValueError("Title must not be empty.")
        return v


class UpdateTaskRequest(BaseModel):
    title: str
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or len(v) == 0:
            raise ValueError("Title must not be empty.")
        return v


class TaskResponse(BaseModel):
    id: str
    userId: str
    title: str
    completed: bool
    due_date: Optional[date] = None

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
