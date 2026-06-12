"""add litigation-legal core tables

Second slice: matters / matter_events / demands / analyses / notifications.

Idempotent guard (锚点表: litigation_matters); name-agnostic downgrade
(reverse FK order: matter_events before matters).

Revision ID: lit2b3c4d5e6f
Revises: lit1a2b3c4d5e
Create Date: 2026-06-12 09:00:01.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "lit2b3c4d5e6f"
down_revision: str | None = "lit1a2b3c4d5e"
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
    if "litigation_matters" in inspector.get_table_names():
        return

    # litigation_matters ----------------------------------------------------
    op.create_table(
        "litigation_matters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("case_name", sa.String(255), nullable=True),
        sa.Column("case_number", sa.String(120), nullable=True),
        sa.Column("court", sa.String(255), nullable=True),
        sa.Column("cause_of_action", sa.String(255), nullable=True),
        sa.Column("case_type", sa.String(120), nullable=True),
        sa.Column("jurisdiction", sa.String(255), nullable=True),
        sa.Column("our_side", sa.String(20), nullable=True),
        sa.Column("counterparty", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("stage", sa.String(20), nullable=True),
        sa.Column("risk", sa.String(20), nullable=True),
        sa.Column("materiality", sa.String(20), nullable=True),
        sa.Column("exposure_range", sa.String(255), nullable=True),
        sa.Column("filing_date", sa.Date(), nullable=True),
        sa.Column("next_deadline", sa.Date(), nullable=True),
        sa.Column("outside_counsel", sa.Text(), nullable=True),
        sa.Column("internal_owners", sa.Text(), nullable=True),
        sa.Column("conflicts", sa.Text(), nullable=True),
        sa.Column("initial_theory", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(30), nullable=False, server_default="manual"),
        sa.Column("closed_date", sa.Date(), nullable=True),
        sa.Column("outcome", sa.String(255), nullable=True),
        sa.Column("final_cost", sa.String(120), nullable=True),
        sa.Column("lessons", sa.Text(), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_litigation_matters_user_id"
        ),
    )
    op.create_index("ix_litigation_matters_user_id", "litigation_matters", ["user_id"])
    op.create_index(
        "ix_litigation_matters_user_status", "litigation_matters", ["user_id", "status"]
    )
    op.create_index(
        "ix_litigation_matters_user_case_number", "litigation_matters", ["user_id", "case_number"]
    )

    # litigation_matter_events ----------------------------------------------
    op.create_table(
        "litigation_matter_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("matter_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("event_type", sa.String(20), nullable=False, server_default="procedure"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("field_changes", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("deadline_status", sa.String(20), nullable=True),
        sa.Column("associated_files", sa.Text(), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["matter_id"],
            ["litigation_matters.id"],
            ondelete="CASCADE",
            name="fk_matter_events_matter_id",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_matter_events_user_id"
        ),
    )
    op.create_index("ix_matter_events_matter_id", "litigation_matter_events", ["matter_id"])
    op.create_index(
        "ix_matter_events_matter_date", "litigation_matter_events", ["matter_id", "event_date"]
    )

    # litigation_demands ----------------------------------------------------
    op.create_table(
        "litigation_demands",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("matter_id", sa.String(36), nullable=True),
        sa.Column("demand_type", sa.String(30), nullable=False, server_default="other"),
        sa.Column("mode", sa.String(20), nullable=False, server_default="send"),
        sa.Column("counterparty", sa.String(255), nullable=True),
        sa.Column("intake_snapshot", sa.Text(), nullable=True),
        sa.Column("right_or_claim", sa.Text(), nullable=True),
        sa.Column("letter_draft", sa.Text(), nullable=True),
        sa.Column("outbound_letter", sa.Text(), nullable=True),
        sa.Column("pretransmit_checklist", sa.Text(), nullable=True),
        sa.Column("response_deadline", sa.Date(), nullable=True),
        sa.Column("triage_result", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="intake"),
        sa.Column("escalation_flag", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("escalation_reason", sa.Text(), nullable=True),
        sa.Column("sent_date", sa.Date(), nullable=True),
        sa.Column("sent_via", sa.String(20), nullable=True),
        sa.Column("log", sa.Text(), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_litigation_demands_user_id"
        ),
        sa.ForeignKeyConstraint(
            ["matter_id"],
            ["litigation_matters.id"],
            ondelete="SET NULL",
            name="fk_litigation_demands_matter_id",
        ),
    )
    op.create_index("ix_litigation_demands_user_id", "litigation_demands", ["user_id"])

    # litigation_analyses ---------------------------------------------------
    op.create_table(
        "litigation_analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("matter_id", sa.String(36), nullable=True),
        sa.Column("analysis_type", sa.String(30), nullable=False),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("counterparty", sa.String(255), nullable=True),
        sa.Column("classification", sa.String(20), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("result_memo", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_litigation_analyses_user_id"
        ),
        sa.ForeignKeyConstraint(
            ["matter_id"],
            ["litigation_matters.id"],
            ondelete="SET NULL",
            name="fk_litigation_analyses_matter_id",
        ),
    )
    op.create_index("ix_litigation_analyses_user_id", "litigation_analyses", ["user_id"])
    op.create_index(
        "ix_litigation_analyses_user_matter", "litigation_analyses", ["user_id", "matter_id"]
    )
    op.create_index("ix_litigation_analyses_type", "litigation_analyses", ["analysis_type"])

    # litigation_notifications -----------------------------------------------
    op.create_table(
        "litigation_notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column(
            "notification_type", sa.String(50), nullable=False, server_default="docket_alert"
        ),
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
            name="fk_litigation_notifications_user_id",
        ),
    )
    op.create_index("ix_litigation_notifications_user_id", "litigation_notifications", ["user_id"])


def downgrade() -> None:
    # 逆 FK 顺序 drop: 先子表后主表
    op.drop_table("litigation_notifications")
    op.drop_table("litigation_analyses")
    op.drop_table("litigation_demands")
    op.drop_table("litigation_matter_events")
    op.drop_table("litigation_matters")
