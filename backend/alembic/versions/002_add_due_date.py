"""Add due_date column to tasks table.

Revision ID: 002
Revises: 001
Create Date: 2026-04-06

Adds:
  - tasks.due_date  DATETIME NULL  (nullable, no default — existing rows get NULL)
  - ix_tasks_userId_due_date  index on (userId, due_date)
"""

from alembic import op
import sqlalchemy as sa

# Alembic revision identifiers.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("due_date", sa.DateTime(), nullable=True))
        batch_op.create_index(
            "ix_tasks_userId_due_date",
            ["userId", "due_date"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_index("ix_tasks_userId_due_date")
        batch_op.drop_column("due_date")
