"""add employment-legal employment_profiles table

First slice of the employment-legal (劳动用工) module data layer: the
per-user practice profile (CLAUDE.md equivalent). `module_configs` already
exists and is reused via its `module_name` discriminator.

Idempotent guard (create_all + Alembic run in tandem); downgrade is
name-agnostic.

Revision ID: f1a2b3c4d5e6
Revises: c58189a7c364
Create Date: 2026-06-03 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: str | None = "c58189a7c364"
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
    if "employment_profiles" in inspector.get_table_names():
        return

    op.create_table(
        "employment_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("jurisdictions", sa.Text(), nullable=True),
        sa.Column("default_jurisdiction", sa.String(100), nullable=True),
        sa.Column("office_model", sa.String(20), nullable=False, server_default="in_office"),
        sa.Column("user_role", sa.String(40), nullable=False, server_default="attorney"),
        sa.Column("lawyer_contact", sa.String(255), nullable=True),
        sa.Column("hiring_trigger", sa.Text(), nullable=True),
        sa.Column("termination_trigger", sa.Text(), nullable=True),
        sa.Column("standard_severance", sa.String(40), nullable=True),
        sa.Column("high_risk_flags", sa.Text(), nullable=True),
        sa.Column("policy_location", sa.String(255), nullable=True),
        sa.Column("provincial_supplements", sa.Text(), nullable=True),
        sa.Column("jurisdiction_table", sa.Text(), nullable=True),
        sa.Column("leave_management_config", sa.Text(), nullable=True),
        sa.Column("escalation_matrix", sa.Text(), nullable=True),
        sa.Column("setup_depth", sa.String(20), nullable=False, server_default="full"),
        sa.Column("setup_status", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("setup_progress", sa.Text(), nullable=True),
        sa.Column("profile_content", sa.Text(), nullable=True),
        sa.Column("alert_channel", sa.String(50), nullable=True),
        sa.Column("output_destination", sa.String(50), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_employment_profiles_user_id"
        ),
        sa.UniqueConstraint("user_id", name="uq_employment_profiles_user_id"),
    )
    op.create_index("ix_employment_profiles_user_id", "employment_profiles", ["user_id"])


def downgrade() -> None:
    op.drop_table("employment_profiles")
