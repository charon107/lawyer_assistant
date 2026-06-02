"""MaterialContractItem database model — one material-contract schedule line.

Backs material-contract-schedule: builds the disclosure schedule from
diligence findings against the purchase-agreement materiality threshold.
Each row is a contract that meets the threshold, with its counterparty,
the threshold basis it cleared, whether it has been disclosed, and an
optional link back to the originating diligence finding.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class MaterialContractItem(Base, TimestampMixin):
    """A single material-contract schedule entry under a deal."""

    __tablename__ = "material_contract_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("corporate_deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_issue_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("diligence_issues.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    contract: Mapped[str] = mapped_column(String(500), nullable=False)
    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    threshold_basis: Mapped[str | None] = mapped_column(String(255), nullable=True)
    disclosed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cite: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<MaterialContractItem(id={self.id}, deal_id={self.deal_id}, contract={self.contract}, disclosed={self.disclosed})>"
