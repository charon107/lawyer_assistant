"""User LLM configuration model — one row per provider config."""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserLLMConfig(Base, TimestampMixin):
    """Per-user LLM provider configuration. A user can have multiple providers."""

    __tablename__ = "user_llm_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    api_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationship back to user
    user: Mapped["User"] = relationship("User", back_populates="llm_configs")

    def __repr__(self) -> str:
        return f"<UserLLMConfig(id={self.id}, user_id={self.user_id}, provider={self.provider})>"
