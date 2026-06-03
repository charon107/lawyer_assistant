"""add employment-legal internal-investigation tables

Third slice: structured investigation (matter header + log entries +
sources checklist + evidentiary gaps).

Idempotent guard; name-agnostic downgrade (children dropped before parent).

Revision ID: f3c4d5e6f7a8
Revises: f2b3c4d5e6f7
Create Date: 2026-06-03 09:00:02.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f3c4d5e6f7a8"
down_revision: str | None = "f2b3c4d5e6f7"
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
    if "employment_investigations" in inspector.get_table_names():
        return

    op.create_table(
        "employment_investigations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("investigation_name", sa.String(255), nullable=False),
        sa.Column("allegation", sa.Text(), nullable=True),
        sa.Column("investigation_type", sa.String(40), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("attorney_directed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("privilege_note", sa.Text(), nullable=True),
        sa.Column("memo", sa.Text(), nullable=True),
        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_employment_investigations_user_id",
        ),
        sa.UniqueConstraint(
            "user_id", "investigation_name", name="uq_employment_investigations_user_name"
        ),
    )
    op.create_index(
        "ix_employment_investigations_user_id", "employment_investigations", ["user_id"]
    )

    op.create_table(
        "investigation_log_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("investigation_id", sa.String(36), nullable=False),
        sa.Column("entry_seq", sa.Integer(), nullable=False),
        sa.Column("entry_type", sa.String(30), nullable=True),
        sa.Column("date_of_event", sa.Date(), nullable=True),
        sa.Column("source", sa.String(500), nullable=True),
        sa.Column("source_type", sa.String(40), nullable=True),
        sa.Column("issues", sa.Text(), nullable=True),
        sa.Column("significance", sa.String(20), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.Column("contradicts_entry_seq", sa.Integer(), nullable=True),
        sa.Column("corroborates_entry_seq", sa.Integer(), nullable=True),
        sa.Column("pull_criterion", sa.String(255), nullable=True),
        sa.Column("privilege", sa.String(60), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["investigation_id"],
            ["employment_investigations.id"],
            ondelete="CASCADE",
            name="fk_investigation_log_entries_investigation_id",
        ),
    )
    op.create_index(
        "ix_investigation_log_entries_investigation_id",
        "investigation_log_entries",
        ["investigation_id"],
    )

    op.create_table(
        "investigation_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("investigation_id", sa.String(36), nullable=False),
        sa.Column("source_seq", sa.Integer(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("notes", sa.Text(), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["investigation_id"],
            ["employment_investigations.id"],
            ondelete="CASCADE",
            name="fk_investigation_sources_investigation_id",
        ),
    )
    op.create_index(
        "ix_investigation_sources_investigation_id",
        "investigation_sources",
        ["investigation_id"],
    )

    op.create_table(
        "investigation_gaps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("investigation_id", sa.String(36), nullable=False),
        sa.Column("gap_seq", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("identified_from", sa.String(500), nullable=True),
        sa.Column("source_to_obtain", sa.String(500), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["investigation_id"],
            ["employment_investigations.id"],
            ondelete="CASCADE",
            name="fk_investigation_gaps_investigation_id",
        ),
    )
    op.create_index(
        "ix_investigation_gaps_investigation_id", "investigation_gaps", ["investigation_id"]
    )


def downgrade() -> None:
    op.drop_table("investigation_gaps")
    op.drop_table("investigation_sources")
    op.drop_table("investigation_log_entries")
    op.drop_table("employment_investigations")
