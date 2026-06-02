"""add commercial-legal phase A tables

Adds the 3 tables needed for Phase A of the commercial-legal module:

- commercial_profiles: per-user practice profile (CLAUDE.md equivalent)
- contract_reviews:    one row per vendor-agreement-review run
- module_configs:      generic per-user, per-module cold-start state

Tables for Phase B (commercial_matters, renewal_registrations,
contract_deviations, playbook_proposals) are intentionally NOT
created here. They will arrive in a later migration.

Old LPA / cases tables are NOT dropped here either; Phase C handles
that.

Revision ID: c0a1b2c3d4e5
Revises: 9f8e7d6c5b4a
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c0a1b2c3d4e5"
down_revision: str | None = "9f8e7d6c5b4a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Skip if tables already exist (may have been created by create_all in dev)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "commercial_profiles" in inspector.get_table_names():
        return
    # commercial_profiles -----------------------------------------------------
    op.create_table(
        "commercial_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("team_size", sa.String(50), nullable=True),
        sa.Column("gc_name", sa.String(255), nullable=True),
        sa.Column("monthly_volume", sa.String(50), nullable=True),
        sa.Column("side", sa.String(20), nullable=False, server_default="purchasing"),
        sa.Column(
            "setup_status",
            sa.String(20),
            nullable=False,
            server_default="not_started",
        ),
        sa.Column("setup_progress", sa.Text(), nullable=True),
        sa.Column("profile_content", sa.Text(), nullable=True),
        sa.Column("playbook_sales", sa.Text(), nullable=True),
        sa.Column("playbook_purchasing", sa.Text(), nullable=True),
        sa.Column("escalation_matrix", sa.Text(), nullable=True),
        sa.Column("renewal_alert_channel", sa.String(50), nullable=True),
        sa.Column("output_destination", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_commercial_profiles_user_id",
        ),
        sa.UniqueConstraint("user_id", name="uq_commercial_profiles_user_id"),
    )
    op.create_index(
        "ix_commercial_profiles_user_id",
        "commercial_profiles",
        ["user_id"],
    )

    # contract_reviews --------------------------------------------------------
    op.create_table(
        "contract_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        # matter_id is plain nullable text now; FK added in Phase B.
        sa.Column("matter_id", sa.String(36), nullable=True),
        sa.Column("review_type", sa.String(20), nullable=False),
        sa.Column("counterparty", sa.String(255), nullable=True),
        sa.Column("agreement_name", sa.String(255), nullable=True),
        sa.Column("agreement_type", sa.String(50), nullable=True),
        sa.Column("side", sa.String(20), nullable=False, server_default="purchasing"),
        sa.Column("annual_value", sa.Float(), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("result_status", sa.String(20), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("result_memo", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("stakeholder_summary", sa.Text(), nullable=True),
        sa.Column("required_approver", sa.String(255), nullable=True),
        sa.Column(
            "escalation_sent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_contract_reviews_user_id",
        ),
    )
    op.create_index("ix_contract_reviews_user_id", "contract_reviews", ["user_id"])
    op.create_index("ix_contract_reviews_matter_id", "contract_reviews", ["matter_id"])

    # module_configs ----------------------------------------------------------
    op.create_table(
        "module_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("module_name", sa.String(50), nullable=False),
        sa.Column(
            "setup_status",
            sa.String(20),
            nullable=False,
            server_default="not_started",
        ),
        sa.Column("setup_data", sa.Text(), nullable=True),
        sa.Column("config_content", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_module_configs_user_id",
        ),
        sa.UniqueConstraint(
            "user_id",
            "module_name",
            name="uq_module_configs_user_module",
        ),
    )
    op.create_index("ix_module_configs_user_id", "module_configs", ["user_id"])
    op.create_index("ix_module_configs_module_name", "module_configs", ["module_name"])


def downgrade() -> None:
    # drop_table drops the table's indexes automatically (SQLite); explicit
    # drop_index is omitted to stay name-agnostic between create_all (*_idx)
    # and migration-created (ix_*) databases.
    op.drop_table("module_configs")
    op.drop_table("contract_reviews")
    op.drop_table("commercial_profiles")
