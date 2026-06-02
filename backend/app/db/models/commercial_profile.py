"""CommercialProfile database model — user's commercial-legal practice profile.

Stores the per-user "practice profile" (equivalent of CLAUDE.md in
claude-for-legal-zh) for the Commercial Legal module:

- Basic team info (company, side, monthly volume, GC).
- Setup progress (drives the multi-step cold-start wizard).
- The compiled Markdown `profile_content` after cold-start completes.
- Structured playbooks (sales / purchasing) stored as JSON text so the
  agent's `get_playbook` tool can read them clause-by-clause without
  re-parsing Markdown.
- Escalation matrix (who approves what).

One row per user.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CommercialProfile(Base, TimestampMixin):
    """Per-user commercial-legal practice profile."""

    __tablename__ = "commercial_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Basic team info
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    team_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gc_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    monthly_volume: Mapped[str | None] = mapped_column(String(50), nullable=True)
    side: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="purchasing",
    )  # sales / purchasing / both

    # Setup depth chosen in the cold-start wizard. "quick" produces a
    # defaults-only profile (no per-clause playbook); downstream review
    # skills must NOT issue a "green / safe to sign" conclusion on it.
    # "full" is the authoritative, lawyer-reviewed depth.
    setup_depth: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="full",
    )  # quick / full

    # Who uses the module. Drives the work-product header and the
    # unauthorized-practice-of-law guardrail (non-lawyers get a research
    # framing + a hard stop before legally-consequential actions).
    used_by: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="lawyer",
    )  # lawyer / non_lawyer

    # Setup state (kept here in addition to module_configs because the cold-start
    # wizard needs to be able to mark this profile "completed" even after the
    # user has wiped/restarted the module_configs row).
    setup_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="not_started",
    )  # not_started / in_progress / completed
    setup_progress: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Compiled Markdown profile (the "CLAUDE.md equivalent" used as agent
    # system prompt input).
    profile_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Structured playbooks (JSON text). Stored as JSON strings rather than
    # SQLAlchemy JSON type for portability across SQLite and future PostgreSQL.
    playbook_sales: Mapped[str | None] = mapped_column(Text, nullable=True)
    playbook_purchasing: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Escalation matrix (JSON text).
    escalation_matrix: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Output / notification preferences.
    renewal_alert_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    output_destination: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CommercialProfile(id={self.id}, user_id={self.user_id}, "
            f"setup_status={self.setup_status})>"
        )
