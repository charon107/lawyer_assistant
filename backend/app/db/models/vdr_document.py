"""VdrDocument database model — one data-room (VDR) document record.

Backs the diligence-issue-extraction inventory and the dataroom-watcher
agent. Each row is a single document mirrored/indexed under a deal, tagged
with its due-diligence request category and a priority flag (high for
重大合同 / 诉讼 / 知识产权).
"""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class VdrDocument(Base, TimestampMixin):
    """A single data-room document under a deal."""

    __tablename__ = "vdr_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("corporate_deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Due-diligence request-list category (e.g. 重大合同 / 公司及组织 / 知识产权).
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    folder: Mapped[str | None] = mapped_column(String(500), nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="normal",
    )  # high / normal
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="new",
    )  # new / reviewing / reviewed
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
    )  # manual / feishu / box / nutstore

    def __repr__(self) -> str:
        return f"<VdrDocument(id={self.id}, deal_id={self.deal_id}, filename={self.filename}, status={self.status})>"
