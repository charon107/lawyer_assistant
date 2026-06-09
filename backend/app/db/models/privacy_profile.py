"""PrivacyProfile model — user's privacy-legal practice profile.

Per-user "practice profile" (CLAUDE.md equivalent) for the Privacy /
Personal-Information-Protection (个人信息保护) module. One row per user.
Mirrors the per-module profile pattern used by commercial / corporate /
employment — NOT a shared company profile.

The compiled Markdown ``profile_content`` is the agent's system-prompt
input. Domain context (regulatory footprint, bidirectional DPA playbook,
privacy-policy commitments, PIA house style, DSAR process) is carried in
JSON-text columns written at cold-start.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class PrivacyProfile(Base, TimestampMixin):
    """Per-user privacy-legal practice profile."""

    __tablename__ = "privacy_profiles"

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

    # Regulatory footprint — 个保法 / 数安法 / 网安法 / 行业监管 (JSON list).
    regulatory_footprint: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_residency: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dpo_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    open_reg_matters: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Who uses the module — drives the work-product header + UPL guardrail.
    user_role: Mapped[str] = mapped_column(
        String(40), nullable=False, default="attorney"
    )  # attorney / non_attorney_with_lawyer / non_attorney_without
    lawyer_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    practice_setting: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # Available integrations (doc_storage / im / scheduled_tasks) — JSON.
    integrations: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Bidirectional DPA playbook: {entrusted: [...], handler: [...], auto_reject: ...} JSON.
    dpa_playbook: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Privacy-policy commitments (data_categories / purposes / retention / ...) JSON.
    policy_commitments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # PIA house style (trigger_criteria / structure / depth / approver) JSON.
    pia_house_style: Mapped[str | None] = mapped_column(Text, nullable=True)

    # DSAR process (volume / handler / systems_list / verification_method / response_sla) JSON.
    dsar_process: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Escalation matrix + seed docs + output config — JSON.
    escalation_matrix: Mapped[str | None] = mapped_column(Text, nullable=True)
    seed_docs: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_config: Mapped[str | None] = mapped_column(Text, nullable=True)

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
            f"<PrivacyProfile(id={self.id}, user_id={self.user_id}, "
            f"setup_status={self.setup_status})>"
        )
