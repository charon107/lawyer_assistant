"""add regulatory-legal regulatory_profiles table

First slice of the regulatory-legal (监管合规) module data layer: the per-user
practice profile (CLAUDE.md equivalent). `module_configs` already exists and is
reused via its `module_name` discriminator.

Idempotent guard (create_all + Alembic run in tandem); downgrade is
name-agnostic.

Revision ID: reg1a2b3c4d5e
Revises: lit2b3c4d5e6f
Create Date: 2026-06-13 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "reg1a2b3c4d5e"
down_revision: str | None = "lit2b3c4d5e6f"
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
    if "regulatory_profiles" in inspector.get_table_names():
        return

    op.create_table(
        "regulatory_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        # 公司画像 (JSON text)
        sa.Column("company_context", sa.Text(), nullable=True),
        # 使用者 / 执业设置
        sa.Column("user_role", sa.String(40), nullable=False, server_default="lawyer"),
        sa.Column("lawyer_contact", sa.String(255), nullable=True),
        sa.Column("practice_setting", sa.String(20), nullable=False, server_default="法务内部"),
        # 监测清单 / 政策库索引 / 重要度阈值 / 动态源配置 / 差距响应流程 (JSON text)
        sa.Column("watchlist", sa.Text(), nullable=True),
        sa.Column("policy_library", sa.Text(), nullable=True),
        sa.Column("materiality_threshold", sa.Text(), nullable=True),
        sa.Column("feed_config", sa.Text(), nullable=True),
        sa.Column("gap_response", sa.Text(), nullable=True),
        # 集成 / 输出与表面 (JSON text)
        sa.Column("integrations", sa.Text(), nullable=True),
        sa.Column("output_config", sa.Text(), nullable=True),
        # 监测状态
        sa.Column("last_feed_check_at", sa.DateTime(timezone=True), nullable=True),
        # 状态
        sa.Column("setup_depth", sa.String(20), nullable=False, server_default="full"),
        sa.Column("setup_status", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("setup_progress", sa.Text(), nullable=True),
        sa.Column("profile_content", sa.Text(), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_regulatory_profiles_user_id"
        ),
        sa.UniqueConstraint("user_id", name="uq_regulatory_profiles_user_id"),
    )
    op.create_index("ix_regulatory_profiles_user_id", "regulatory_profiles", ["user_id"])


def downgrade() -> None:
    op.drop_table("regulatory_profiles")
