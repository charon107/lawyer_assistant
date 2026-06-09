"""add privacy-legal privacy_profiles table

First slice of the privacy-legal (个人信息保护) module data layer: the
per-user practice profile (CLAUDE.md equivalent). `module_configs` already
exists and is reused via its `module_name` discriminator.

Idempotent guard (create_all + Alembic run in tandem); downgrade is
name-agnostic.

Revision ID: prv1a2b3c4d5
Revises: f3c4d5e6f7a8
Create Date: 2026-06-07 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "prv1a2b3c4d5"
down_revision: str | None = "f3c4d5e6f7a8"
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
    if "privacy_profiles" in inspector.get_table_names():
        return

    op.create_table(
        "privacy_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("regulatory_footprint", sa.Text(), nullable=True),
        sa.Column("data_residency", sa.String(255), nullable=True),
        sa.Column("dpo_info", sa.String(255), nullable=True),
        sa.Column("open_reg_matters", sa.Text(), nullable=True),
        sa.Column("user_role", sa.String(40), nullable=False, server_default="attorney"),
        sa.Column("lawyer_contact", sa.String(255), nullable=True),
        sa.Column("practice_setting", sa.String(60), nullable=True),
        sa.Column("integrations", sa.Text(), nullable=True),
        sa.Column("dpa_playbook", sa.Text(), nullable=True),
        sa.Column("policy_commitments", sa.Text(), nullable=True),
        sa.Column("pia_house_style", sa.Text(), nullable=True),
        sa.Column("dsar_process", sa.Text(), nullable=True),
        sa.Column("escalation_matrix", sa.Text(), nullable=True),
        sa.Column("seed_docs", sa.Text(), nullable=True),
        sa.Column("output_config", sa.Text(), nullable=True),
        sa.Column("setup_depth", sa.String(20), nullable=False, server_default="full"),
        sa.Column("setup_status", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("setup_progress", sa.Text(), nullable=True),
        sa.Column("profile_content", sa.Text(), nullable=True),
        sa.Column("alert_channel", sa.String(50), nullable=True),
        sa.Column("output_destination", sa.String(50), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_privacy_profiles_user_id"
        ),
        sa.UniqueConstraint("user_id", name="uq_privacy_profiles_user_id"),
    )
    op.create_index("ix_privacy_profiles_user_id", "privacy_profiles", ["user_id"])


def downgrade() -> None:
    op.drop_table("privacy_profiles")
