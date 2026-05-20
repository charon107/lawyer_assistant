"""add law_metadata table

Revision ID: f030249bd9eb
Revises: 618bc6dc5e76
Create Date: 2026-05-09 00:41:02.141496

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f030249bd9eb"
down_revision: str | None = "618bc6dc5e76"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Skip if table already exists (may have been created by create_all in dev)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "law_metadata" in inspector.get_table_names():
        return
    op.create_table(
        "law_metadata",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("sub_category", sa.String(50), nullable=True),
        sa.Column("source_type", sa.String(20), nullable=False, server_default="法律"),
        sa.Column("effective_date", sa.String(10), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="现行有效"),
        sa.Column("article_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("law_metadata")
