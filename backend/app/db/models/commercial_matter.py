"""CommercialMatter database model — a tracked commercial-legal matter.

A "matter" groups one counterparty relationship: the agreements reviewed,
the renewals registered, and the deviations logged against it. Phase A's
`contract_reviews.matter_id` becomes a real ForeignKey to this table in
the Phase B migration.

One user owns many matters. `owner` is free text (a team member's name)
rather than a second ForeignKey, because team members are not separate
User accounts in this product.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CommercialMatter(Base, TimestampMixin):
    """A tracked commercial-legal matter (one counterparty relationship)."""

    __tablename__ = "commercial_matters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    matter_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agreement_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
    )  # active / closed / archived
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CommercialMatter(id={self.id}, user_id={self.user_id}, "
            f"counterparty={self.counterparty}, status={self.status})>"
        )
