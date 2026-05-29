"""add commercial-legal phase B tables

Adds the 4 tables needed for Phase B of the commercial-legal module:

- commercial_matters:      one counterparty relationship per row
- renewal_registrations:   term basics + computed cancellation deadlines
- contract_deviations:     one persisted clause deviation per row
- playbook_proposals:      suggested playbook updates awaiting a decision

Also upgrades `contract_reviews.matter_id` from a plain nullable string
into a real ForeignKey to `commercial_matters.id` (ON DELETE SET NULL),
using batch mode for SQLite compatibility.

No tables are dropped here. Old LPA / cases tables are retired in Phase C.

Revision ID: d1b2c3d4e5f6
Revises: c0a1b2c3d4e5
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1b2c3d4e5f6"
down_revision: str | None = "c0a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # commercial_matters ------------------------------------------------------
    op.create_table(
        "commercial_matters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("counterparty", sa.String(255), nullable=True),
        sa.Column("matter_name", sa.String(255), nullable=True),
        sa.Column("agreement_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
            name="fk_commercial_matters_user_id",
        ),
    )
    op.create_index("ix_commercial_matters_user_id", "commercial_matters", ["user_id"])

    # renewal_registrations ---------------------------------------------------
    op.create_table(
        "renewal_registrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("matter_id", sa.String(36), nullable=True),
        sa.Column("counterparty", sa.String(255), nullable=True),
        sa.Column("agreement_name", sa.String(255), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("term_months", sa.Integer(), nullable=False, server_default=sa.text("12")),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("notice_days", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("cancel_by_calendar", sa.Date(), nullable=True),
        sa.Column("cancel_by_effective", sa.Date(), nullable=True),
        sa.Column("send_by_effective", sa.Date(), nullable=True),
        sa.Column("decision", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text(), nullable=True),
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
            name="fk_renewal_registrations_user_id",
        ),
        sa.ForeignKeyConstraint(
            ["matter_id"],
            ["commercial_matters.id"],
            ondelete="CASCADE",
            name="fk_renewal_registrations_matter_id",
        ),
    )
    op.create_index("ix_renewal_registrations_user_id", "renewal_registrations", ["user_id"])
    op.create_index("ix_renewal_registrations_matter_id", "renewal_registrations", ["matter_id"])

    # contract_deviations -----------------------------------------------------
    op.create_table(
        "contract_deviations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("review_id", sa.String(36), nullable=False),
        sa.Column("clause_key", sa.String(80), nullable=False),
        sa.Column("clause_label", sa.String(120), nullable=True),
        sa.Column("playbook_position", sa.Text(), nullable=True),
        sa.Column("signed_position", sa.Text(), nullable=True),
        sa.Column("severity_legal", sa.String(10), nullable=False, server_default="green"),
        sa.Column("severity_commercial", sa.String(10), nullable=False, server_default="green"),
        sa.Column("category", sa.String(40), nullable=True),
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
            name="fk_contract_deviations_user_id",
        ),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["contract_reviews.id"],
            ondelete="CASCADE",
            name="fk_contract_deviations_review_id",
        ),
    )
    op.create_index("ix_contract_deviations_user_id", "contract_deviations", ["user_id"])
    op.create_index("ix_contract_deviations_review_id", "contract_deviations", ["review_id"])
    op.create_index("ix_contract_deviations_clause_key", "contract_deviations", ["clause_key"])

    # playbook_proposals ------------------------------------------------------
    op.create_table(
        "playbook_proposals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("clause_key", sa.String(80), nullable=False),
        sa.Column("clause_label", sa.String(120), nullable=True),
        sa.Column("current_position", sa.Text(), nullable=True),
        sa.Column("proposed_position", sa.Text(), nullable=True),
        sa.Column("deviation_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("rationale", sa.Text(), nullable=True),
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
            name="fk_playbook_proposals_user_id",
        ),
    )
    op.create_index("ix_playbook_proposals_user_id", "playbook_proposals", ["user_id"])
    op.create_index("ix_playbook_proposals_clause_key", "playbook_proposals", ["clause_key"])

    # contract_reviews.matter_id -> commercial_matters.id (FK, SET NULL) ------
    # SQLite cannot ALTER a column to add a constraint in place, so batch mode
    # rebuilds the table and copies the existing index across.
    with op.batch_alter_table("contract_reviews", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_contract_reviews_matter_id",
            "commercial_matters",
            ["matter_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("contract_reviews", schema=None) as batch_op:
        batch_op.drop_constraint("fk_contract_reviews_matter_id", type_="foreignkey")

    op.drop_index("ix_playbook_proposals_clause_key", table_name="playbook_proposals")
    op.drop_index("ix_playbook_proposals_user_id", table_name="playbook_proposals")
    op.drop_table("playbook_proposals")

    op.drop_index("ix_contract_deviations_clause_key", table_name="contract_deviations")
    op.drop_index("ix_contract_deviations_review_id", table_name="contract_deviations")
    op.drop_index("ix_contract_deviations_user_id", table_name="contract_deviations")
    op.drop_table("contract_deviations")

    op.drop_index("ix_renewal_registrations_matter_id", table_name="renewal_registrations")
    op.drop_index("ix_renewal_registrations_user_id", table_name="renewal_registrations")
    op.drop_table("renewal_registrations")

    op.drop_index("ix_commercial_matters_user_id", table_name="commercial_matters")
    op.drop_table("commercial_matters")
