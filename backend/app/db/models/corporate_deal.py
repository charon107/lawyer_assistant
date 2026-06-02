"""CorporateDeal database model — a corporate-legal matter / deal workspace.

In claude-for-legal-zh a "matter" in the corporate plugin is usually a
transaction (并购买方/卖方、融资、董事会事项、主体重组、整合项目). This is the
anchor every M&A-core record (VDR docs, diligence issues, tabular reviews,
closing checklist, material contracts) hangs off via `deal_id`.

One deal has a short `code` (slug) unique per user — the matter-workspace
skill's `<简称>`.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CorporateDeal(Base, TimestampMixin):
    """A corporate-legal deal / matter workspace."""

    __tablename__ = "corporate_deals"
    __table_args__ = (UniqueConstraint("user_id", "code", name="uq_corporate_deals_user_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Slug identifier (matter-workspace 简称) — lowercase + hyphens.
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    client: Mapped[str | None] = mapped_column(String(255), nullable=True)
    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 并购买方 / 并购卖方 / 融资 / 董事会事项 / 主体重组 / 整合项目 / 其他
    deal_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    side: Mapped[str | None] = mapped_column(String(20), nullable=True)  # buyer / seller / na
    # 标准 / 较高 / 清洁团队
    confidentiality_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="standard",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
    )  # active / closed / archived

    key_facts: Mapped[str | None] = mapped_column(Text, nullable=True)
    overrides: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON / Markdown
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Data-room location + materiality thresholds (deal-context.md equivalents).
    dataroom_location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    materiality_contract: Mapped[str | None] = mapped_column(String(255), nullable=True)
    materiality_litigation: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<CorporateDeal(id={self.id}, user_id={self.user_id}, code={self.code}, status={self.status})>"
