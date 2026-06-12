"""add litigation-legal litigation_profiles table

First slice of the litigation-legal (争议解决) module data layer: the per-user
practice profile (CLAUDE.md equivalent). `module_configs` already exists and
is reused via its `module_name` discriminator.

Idempotent guard (create_all + Alembic run in tandem); downgrade is
name-agnostic.

Revision ID: lit1a2b3c4d5e
Revises: ip2b3c4d5e6f
Create Date: 2026-06-12 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "lit1a2b3c4d5e"
down_revision: str | None = "ip2b3c4d5e6f"
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
    if "litigation_profiles" in inspector.get_table_names():
        return

    op.create_table(
        "litigation_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        # 公司画像 (JSON text columns)
        sa.Column("company_context", sa.Text(), nullable=True),
        sa.Column("key_contacts", sa.Text(), nullable=True),
        # 使用者 / 执业角色 / 当事人角色
        sa.Column("user_role", sa.String(40), nullable=False, server_default="lawyer"),
        sa.Column("lawyer_contact", sa.String(255), nullable=True),
        sa.Column("practice_role", sa.String(20), nullable=False, server_default="企业法务"),
        sa.Column("party_role", sa.String(20), nullable=False, server_default="依案件而定"),
        # 集成 / 风险校准 / 争议画像 / 文书风格 (JSON text)
        sa.Column("integrations", sa.Text(), nullable=True),
        sa.Column("risk_calibration", sa.Text(), nullable=True),
        sa.Column("dispute_profile", sa.Text(), nullable=True),
        sa.Column("doc_style", sa.Text(), nullable=True),
        # 输出与表面 (JSON text)
        sa.Column("output_config", sa.Text(), nullable=True),
        # 状态
        sa.Column("setup_depth", sa.String(20), nullable=False, server_default="full"),
        sa.Column("setup_status", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("setup_progress", sa.Text(), nullable=True),
        sa.Column("profile_content", sa.Text(), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_litigation_profiles_user_id"
        ),
        sa.UniqueConstraint("user_id", name="uq_litigation_profiles_user_id"),
    )
    op.create_index("ix_litigation_profiles_user_id", "litigation_profiles", ["user_id"])


def downgrade() -> None:
    op.drop_table("litigation_profiles")
