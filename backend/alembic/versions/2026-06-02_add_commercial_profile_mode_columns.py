"""add setup_depth and used_by columns to commercial_profiles

Materializes the cold-start wizard's "config mode" choices so they
actually condition downstream behaviour:

- ``setup_depth`` (quick / full): quick produces a defaults-only profile;
  downstream review skills must not issue a "green / safe to sign" result
  on it.
- ``used_by`` (lawyer / non_lawyer): drives the work-product header and the
  unauthorized-practice-of-law guardrail.

Existing rows default to ``full`` / ``lawyer`` to preserve current behaviour
(see plan Risks): only new cold-starts write the real chosen values.

Revision ID: a2b3c4d5e6f7
Revises: f3d4e5f6a7b8
Create Date: 2026-06-02 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: str | None = "f3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(sa.text(f"PRAGMA table_info({table})"))
    return column in [row[1] for row in result]


def upgrade() -> None:
    if not _column_exists("commercial_profiles", "setup_depth"):
        op.add_column(
            "commercial_profiles",
            sa.Column(
                "setup_depth",
                sa.String(20),
                nullable=False,
                server_default="full",
            ),
        )
    if not _column_exists("commercial_profiles", "used_by"):
        op.add_column(
            "commercial_profiles",
            sa.Column(
                "used_by",
                sa.String(20),
                nullable=False,
                server_default="lawyer",
            ),
        )


def downgrade() -> None:
    if _column_exists("commercial_profiles", "used_by"):
        with op.batch_alter_table("commercial_profiles", schema=None) as batch_op:
            batch_op.drop_column("used_by")
    if _column_exists("commercial_profiles", "setup_depth"):
        with op.batch_alter_table("commercial_profiles", schema=None) as batch_op:
            batch_op.drop_column("setup_depth")
