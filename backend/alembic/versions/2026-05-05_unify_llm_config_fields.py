"""unify llm config fields

Revision ID: a1b2c3d4e5f6
Revises: bc01a01ab35c
Create Date: 2026-05-05 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "bc01a01ab35c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # SQLite doesn't support DROP COLUMN in batch mode before 3.35.
    # Use batch_alter_table for safe column removal.
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("ai_model")
        batch_op.drop_column("openai_api_key")
        batch_op.drop_column("anthropic_api_key")

    op.add_column("users", sa.Column("llm_model", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("llm_api_key", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "llm_api_key")
    op.drop_column("users", "llm_model")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("anthropic_api_key", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("openai_api_key", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("ai_model", sa.String(length=100), nullable=True))
