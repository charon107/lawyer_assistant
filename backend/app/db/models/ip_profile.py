"""IpProfile model — user's ip-legal (知识产权) practice profile.

Per-user "practice profile" (CLAUDE.md equivalent) for the IP / Intellectual
Property module. One row per user. Mirrors the per-module profile pattern used
by commercial / corporate / employment / privacy — NOT a shared company
profile.

The compiled Markdown ``profile_content`` is the agent's system-prompt input.
Domain context (IP scope, registration jurisdictions, enforcement posture +
approval matrix, brand-protection watch list, 4-variant work-product header
rules) is carried in JSON-text columns written at cold-start.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class IpProfile(Base, TimestampMixin):
    """Per-user ip-legal practice profile."""

    __tablename__ = "ip_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Basic info (mostly from the shared company profile).
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Who uses the module — drives the 4-variant work-product header + UPL guardrail.
    # attorney / patent_agent / non_attorney_with_lawyer / non_attorney_without
    user_role: Mapped[str] = mapped_column(String(40), nullable=False, default="attorney")
    lawyer_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supervising_lawyer: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Available integrations (ip_mgmt_system / legal_research / patent_research / ...) JSON.
    integrations: Mapped[str | None] = mapped_column(Text, nullable=True)

    # IP practice scope — 商标/著作权/专利/商业秘密/开源 (JSON list).
    ip_scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Registration jurisdictions — CNIPA / 港澳 / 马德里 / PCT-EPO (JSON list).
    registration_jurisdictions: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_management_system: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Domain ownership (商标/专利/著作权/商业秘密/开源 → owner) JSON.
    domain_ownership: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Outside counsel roster JSON.
    outside_counsel: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Enforcement posture: {default_stance, when_*, approval_matrix, auto_escalation} JSON.
    enforcement_posture: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Brand protection: {monitored_marks, jurisdictions, service, frequency} JSON.
    brand_protection: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Portfolio meta: {last_audit_date, renewal_alert_channel} JSON.
    portfolio_meta: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Seed docs + output config (work-product header rules / naming) — JSON.
    seed_docs: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_config: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Setup state
    setup_depth: Mapped[str] = mapped_column(
        String(20), nullable=False, default="full"
    )  # quick/full
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
            f"<IpProfile(id={self.id}, user_id={self.user_id}, setup_status={self.setup_status})>"
        )
