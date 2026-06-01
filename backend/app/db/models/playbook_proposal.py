"""PlaybookProposal database model — a suggested playbook update.

When a clause family has been deviated from often enough (the playbook-monitor
threshold in Phase C), the system proposes updating the playbook's standard
position to match reality. The lawyer reviews each proposal and either accepts
it (the playbook is out of step with practice) or dismisses it.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class PlaybookProposal(Base, TimestampMixin):
    """A proposed update to a playbook clause position."""

    __tablename__ = "playbook_proposals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    clause_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    clause_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    current_position: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_position: Mapped[str | None] = mapped_column(Text, nullable=True)

    deviation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )  # pending / accepted / dismissed
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<PlaybookProposal(id={self.id}, user_id={self.user_id}, "
            f"clause_key={self.clause_key}, status={self.status})>"
        )
