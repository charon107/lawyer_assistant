
"""add document_type to lpa_cases

Revision ID: 618bc6dc5e76
Revises: e015f3b6544f
Create Date: 2026-05-08 07:43:29.625196

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '618bc6dc5e76'
down_revision: Union[str, None] = 'e015f3b6544f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('lpa_cases', sa.Column('document_type', sa.String(length=50), nullable=False, server_default='lpa'))


def downgrade() -> None:
    op.drop_column('lpa_cases', 'document_type')
