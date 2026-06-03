"""EmploymentProfile model — user's employment-legal practice profile.

Per-user "practice profile" (CLAUDE.md equivalent) for the Employment
Legal (劳动用工) module. One row per user. Mirrors the per-module profile
pattern used by commercial / corporate — NOT a shared company profile.

The compiled Markdown ``profile_content`` is the agent's system-prompt
input. Jurisdiction awareness is central: ``jurisdiction_table`` holds
per-province special rules + auto-escalation hints written at cold-start.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class EmploymentProfile(Base, TimestampMixin):
    """Per-user employment-legal practice profile."""

    __tablename__ = "employment_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Basic info
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Jurisdictions (境内异地; 海外延后, 不建 overseas 字段)
    jurisdictions: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    default_jurisdiction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    office_model: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_office"
    )  # remote_first / in_office / hybrid

    # Who uses the module — drives the work-product header + UPL guardrail.
    user_role: Mapped[str] = mapped_column(
        String(40), nullable=False, default="attorney"
    )  # attorney / non_attorney_with_lawyer / non_attorney_without
    lawyer_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Review triggers
    hiring_trigger: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    termination_trigger: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    standard_severance: Mapped[str | None] = mapped_column(
        String(40), nullable=True
    )  # statutory / negotiated / none
    high_risk_flags: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list

    # Policy config
    policy_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provincial_supplements: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Jurisdiction table — per-province special rules + auto-escalation hints.
    jurisdiction_table: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Leave management + escalation matrix
    leave_management_config: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    escalation_matrix: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Setup state
    setup_depth: Mapped[str] = mapped_column(
        String(20), nullable=False, default="full"
    )  # quick / full
    setup_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="not_started"
    )  # not_started / in_progress / completed
    setup_progress: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Compiled Markdown profile (the CLAUDE.md equivalent).
    profile_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Output / notification preferences.
    alert_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    output_destination: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<EmploymentProfile(id={self.id}, user_id={self.user_id}, "
            f"setup_status={self.setup_status})>"
        )
