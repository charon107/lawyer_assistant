"""add corporate-legal corporate_profiles table

First slice of the corporate-legal (公司并购) module data layer: the
per-user modular practice profile (CLAUDE.md equivalent). The remaining
M&A-core tables (corporate_deals, vdr_documents, diligence_issues,
tabular_reviews, closing_checklist_items, material_contract_items) arrive
in a later migration.

`module_configs` already exists (created by the commercial Phase A
migration) and is reused for corporate-legal cold-start state via its
`module_name` discriminator — not recreated here.

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-06-02 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: str | None = "a2b3c4d5e6f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Skip if the table already exists (may have been created by create_all
    # in dev — the project runs create_all and Alembic in tandem).
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "corporate_profiles" in inspector.get_table_names():
        return

    op.create_table(
        "corporate_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("stage", sa.String(50), nullable=True),
        sa.Column("main_jurisdiction", sa.String(255), nullable=True),
        sa.Column("team_size", sa.String(50), nullable=True),
        sa.Column("escalation_path", sa.String(255), nullable=True),
        sa.Column("used_by", sa.String(20), nullable=False, server_default="lawyer"),
        sa.Column("setup_depth", sa.String(20), nullable=False, server_default="full"),
        sa.Column(
            "setup_status",
            sa.String(20),
            nullable=False,
            server_default="not_started",
        ),
        sa.Column("setup_progress", sa.Text(), nullable=True),
        sa.Column("active_modules", sa.Text(), nullable=True),
        sa.Column("mna_config", sa.Text(), nullable=True),
        sa.Column("board_config", sa.Text(), nullable=True),
        sa.Column("public_config", sa.Text(), nullable=True),
        sa.Column("entity_config", sa.Text(), nullable=True),
        sa.Column("profile_content", sa.Text(), nullable=True),
        sa.Column("alert_channel", sa.String(50), nullable=True),
        sa.Column("output_destination", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_corporate_profiles_user_id",
        ),
        sa.UniqueConstraint("user_id", name="uq_corporate_profiles_user_id"),
    )
    op.create_index(
        "ix_corporate_profiles_user_id",
        "corporate_profiles",
        ["user_id"],
    )


def downgrade() -> None:
    # drop_table drops the table's indexes automatically (SQLite); explicit
    # drop_index is omitted to stay name-agnostic between create_all (*_idx)
    # and migration-created (ix_*) databases.
    op.drop_table("corporate_profiles")
