"""EmploymentReview model — a saved employment review result.

Written by the WS Agent skills (hiring / termination / classification /
policy / wage_hour / handbook) via the ``save_review_result`` tool; REST
only reads the history.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class EmploymentReview(Base, TimestampMixin):
    """A saved employment-legal review record."""

    __tablename__ = "employment_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    review_type: Mapped[str] = mapped_column(
        String(40), nullable=False
    )  # hiring / termination / worker_classification / policy / wage_hour / handbook
    employee_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Input
    input_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Result
    result_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # proceed / needs_fix / stop / in_progress
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_memo: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # High-risk flags triggered (JSON list of flag ids).
    high_risk_flags: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Escalation
    required_approver: Mapped[str | None] = mapped_column(String(255), nullable=True)
    escalation_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return (
            f"<EmploymentReview(id={self.id}, type={self.review_type}, "
            f"status={self.result_status})>"
        )
