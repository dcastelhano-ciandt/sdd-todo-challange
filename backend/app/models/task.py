"""
SQLAlchemy ORM model for the tasks table.

Physical schema:
  id          VARCHAR(36)  PRIMARY KEY
  userId      VARCHAR(36)  NOT NULL, FK → users.id ON DELETE CASCADE
  title       VARCHAR(255) NOT NULL
  completed   BOOLEAN      NOT NULL DEFAULT FALSE
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
  due_date    DATETIME     NULL
"""
from datetime import date
from typing import Optional

from sqlalchemy import VARCHAR, Boolean, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True)
    userId: Mapped[str] = mapped_column(
        VARCHAR(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("0"),
        default=False,
    )
    created_at: Mapped[object] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )
