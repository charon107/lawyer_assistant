"""add_lpa_cases_and_document_support

Revision ID: e015f3b6544f
Revises: b2c3d4e5f6a7
Create Date: 2026-05-08 05:29:01.916905

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e015f3b6544f"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_exists(table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    result = bind.execute(sa.text(f"PRAGMA table_info({table})"))
    columns = [row[1] for row in result]
    return column in columns


def _index_exists(index_name: str) -> bool:
    """Check if an index exists."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='index' AND name=:name"),
        {"name": index_name},
    )
    return result.first() is not None


def _table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table_name},
    )
    return result.first() is not None


def upgrade() -> None:
    # Create lpa_cases table if not exists
    if not _table_exists("lpa_cases"):
        op.create_table(
            "lpa_cases",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
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
        op.create_index("lpa_cases_user_id_idx", "lpa_cases", ["user_id"], unique=False)

    # Add columns to chat_files if not present
    if not _column_exists("chat_files", "case_id"):
        op.execute("ALTER TABLE chat_files ADD COLUMN case_id VARCHAR(36)")
    if not _column_exists("chat_files", "summary"):
        op.execute("ALTER TABLE chat_files ADD COLUMN summary TEXT")
    if not _index_exists("chat_files_case_id_idx"):
        op.execute("CREATE INDEX chat_files_case_id_idx ON chat_files (case_id)")

    # Add case_id to conversations if not present
    if not _column_exists("conversations", "case_id"):
        op.execute("ALTER TABLE conversations ADD COLUMN case_id VARCHAR(36)")
    if not _index_exists("conversations_case_id_idx"):
        op.execute("CREATE INDEX conversations_case_id_idx ON conversations (case_id)")


def downgrade() -> None:
    op.drop_index("conversations_case_id_idx", table_name="conversations")
    op.drop_index("chat_files_case_id_idx", table_name="chat_files")
    op.drop_index("lpa_cases_user_id_idx", table_name="lpa_cases")
    op.drop_table("lpa_cases")
