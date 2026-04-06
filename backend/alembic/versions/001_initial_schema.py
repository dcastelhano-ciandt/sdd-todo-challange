"""Initial schema: users, tasks, and token_blacklist tables.

Revision ID: 001
Revises: (none)
Create Date: 2026-04-02

Creates three tables and their associated indexes:
  - users        (id, email, hashed_password)
  - tasks        (id, userId FK→users ON DELETE CASCADE, title, completed, created_at)
  - token_blacklist (jti, expires_at)

Indexes created:
  - ix_tasks_userId           on tasks(userId)
  - ix_tasks_userId_completed on tasks(userId, completed)
  - ix_token_blacklist_expires_at on token_blacklist(expires_at)
"""

from alembic import op
import sqlalchemy as sa

# Alembic revision identifiers.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Table: users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.VARCHAR(36), nullable=False),
        sa.Column("email", sa.VARCHAR(255), nullable=False),
        sa.Column("hashed_password", sa.VARCHAR(255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # ------------------------------------------------------------------
    # Table: tasks
    # ------------------------------------------------------------------
    op.create_table(
        "tasks",
        sa.Column("id", sa.VARCHAR(36), nullable=False),
        sa.Column("userId", sa.VARCHAR(36), nullable=False),
        sa.Column("title", sa.VARCHAR(255), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["userId"],
            ["users.id"],
            ondelete="CASCADE",
        ),
    )

    # Indexes on tasks
    op.create_index("ix_tasks_userId", "tasks", ["userId"], unique=False)
    op.create_index(
        "ix_tasks_userId_completed", "tasks", ["userId", "completed"], unique=False
    )

    # ------------------------------------------------------------------
    # Table: token_blacklist
    # ------------------------------------------------------------------
    op.create_table(
        "token_blacklist",
        sa.Column("jti", sa.VARCHAR(36), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("jti"),
    )

    # Index on token_blacklist to support efficient lazy pruning.
    op.create_index(
        "ix_token_blacklist_expires_at", "token_blacklist", ["expires_at"], unique=False
    )


def downgrade() -> None:
    # Drop in reverse dependency order (children before parents).
    op.drop_index("ix_token_blacklist_expires_at", table_name="token_blacklist")
    op.drop_table("token_blacklist")

    op.drop_index("ix_tasks_userId_completed", table_name="tasks")
    op.drop_index("ix_tasks_userId", table_name="tasks")
    op.drop_table("tasks")

    op.drop_table("users")
