
"""add parsed_content to vdr_documents

Revision ID: c58189a7c364
Revises: d5e6f7a8b9c0
Create Date: 2026-06-03 08:03:37.340760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c58189a7c364'
down_revision: Union[str, None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotent: check if column already exists (create_all may have added it).
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("vdr_documents")}
    if "parsed_content" not in columns:
        op.add_column("vdr_documents", sa.Column("parsed_content", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("vdr_documents", "parsed_content")
