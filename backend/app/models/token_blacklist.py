"""
SQLAlchemy ORM model for the token_blacklist table.

Physical schema:
  jti         VARCHAR(36)  PRIMARY KEY
  expires_at  DATETIME     NOT NULL
"""
from sqlalchemy import VARCHAR, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    jti: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True)
    expires_at: Mapped[object] = mapped_column(DateTime, nullable=False)
