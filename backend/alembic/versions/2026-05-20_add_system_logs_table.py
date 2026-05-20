"""add system_logs table

Revision ID: 9f8e7d6c5b4a
Revises: fb1e5e73ee3a
Create Date: 2026-05-20 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f8e7d6c5b4a"
down_revision: str | None = "fb1e5e73ee3a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "system_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("level", sa.String(20), nullable=False, server_default="info"),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("metadata_json", sa.Text, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("request_id", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("system_logs_created_at_idx", "system_logs", ["created_at"])
    op.create_index("system_logs_category_idx", "system_logs", ["category"])
    op.create_index("system_logs_user_id_idx", "system_logs", ["user_id"])


def downgrade() -> None:
    op.drop_index("system_logs_user_id_idx", "system_logs")
    op.drop_index("system_logs_category_idx", "system_logs")
    op.drop_index("system_logs_created_at_idx", "system_logs")
    op.drop_table("system_logs")
