"""add regulatory-legal core tables

Second slice: reg_items / analyses / gaps / comments / notifications.

Idempotent guard (锚点表: regulatory_reg_items); name-agnostic downgrade
(reverse FK order: notifications/comments/gaps/analyses before reg_items).

Revision ID: reg2b3c4d5e6f
Revises: reg1a2b3c4d5e
Create Date: 2026-06-13 10:00:01.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "reg2b3c4d5e6f"
down_revision: str | None = "reg1a2b3c4d5e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _ts_columns() -> list[sa.Column]:
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
    if "regulatory_reg_items" in inspector.get_table_names():
        return

    # regulatory_reg_items --------------------------------------------------
    op.create_table(
        "regulatory_reg_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("regulator", sa.String(255), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("item_type", sa.String(20), nullable=False, server_default="other"),
        sa.Column("materiality", sa.String(20), nullable=False, server_default="review"),
        sa.Column("materiality_source", sa.String(20), nullable=False, server_default="auto_rule"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("relevance_hook", sa.Text(), nullable=True),
        sa.Column("link", sa.String(1000), nullable=True),
        sa.Column("published_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("comment_deadline", sa.Date(), nullable=True),
        sa.Column("source_tag", sa.String(60), nullable=True),
        sa.Column("source_name", sa.String(255), nullable=True),
        sa.Column("status_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("dedup_key", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_regulatory_reg_items_user_id"
        ),
    )
    op.create_index("ix_regulatory_reg_items_user_id", "regulatory_reg_items", ["user_id"])
    op.create_index(
        "ix_regulatory_reg_items_user_materiality",
        "regulatory_reg_items",
        ["user_id", "materiality"],
    )
    op.create_index(
        "ix_regulatory_reg_items_user_created", "regulatory_reg_items", ["user_id", "created_at"]
    )
    op.create_index(
        "ix_regulatory_reg_items_user_dedup", "regulatory_reg_items", ["user_id", "dedup_key"]
    )

    # regulatory_analyses ---------------------------------------------------
    op.create_table(
        "regulatory_analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("reg_item_id", sa.String(36), nullable=True),
        sa.Column("analysis_type", sa.String(30), nullable=False),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("regulation_name", sa.String(255), nullable=True),
        sa.Column("policy_affected", sa.String(255), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("scope_limited", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("scope_note", sa.Text(), nullable=True),
        sa.Column("status_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("result_memo", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_regulatory_analyses_user_id"
        ),
        sa.ForeignKeyConstraint(
            ["reg_item_id"],
            ["regulatory_reg_items.id"],
            ondelete="SET NULL",
            name="fk_regulatory_analyses_reg_item_id",
        ),
    )
    op.create_index("ix_regulatory_analyses_user_id", "regulatory_analyses", ["user_id"])
    op.create_index(
        "ix_regulatory_analyses_user_subject", "regulatory_analyses", ["user_id", "subject"]
    )
    op.create_index("ix_regulatory_analyses_type", "regulatory_analyses", ["analysis_type"])

    # regulatory_gaps -------------------------------------------------------
    op.create_table(
        "regulatory_gaps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("reg_item_id", sa.String(36), nullable=True),
        sa.Column("analysis_id", sa.String(36), nullable=True),
        sa.Column("requirement", sa.Text(), nullable=True),
        sa.Column("regulation", sa.String(500), nullable=True),
        sa.Column("regulation_citation", sa.String(255), nullable=True),
        sa.Column("policy_affected", sa.String(255), nullable=True),
        sa.Column("gap_type", sa.String(20), nullable=False, server_default="partial"),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("owner_contact", sa.String(255), nullable=True),
        sa.Column("opened", sa.Date(), nullable=True),
        sa.Column("due", sa.Date(), nullable=True),
        sa.Column("status_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("notified", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("accepted_by", sa.String(255), nullable=True),
        sa.Column("accepted_rationale", sa.Text(), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_regulatory_gaps_user_id"
        ),
        sa.ForeignKeyConstraint(
            ["reg_item_id"],
            ["regulatory_reg_items.id"],
            ondelete="SET NULL",
            name="fk_regulatory_gaps_reg_item_id",
        ),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["regulatory_analyses.id"],
            ondelete="SET NULL",
            name="fk_regulatory_gaps_analysis_id",
        ),
    )
    op.create_index("ix_regulatory_gaps_user_id", "regulatory_gaps", ["user_id"])
    op.create_index("ix_regulatory_gaps_user_status", "regulatory_gaps", ["user_id", "status"])
    op.create_index("ix_regulatory_gaps_user_due", "regulatory_gaps", ["user_id", "due"])

    # regulatory_comments ---------------------------------------------------
    op.create_table(
        "regulatory_comments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("reg_item_id", sa.String(36), nullable=True),
        sa.Column("regulation", sa.String(500), nullable=True),
        sa.Column("regulator", sa.String(255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("link", sa.String(1000), nullable=True),
        sa.Column("comment_deadline", sa.Date(), nullable=True),
        sa.Column("detected", sa.Date(), nullable=True),
        sa.Column("decision", sa.String(20), nullable=False, server_default="undecided"),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("owner_contact", sa.String(255), nullable=True),
        sa.Column("notified", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("filed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_regulatory_comments_user_id"
        ),
        sa.ForeignKeyConstraint(
            ["reg_item_id"],
            ["regulatory_reg_items.id"],
            ondelete="SET NULL",
            name="fk_regulatory_comments_reg_item_id",
        ),
    )
    op.create_index("ix_regulatory_comments_user_id", "regulatory_comments", ["user_id"])
    op.create_index(
        "ix_regulatory_comments_user_decision", "regulatory_comments", ["user_id", "decision"]
    )
    op.create_index(
        "ix_regulatory_comments_user_deadline",
        "regulatory_comments",
        ["user_id", "comment_deadline"],
    )

    # regulatory_notifications ----------------------------------------------
    op.create_table(
        "regulatory_notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("notification_type", sa.String(50), nullable=False, server_default="reg_digest"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("action_url", sa.String(500), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_regulatory_notifications_user_id",
        ),
    )
    op.create_index("ix_regulatory_notifications_user_id", "regulatory_notifications", ["user_id"])


def downgrade() -> None:
    # 逆 FK 顺序 drop: 先子表后主表
    op.drop_table("regulatory_notifications")
    op.drop_table("regulatory_comments")
    op.drop_table("regulatory_gaps")
    op.drop_table("regulatory_analyses")
    op.drop_table("regulatory_reg_items")
