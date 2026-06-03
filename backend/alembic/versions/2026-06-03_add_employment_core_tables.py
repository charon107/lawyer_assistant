"""add employment-legal core tables

Second slice: reviews / leaves / expansions / notifications. Internal
investigation tables arrive in the next migration.

Idempotent guard; name-agnostic downgrade.

Revision ID: f2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-06-03 09:00:01.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f2b3c4d5e6f7"
down_revision: str | None = "f1a2b3c4d5e6"
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
    if "employment_reviews" in inspector.get_table_names():
        return

    # employment_reviews -----------------------------------------------------
    op.create_table(
        "employment_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("review_type", sa.String(40), nullable=False),
        sa.Column("employee_name", sa.String(255), nullable=True),
        sa.Column("position", sa.String(255), nullable=True),
        sa.Column("jurisdiction", sa.String(100), nullable=True),
        sa.Column("input_description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("result_status", sa.String(20), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("result_memo", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("high_risk_flags", sa.Text(), nullable=True),
        sa.Column("required_approver", sa.String(255), nullable=True),
        sa.Column("escalation_sent", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_employment_reviews_user_id"
        ),
    )
    op.create_index("ix_employment_reviews_user_id", "employment_reviews", ["user_id"])

    # leave_registrations ----------------------------------------------------
    op.create_table(
        "leave_registrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("employee_id", sa.String(100), nullable=True),
        sa.Column("employee_name", sa.String(255), nullable=True),
        sa.Column("position", sa.String(255), nullable=True),
        sa.Column("jurisdiction", sa.String(100), nullable=False),
        sa.Column("leave_type", sa.String(40), nullable=False),
        sa.Column("leave_start", sa.Date(), nullable=False),
        sa.Column("expected_return", sa.Date(), nullable=True),
        sa.Column("intermittent", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("accumulated_work_years", sa.Integer(), nullable=True),
        sa.Column("company_work_years", sa.Integer(), nullable=True),
        sa.Column("normal_schedule", sa.String(100), nullable=True),
        sa.Column("leave_approved", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("leave_approval_date", sa.Date(), nullable=True),
        sa.Column(
            "medical_certificate_received",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("entitlement", sa.Text(), nullable=True),
        sa.Column("time_used", sa.Text(), nullable=True),
        sa.Column("medical_period_end", sa.Date(), nullable=True),
        sa.Column("maternity_return_date", sa.Date(), nullable=True),
        sa.Column("work_injury_period_end", sa.Date(), nullable=True),
        sa.Column("annual_carryover_deadline", sa.Date(), nullable=True),
        sa.Column("social_insurance_status", sa.String(100), nullable=True),
        sa.Column("labor_capacity_assessment", sa.String(40), nullable=True),
        sa.Column(
            "return_to_work_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("annual_leave_carryover", sa.String(40), nullable=True),
        sa.Column("unpaid_leave_compensation", sa.String(40), nullable=True),
        sa.Column("controlling_sources", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("last_updated", sa.Date(), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_leave_registrations_user_id"
        ),
    )
    op.create_index("ix_leave_registrations_user_id", "leave_registrations", ["user_id"])

    # employment_expansions --------------------------------------------------
    op.create_table(
        "employment_expansions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("province", sa.String(100), nullable=False),
        sa.Column("headcount", sa.String(100), nullable=True),
        sa.Column("position_types", sa.Text(), nullable=True),
        sa.Column("expected_timeline", sa.String(255), nullable=True),
        sa.Column("employment_structure", sa.String(40), nullable=True),
        sa.Column("analysis_result", sa.Text(), nullable=True),
        sa.Column("tracking_items", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_employment_expansions_user_id"
        ),
        sa.UniqueConstraint("user_id", "slug", name="uq_employment_expansions_user_slug"),
    )
    op.create_index("ix_employment_expansions_user_id", "employment_expansions", ["user_id"])
    op.create_index("ix_employment_expansions_slug", "employment_expansions", ["slug"])

    # employment_notifications -----------------------------------------------
    op.create_table(
        "employment_notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(50), nullable=False, server_default="leave_tracker"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("action_url", sa.String(500), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_employment_notifications_user_id",
        ),
    )
    op.create_index("ix_employment_notifications_user_id", "employment_notifications", ["user_id"])


def downgrade() -> None:
    op.drop_table("employment_notifications")
    op.drop_table("employment_expansions")
    op.drop_table("leave_registrations")
    op.drop_table("employment_reviews")
