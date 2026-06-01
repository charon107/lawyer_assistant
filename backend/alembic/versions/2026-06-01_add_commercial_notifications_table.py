"""add commercial_notifications table

Phase C, Track C1. Adds the in-app notification inbox that the scheduled
commercial tasks (renewal-watcher, deal-debrief, playbook-monitor) write to.

Revision ID: e2c3d4e5f6a7
Revises: d1b2c3d4e5f6
Create Date: 2026-06-01 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2c3d4e5f6a7"
down_revision: str | None = "d1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "commercial_notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_commercial_notifications_user_id",
        ),
    )
    op.create_index("ix_commercial_notifications_user_id", "commercial_notifications", ["user_id"])
    op.create_index("ix_commercial_notifications_type", "commercial_notifications", ["type"])
    op.create_index("ix_commercial_notifications_read", "commercial_notifications", ["read"])


def downgrade() -> None:
    op.drop_index("ix_commercial_notifications_read", table_name="commercial_notifications")
    op.drop_index("ix_commercial_notifications_type", table_name="commercial_notifications")
    op.drop_index("ix_commercial_notifications_user_id", table_name="commercial_notifications")
    op.drop_table("commercial_notifications")
