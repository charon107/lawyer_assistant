"""EmploymentExpansion model — a domestic (cross-province) expansion tracker.

expansion-kickoff (WS) pre-creates the row, then the Agent fills
``analysis_result`` (structure analysis) and ``tracking_items``;
expansion-update (REST) edits ``tracking_items``.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class EmploymentExpansion(Base, TimestampMixin):
    """A cross-province employment expansion tracker."""

    __tablename__ = "employment_expansions"
    __table_args__ = (
        UniqueConstraint("user_id", "slug", name="uq_employment_expansions_user_slug"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    province: Mapped[str] = mapped_column(String(100), nullable=False)
    headcount: Mapped[str | None] = mapped_column(String(100), nullable=True)
    position_types: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    expected_timeline: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # direct / labor_dispatch / outsourcing
    employment_structure: Mapped[str | None] = mapped_column(String(40), nullable=True)
    analysis_result: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    tracking_items: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active / completed / cancelled

    def __repr__(self) -> str:
        return f"<EmploymentExpansion(id={self.id}, slug={self.slug}, province={self.province})>"
