"""drop LPA tables and case_id columns (C4 deprecation)

Drops the LPA (Legal Process Automation) schema: the ``cases`` and
``document_analyses`` tables, the stray ``lpa_cases`` leftover, and the
``case_id`` foreign-key columns on ``conversations`` and ``chat_files``.

Both ``cases`` and ``document_analyses`` are empty in production, so this is
non-destructive with respect to data. The downgrade recreates the tables and
columns (final pre-drop schema) but cannot restore data.

Revision ID: f3d4e5f6a7b8
Revises: e2c3d4e5f6a7
Create Date: 2026-06-01 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3d4e5f6a7b8"
down_revision: str | None = "e2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": name},
    )
    return result.first() is not None


def _index_exists(name: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='index' AND name=:name"),
        {"name": name},
    )
    return result.first() is not None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(sa.text(f"PRAGMA table_info({table})"))
    return column in [row[1] for row in result]


def upgrade() -> None:
    # 1. Drop case_id from conversations (batch mode recreates the table without
    #    the column and its FK to cases). Drop its index first if present.
    if _index_exists("conversations_case_id_idx"):
        op.drop_index("conversations_case_id_idx", table_name="conversations")
    if _column_exists("conversations", "case_id"):
        with op.batch_alter_table("conversations", schema=None) as batch_op:
            batch_op.drop_column("case_id")

    # 2. Drop case_id from chat_files (keep the unrelated `summary` column).
    if _index_exists("chat_files_case_id_idx"):
        op.drop_index("chat_files_case_id_idx", table_name="chat_files")
    if _column_exists("chat_files", "case_id"):
        with op.batch_alter_table("chat_files", schema=None) as batch_op:
            batch_op.drop_column("case_id")

    # 3. Drop dependent table first, then the parent case tables.
    if _table_exists("document_analyses"):
        op.drop_table("document_analyses")
    if _table_exists("cases"):
        op.drop_table("cases")
    # Stray leftover from the historical lpa_cases -> cases rename.
    if _table_exists("lpa_cases"):
        op.drop_table("lpa_cases")


def downgrade() -> None:
    # Recreate the `cases` table (final schema, including document_type).
    if not _table_exists("cases"):
        op.create_table(
            "cases",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column(
                "document_type",
                sa.String(length=50),
                nullable=False,
                server_default="lpa",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["user_id"], ["users.id"], name="lpa_cases_user_id_fkey", ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id", name="lpa_cases_pkey"),
        )
    if not _index_exists("lpa_cases_user_id_idx"):
        op.create_index("lpa_cases_user_id_idx", "cases", ["user_id"], unique=False)

    # Recreate the `document_analyses` table.
    if not _table_exists("document_analyses"):
        op.create_table(
            "document_analyses",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("chat_file_id", sa.String(length=36), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("analysis_json", sa.Text(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["chat_file_id"], ["chat_files.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("chat_file_id"),
        )

    # Re-add case_id columns with FK + index.
    if not _column_exists("chat_files", "case_id"):
        with op.batch_alter_table("chat_files", schema=None) as batch_op:
            batch_op.add_column(sa.Column("case_id", sa.String(length=36), nullable=True))
            batch_op.create_foreign_key(
                "chat_files_case_id_fkey", "cases", ["case_id"], ["id"], ondelete="CASCADE"
            )
    if not _index_exists("chat_files_case_id_idx"):
        op.create_index("chat_files_case_id_idx", "chat_files", ["case_id"], unique=False)

    if not _column_exists("conversations", "case_id"):
        with op.batch_alter_table("conversations", schema=None) as batch_op:
            batch_op.add_column(sa.Column("case_id", sa.String(length=36), nullable=True))
            batch_op.create_foreign_key(
                "conversations_case_id_fkey", "cases", ["case_id"], ["id"], ondelete="CASCADE"
            )
    if not _index_exists("conversations_case_id_idx"):
        op.create_index("conversations_case_id_idx", "conversations", ["case_id"], unique=False)
