"""TabularReview database model — one tabular-review run under a deal.

Backs tabular-review: one row per document, one column per data point,
exported to Excel. The column definitions and the extracted rows are
stored as JSON text; `export_path` points at the generated .xlsx.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class TabularReview(Base, TimestampMixin):
    """A tabular-review job + result under a deal."""

    __tablename__ = "tabular_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("corporate_deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # Column definitions (JSON: list of {key, label, prompt}).
    columns: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Extracted rows (JSON: list of {document, cells: {key: {value, cite}}}).
    rows: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Source documents covered (JSON: list of paths/filenames).
    source_docs: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="in_progress",
    )  # in_progress / completed
    export_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<TabularReview(id={self.id}, deal_id={self.deal_id}, title={self.title}, status={self.status})>"
