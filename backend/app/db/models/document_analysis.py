"""DocumentAnalysis database model - stores structured pre-analysis results for case documents."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.chat_file import ChatFile


class DocumentAnalysis(Base, TimestampMixin):
    """Structured pre-analysis of a case document.

    One-to-one with ChatFile. Stores legal analysis results as JSON
    (parties, contract type, key terms, legal relationships, risks, etc.)
    """

    __tablename__ = "document_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_file_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("chat_files.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    analysis_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    chat_file: Mapped["ChatFile"] = relationship("ChatFile", back_populates="analysis")

    def __repr__(self) -> str:
        return f"<DocumentAnalysis(id={self.id}, chat_file_id={self.chat_file_id}, status={self.status})>"
