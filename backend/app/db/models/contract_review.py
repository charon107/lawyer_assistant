"""ContractReview database model — one commercial-legal contract review run.

Stores the metadata and final output of a vendor-agreement-review (Phase A)
run. Phase B will add `nda` and `saas` review types via the `review_type`
column.

`matter_id` is intentionally left as a plain nullable string column rather
than a ForeignKey, because the `commercial_matters` table arrives in
Phase B. Adding the FK later is a non-destructive Alembic migration.
"""

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ContractReview(Base, TimestampMixin):
    """A single contract review record (vendor / nda / saas)."""

    __tablename__ = "contract_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Phase B will turn this into a ForeignKey to commercial_matters.id.
    matter_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # What was reviewed.
    review_type: Mapped[str] = mapped_column(String(20), nullable=False)  # vendor / nda / saas
    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agreement_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agreement_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    side: Mapped[str] = mapped_column(String(20), nullable=False, default="purchasing")
    annual_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    # The source file.
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Result.
    result_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )  # in_progress / green / yellow / red
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_memo: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Optional sub-products from later skills (filled in by stakeholder-summary etc).
    stakeholder_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Escalation routing decisions.
    required_approver: Mapped[str | None] = mapped_column(String(255), nullable=True)
    escalation_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return (
            f"<ContractReview(id={self.id}, user_id={self.user_id}, "
            f"review_type={self.review_type}, result_status={self.result_status})>"
        )
