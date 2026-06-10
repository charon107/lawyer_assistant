"""add ip-legal core tables

Second slice: reviews / enforcement / portfolio / notifications.

Idempotent guard; name-agnostic downgrade.

Revision ID: ip2b3c4d5e6f
Revises: ip1a2b3c4d5e
Create Date: 2026-06-10 09:00:01.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ip2b3c4d5e6f"
down_revision: str | None = "ip1a2b3c4d5e"
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
    if "ip_reviews" in inspector.get_table_names():
        return

    # ip_reviews -------------------------------------------------------------
    op.create_table(
        "ip_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("review_type", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("counterparty", sa.String(255), nullable=True),
        sa.Column("ip_category", sa.String(20), nullable=True),
        sa.Column("classification", sa.String(20), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("result_memo", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_ip_reviews_user_id"
        ),
    )
    op.create_index("ix_ip_reviews_user_id", "ip_reviews", ["user_id"])
    op.create_index("ix_ip_reviews_user_subject", "ip_reviews", ["user_id", "subject"])

    # ip_enforcement ---------------------------------------------------------
    op.create_table(
        "ip_enforcement",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("matter_type", sa.String(20), nullable=False, server_default="cease_desist"),
        sa.Column("mode", sa.String(20), nullable=False, server_default="send"),
        sa.Column("counterparty", sa.String(255), nullable=True),
        sa.Column("right_at_issue", sa.Text(), nullable=True),
        sa.Column("infringement_facts", sa.Text(), nullable=True),
        sa.Column("due_diligence", sa.Text(), nullable=True),
        sa.Column("response_deadline", sa.Date(), nullable=True),
        sa.Column("letter_draft", sa.Text(), nullable=True),
        sa.Column("outbound_letter", sa.Text(), nullable=True),
        sa.Column("send_gate", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="intake"),
        sa.Column("escalation_flag", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("escalation_reason", sa.Text(), nullable=True),
        sa.Column("log", sa.Text(), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_ip_enforcement_user_id"
        ),
    )
    op.create_index("ix_ip_enforcement_user_id", "ip_enforcement", ["user_id"])

    # ip_portfolio -----------------------------------------------------------
    op.create_table(
        "ip_portfolio",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("asset_type", sa.String(30), nullable=False, server_default="trademark"),
        sa.Column("jurisdiction", sa.String(60), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("owner_entity", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="registered"),
        sa.Column("application_number", sa.String(120), nullable=True),
        sa.Column("registration_number", sa.String(120), nullable=True),
        sa.Column("filing_date", sa.Date(), nullable=True),
        sa.Column("registration_date", sa.Date(), nullable=True),
        sa.Column("grant_date", sa.Date(), nullable=True),
        sa.Column("priority_date", sa.Date(), nullable=True),
        sa.Column("next_deadlines", sa.Text(), nullable=True),
        sa.Column("business_owner", sa.String(255), nullable=True),
        sa.Column("agent_managed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(30), nullable=False, server_default="manual"),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_ip_portfolio_user_id"
        ),
    )
    op.create_index("ix_ip_portfolio_user_id", "ip_portfolio", ["user_id"])
    op.create_index("ix_ip_portfolio_user_type", "ip_portfolio", ["user_id", "asset_type"])

    # ip_notifications -------------------------------------------------------
    op.create_table(
        "ip_notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(50), nullable=False, server_default="renewal_alert"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("action_url", sa.String(500), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_ip_notifications_user_id"
        ),
    )
    op.create_index("ix_ip_notifications_user_id", "ip_notifications", ["user_id"])


def downgrade() -> None:
    op.drop_table("ip_notifications")
    op.drop_table("ip_portfolio")
    op.drop_table("ip_enforcement")
    op.drop_table("ip_reviews")
