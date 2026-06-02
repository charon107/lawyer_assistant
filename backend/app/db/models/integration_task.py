"""IntegrationTask model — post-closing integration plan (integration-management)."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class IntegrationTask(Base, TimestampMixin):
    """A post-closing integration work item under a deal (D1/30/90/180)."""

    __tablename__ = "integration_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("corporate_deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # D1 / D30 / D90 / D180
    phase: Mapped[str] = mapped_column(String(10), nullable=False, default="D30")
    task: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    due: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<IntegrationTask(id={self.id}, phase={self.phase}, status={self.status})>"
