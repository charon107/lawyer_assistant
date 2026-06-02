"""BoardMeeting + BoardDocument models — 董事会与公司秘书 module.

`board_meeting` records a governance meeting; `board_document` holds the
drafted minutes / resolutions / written consents (board-minutes and
written-consent skills), in draft or final state.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class BoardMeeting(Base, TimestampMixin):
    """A board / shareholder meeting under a user's practice."""

    __tablename__ = "board_meetings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # board / shareholder / committee
    kind: Mapped[str] = mapped_column(String(30), nullable=False, default="board")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    meeting_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    attendees: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")

    def __repr__(self) -> str:
        return f"<BoardMeeting(id={self.id}, kind={self.kind}, status={self.status})>"


class BoardDocument(Base, TimestampMixin):
    """A drafted governance document (minutes / resolution / written consent)."""

    __tablename__ = "board_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    meeting_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("board_meetings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # minutes / resolution / written_consent
    doc_kind: Mapped[str] = mapped_column(String(30), nullable=False, default="minutes")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )  # draft / final

    def __repr__(self) -> str:
        return f"<BoardDocument(id={self.id}, doc_kind={self.doc_kind}, status={self.status})>"
