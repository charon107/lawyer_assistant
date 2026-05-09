"""add document_type to lpa_cases

Revision ID: 618bc6dc5e76
Revises: e015f3b6544f
Create Date: 2026-05-08 07:43:29.625196

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "618bc6dc5e76"
down_revision: str | None = "e015f3b6544f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "lpa_cases",
        sa.Column("document_type", sa.String(length=50), nullable=False, server_default="lpa"),
    )


def downgrade() -> None:
    op.drop_column("lpa_cases", "document_type")
