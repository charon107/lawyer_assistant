"""ContractDeviation database model — one persisted clause deviation.

A single row records that a reviewed contract deviated from the playbook on one
clause family. These rows are written during a review (from the structured
`result_json.deviations`) so the playbook-monitor (Phase C) can count how often
a given clause is deviated from over a rolling window without re-parsing JSON
blobs.

`review_id` links back to the `ContractReview` the deviation came from.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ContractDeviation(Base, TimestampMixin):
    """A single clause deviation persisted from a contract review."""

    __tablename__ = "contract_deviations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    review_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("contract_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    clause_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    clause_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    playbook_position: Mapped[str | None] = mapped_column(Text, nullable=True)
    signed_position: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Double-axis severity (mirrors SeverityAxis in the review schema).
    severity_legal: Mapped[str] = mapped_column(String(10), nullable=False, default="green")
    severity_commercial: Mapped[str] = mapped_column(String(10), nullable=False, default="green")

    category: Mapped[str | None] = mapped_column(String(40), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ContractDeviation(id={self.id}, review_id={self.review_id}, "
            f"clause_key={self.clause_key})>"
        )
