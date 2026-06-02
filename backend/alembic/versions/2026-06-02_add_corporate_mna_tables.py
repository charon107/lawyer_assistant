"""add corporate-legal M&A-core tables

Second slice of the corporate-legal (公司并购) data layer — the M&A-core
tables that hang off a deal:

- corporate_deals          交易/事项工作区（其余表的父锚点）
- vdr_documents            数据室文档
- diligence_issues         尽调问题
- tabular_reviews          表格化审查（一行一文件，导出 Excel）
- closing_checklist_items  交割检查表
- material_contract_items  重大合同披露清单

Idempotent guard (create_all + Alembic run in tandem); downgrade is
name-agnostic (drop_table drops indexes; no explicit drop_index).

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-06-02 00:00:01.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: str | None = "b3c4d5e6f7a8"
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
    if "corporate_deals" in inspector.get_table_names():
        return

    # corporate_deals ---------------------------------------------------------
    op.create_table(
        "corporate_deals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("client", sa.String(255), nullable=True),
        sa.Column("counterparty", sa.String(255), nullable=True),
        sa.Column("deal_type", sa.String(50), nullable=True),
        sa.Column("side", sa.String(20), nullable=True),
        sa.Column(
            "confidentiality_level", sa.String(20), nullable=False, server_default="standard"
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("key_facts", sa.Text(), nullable=True),
        sa.Column("overrides", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("dataroom_location", sa.String(500), nullable=True),
        sa.Column("materiality_contract", sa.String(255), nullable=True),
        sa.Column("materiality_litigation", sa.String(255), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_corporate_deals_user_id"
        ),
        sa.UniqueConstraint("user_id", "code", name="uq_corporate_deals_user_code"),
    )
    op.create_index("ix_corporate_deals_user_id", "corporate_deals", ["user_id"])
    op.create_index("ix_corporate_deals_code", "corporate_deals", ["code"])

    # vdr_documents -----------------------------------------------------------
    op.create_table(
        "vdr_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("deal_id", sa.String(36), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("folder", sa.String(500), nullable=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column("source", sa.String(50), nullable=False, server_default="manual"),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["deal_id"], ["corporate_deals.id"], ondelete="CASCADE", name="fk_vdr_documents_deal_id"
        ),
    )
    op.create_index("ix_vdr_documents_deal_id", "vdr_documents", ["deal_id"])

    # diligence_issues --------------------------------------------------------
    op.create_table(
        "diligence_issues",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("deal_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("source_doc", sa.String(500), nullable=True),
        sa.Column("finding", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("cite", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["deal_id"],
            ["corporate_deals.id"],
            ondelete="CASCADE",
            name="fk_diligence_issues_deal_id",
        ),
    )
    op.create_index("ix_diligence_issues_deal_id", "diligence_issues", ["deal_id"])

    # tabular_reviews ---------------------------------------------------------
    op.create_table(
        "tabular_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("deal_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("columns", sa.Text(), nullable=True),
        sa.Column("rows", sa.Text(), nullable=True),
        sa.Column("source_docs", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="in_progress"),
        sa.Column("export_path", sa.String(500), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["deal_id"],
            ["corporate_deals.id"],
            ondelete="CASCADE",
            name="fk_tabular_reviews_deal_id",
        ),
    )
    op.create_index("ix_tabular_reviews_deal_id", "tabular_reviews", ["deal_id"])

    # closing_checklist_items -------------------------------------------------
    op.create_table(
        "closing_checklist_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("deal_id", sa.String(36), nullable=False),
        sa.Column("source_issue_id", sa.String(36), nullable=True),
        sa.Column("item_type", sa.String(30), nullable=False, server_default="condition"),
        sa.Column("item", sa.Text(), nullable=False),
        sa.Column("basis", sa.Text(), nullable=True),
        sa.Column("approval_threshold", sa.String(255), nullable=True),
        sa.Column("responsible", sa.String(255), nullable=True),
        sa.Column("blocking", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("due", sa.String(50), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["deal_id"],
            ["corporate_deals.id"],
            ondelete="CASCADE",
            name="fk_closing_checklist_items_deal_id",
        ),
        sa.ForeignKeyConstraint(
            ["source_issue_id"],
            ["diligence_issues.id"],
            ondelete="SET NULL",
            name="fk_closing_checklist_items_source_issue_id",
        ),
    )
    op.create_index("ix_closing_checklist_items_deal_id", "closing_checklist_items", ["deal_id"])
    op.create_index(
        "ix_closing_checklist_items_source_issue_id",
        "closing_checklist_items",
        ["source_issue_id"],
    )

    # material_contract_items -------------------------------------------------
    op.create_table(
        "material_contract_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("deal_id", sa.String(36), nullable=False),
        sa.Column("source_issue_id", sa.String(36), nullable=True),
        sa.Column("contract", sa.String(500), nullable=False),
        sa.Column("counterparty", sa.String(255), nullable=True),
        sa.Column("threshold_basis", sa.String(255), nullable=True),
        sa.Column("disclosed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("cite", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_ts_columns(),
        sa.ForeignKeyConstraint(
            ["deal_id"],
            ["corporate_deals.id"],
            ondelete="CASCADE",
            name="fk_material_contract_items_deal_id",
        ),
        sa.ForeignKeyConstraint(
            ["source_issue_id"],
            ["diligence_issues.id"],
            ondelete="SET NULL",
            name="fk_material_contract_items_source_issue_id",
        ),
    )
    op.create_index("ix_material_contract_items_deal_id", "material_contract_items", ["deal_id"])
    op.create_index(
        "ix_material_contract_items_source_issue_id",
        "material_contract_items",
        ["source_issue_id"],
    )


def downgrade() -> None:
    op.drop_table("material_contract_items")
    op.drop_table("closing_checklist_items")
    op.drop_table("tabular_reviews")
    op.drop_table("diligence_issues")
    op.drop_table("vdr_documents")
    op.drop_table("corporate_deals")
