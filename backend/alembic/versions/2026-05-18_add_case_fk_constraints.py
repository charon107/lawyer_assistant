"""add case FK constraints and rename table

Revision ID: fb1e5e73ee3a
Revises: 51e048db21e3
Create Date: 2026-05-18 21:50:07.177833

"""

from collections.abc import Sequence

from sqlalchemy import inspect

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fb1e5e73ee3a"
down_revision: str | None = "51e048db21e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Rename lpa_cases -> cases (skip if already renamed)
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    if "lpa_cases" in tables:
        op.rename_table("lpa_cases", "cases")

    # Add FK constraints using batch mode (SQLite compatible)
    with op.batch_alter_table("chat_files", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "chat_files_case_id_fkey", "cases", ["case_id"], ["id"], ondelete="CASCADE"
        )

    with op.batch_alter_table("conversations", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "conversations_case_id_fkey", "cases", ["case_id"], ["id"], ondelete="CASCADE"
        )


def downgrade() -> None:
    with op.batch_alter_table("conversations", schema=None) as batch_op:
        batch_op.drop_constraint("conversations_case_id_fkey", type_="foreignkey")

    with op.batch_alter_table("chat_files", schema=None) as batch_op:
        batch_op.drop_constraint("chat_files_case_id_fkey", type_="foreignkey")

    # Rename cases -> lpa_cases (skip if already renamed)
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    if "cases" in tables:
        op.rename_table("cases", "lpa_cases")
