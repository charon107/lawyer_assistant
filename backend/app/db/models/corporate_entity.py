"""CorporateEntity + EntityComplianceItem models — 主体管理 module.

`corporate_entity` is the subsidiary/entity register; `entity_compliance_item`
is the per-entity compliance calendar (annual report, filings, audits) the
ip-renewal-watcher analogue surfaces.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CorporateEntity(Base, TimestampMixin):
    """A managed legal entity (subsidiary / affiliate)."""

    __tablename__ = "corporate_entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # 有限公司 / 股份公司 / 合伙企业 / ...
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(255), nullable=True)
    controller: Mapped[str | None] = mapped_column(String(255), nullable=True)
    equity_ratio: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active / dormant
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CorporateEntity(id={self.id}, name={self.name}, status={self.status})>"


class EntityComplianceItem(Base, TimestampMixin):
    """A compliance-calendar item for an entity (filing / report / audit)."""

    __tablename__ = "entity_compliance_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("corporate_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filing_type: Mapped[str] = mapped_column(String(100), nullable=False)
    due_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recurrence: Mapped[str | None] = mapped_column(String(50), nullable=True)  # annual / one_time
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<EntityComplianceItem(id={self.id}, filing_type={self.filing_type}, status={self.status})>"
