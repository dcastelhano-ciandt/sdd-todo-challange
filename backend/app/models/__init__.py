"""
ORM model package — import all models so that Base.metadata is fully populated
before any `create_all` or Alembic autogenerate call.
"""
from app.models.base import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.token_blacklist import TokenBlacklist  # noqa: F401
