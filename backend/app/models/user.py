"""
SQLAlchemy ORM model for the users table.

Physical schema:
  id            VARCHAR(36)  PRIMARY KEY
  email         VARCHAR(255) NOT NULL, UNIQUE
  hashed_password VARCHAR(255) NOT NULL
"""
from sqlalchemy import VARCHAR, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email"),)

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True)
    email: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
