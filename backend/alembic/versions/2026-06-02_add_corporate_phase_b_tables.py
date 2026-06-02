"""add corporate-legal Phase B tables (governance / entity / integration / notifications)

- board_meetings, board_documents      董事会与公司秘书
- corporate_entities, entity_compliance_items  主体管理
- integration_tasks                    交割后整合
- corporate_notifications              dataroom-watcher 站内通知

Idempotent guard; name-agnostic downgrade.

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-06-02 00:00:02.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d5e6f7a8b9c0"
down_revision: str | None = "c4d5e6f7a8b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _ts() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "board_meetings" in inspector.get_table_names():
        return

    op.create_table(
        "board_meetings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("entity_name", sa.String(255), nullable=True),
        sa.Column("kind", sa.String(30), nullable=False, server_default="board"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("meeting_date", sa.String(50), nullable=True),
        sa.Column("attendees", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        *_ts(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_board_meetings_user_id"
        ),
    )
    op.create_index("ix_board_meetings_user_id", "board_meetings", ["user_id"])

    op.create_table(
        "board_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("meeting_id", sa.String(36), nullable=True),
        sa.Column("doc_kind", sa.String(30), nullable=False, server_default="minutes"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        *_ts(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_board_documents_user_id"
        ),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["board_meetings.id"],
            ondelete="SET NULL",
            name="fk_board_documents_meeting_id",
        ),
    )
    op.create_index("ix_board_documents_user_id", "board_documents", ["user_id"])
    op.create_index("ix_board_documents_meeting_id", "board_documents", ["meeting_id"])

    op.create_table(
        "corporate_entities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("jurisdiction", sa.String(255), nullable=True),
        sa.Column("controller", sa.String(255), nullable=True),
        sa.Column("equity_ratio", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("notes", sa.Text(), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_corporate_entities_user_id"
        ),
    )
    op.create_index("ix_corporate_entities_user_id", "corporate_entities", ["user_id"])

    op.create_table(
        "entity_compliance_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("filing_type", sa.String(100), nullable=False),
        sa.Column("due_date", sa.String(50), nullable=True),
        sa.Column("recurrence", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("notes", sa.Text(), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["corporate_entities.id"],
            ondelete="CASCADE",
            name="fk_entity_compliance_items_entity_id",
        ),
    )
    op.create_index(
        "ix_entity_compliance_items_entity_id", "entity_compliance_items", ["entity_id"]
    )

    op.create_table(
        "integration_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("deal_id", sa.String(36), nullable=False),
        sa.Column("phase", sa.String(10), nullable=False, server_default="D30"),
        sa.Column("task", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("due", sa.String(50), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(
            ["deal_id"],
            ["corporate_deals.id"],
            ondelete="CASCADE",
            name="fk_integration_tasks_deal_id",
        ),
    )
    op.create_index("ix_integration_tasks_deal_id", "integration_tasks", ["deal_id"])

    op.create_table(
        "corporate_notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(50), nullable=False, server_default="dataroom_watcher"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("deal_id", sa.String(36), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        *_ts(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_corporate_notifications_user_id"
        ),
    )
    op.create_index("ix_corporate_notifications_user_id", "corporate_notifications", ["user_id"])
    op.create_index("ix_corporate_notifications_deal_id", "corporate_notifications", ["deal_id"])


def downgrade() -> None:
    op.drop_table("corporate_notifications")
    op.drop_table("integration_tasks")
    op.drop_table("entity_compliance_items")
    op.drop_table("corporate_entities")
    op.drop_table("board_documents")
    op.drop_table("board_meetings")
