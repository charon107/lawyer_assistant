"""add privacy-legal core tables

Second slice: reviews / dsar / notifications.

Idempotent guard; name-agnostic downgrade.

Revision ID: prv2b3c4d5e6
Revises: prv1a2b3c4d5
Create Date: 2026-06-07 09:00:01.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "prv2b3c4d5e6"
down_revision: str | None = "prv1a2b3c4d5"
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
    if "privacy_reviews" in inspector.get_table_names():
        return

    # privacy_reviews --------------------------------------------------------
    op.create_table(
        "privacy_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("review_type", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("counterparty", sa.String(255), nullable=True),
        sa.Column("direction", sa.String(20), nullable=True),
        sa.Column("classification", sa.String(20), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("recommendation", sa.String(30), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("result_memo", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_privacy_reviews_user_id"
        ),
    )
    op.create_index("ix_privacy_reviews_user_id", "privacy_reviews", ["user_id"])
    op.create_index("ix_privacy_reviews_user_subject", "privacy_reviews", ["user_id", "subject"])

    # privacy_dsar -----------------------------------------------------------
    op.create_table(
        "privacy_dsar",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("request_types", sa.Text(), nullable=True),
        sa.Column("data_subject_ref", sa.String(120), nullable=True),
        sa.Column("date_received", sa.Date(), nullable=True),
        sa.Column("date_verified", sa.Date(), nullable=True),
        sa.Column("date_responded", sa.Date(), nullable=True),
        sa.Column("response_deadline", sa.Date(), nullable=True),
        sa.Column("identity_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("verification_method", sa.String(120), nullable=True),
        sa.Column("systems_checked", sa.Text(), nullable=True),
        sa.Column("exemptions", sa.Text(), nullable=True),
        sa.Column("ack_letter", sa.Text(), nullable=True),
        sa.Column("response_letter", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="received"),
        sa.Column("escalation_flag", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("escalation_reason", sa.Text(), nullable=True),
        sa.Column("log", sa.Text(), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_privacy_dsar_user_id"
        ),
    )
    op.create_index("ix_privacy_dsar_user_id", "privacy_dsar", ["user_id"])

    # privacy_notifications --------------------------------------------------
    op.create_table(
        "privacy_notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(50), nullable=False, server_default="policy_sweep_reminder"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("action_url", sa.String(500), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_privacy_notifications_user_id"
        ),
    )
    op.create_index("ix_privacy_notifications_user_id", "privacy_notifications", ["user_id"])


def downgrade() -> None:
    op.drop_table("privacy_notifications")
    op.drop_table("privacy_dsar")
    op.drop_table("privacy_reviews")
