"""
Pydantic request/response schemas for the tasks router.

CreateTaskRequest   — title (min_length=1)
UpdateTaskRequest   — title (min_length=1)
TaskResponse        — id, userId, title, completed
TaskListResponse    — tasks: list[TaskResponse]
"""
from typing import List

from pydantic import BaseModel, field_validator


class CreateTaskRequest(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or len(v) == 0:
            raise ValueError("Title must not be empty.")
        return v


class UpdateTaskRequest(BaseModel):
    title: str

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

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
