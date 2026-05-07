"""LPACase database model - stores lawyer case metadata."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.chat_file import ChatFile
    from app.db.models.conversation import Conversation


class LPACase(Base, TimestampMixin):
    """Legal case model - groups documents and conversations."""

    __tablename__ = "lpa_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    # Relationships
    documents: Mapped[list["ChatFile"]] = relationship(
        "ChatFile",
        foreign_keys="ChatFile.case_id",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        foreign_keys="Conversation.case_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<LPACase(id={self.id}, name={self.name})>"
