"""CorporateProfile database model — user's corporate-legal practice profile.

Stores the per-user "practice profile" (equivalent of CLAUDE.md in
claude-for-legal-zh's corporate-legal plugin) for the Corporate Legal
(公司并购) module.

Unlike the commercial-legal profile (single sales/purchasing playbook),
the corporate profile is **modular**: the cold-start interview activates
any subset of four practice modules and writes only the activated ones —

- ``mna``      并购（M&A）
- ``board``    董事会与公司秘书
- ``public``   公众公司
- ``entities`` 主体管理

``active_modules`` holds the selected list; each ``*_config`` column holds
that module's structured settings as JSON text (None when inactive). The
compiled Markdown ``profile_content`` is the agent's system-prompt input.

One row per user.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CorporateProfile(Base, TimestampMixin):
    """Per-user corporate-legal practice profile."""

    __tablename__ = "corporate_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Basic info (company-level facts usually come from the shared
    # company-profile.md; kept here for module-local convenience).
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 非上市 / 上市公司 / 上市公司的子公司
    stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    main_jurisdiction: Mapped[str | None] = mapped_column(String(255), nullable=True)
    team_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    escalation_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Who uses the module — drives the work-product header and the
    # unauthorized-practice-of-law guardrail (non-lawyers get a research
    # framing + a hard stop before legally-consequential actions).
    used_by: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="lawyer",
    )  # lawyer / non_lawyer

    # Setup depth chosen in the cold-start wizard. "quick" produces a
    # defaults-only profile; "full" is the authoritative, lawyer-reviewed depth.
    setup_depth: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="full",
    )  # quick / full

    setup_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="not_started",
    )  # not_started / in_progress / completed
    setup_progress: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Which practice modules are active (JSON list of:
    # "mna" | "board" | "public" | "entities").
    active_modules: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Per-module structured settings (JSON text; None when the module is
    # not active). Stored as JSON strings for SQLite/PostgreSQL portability.
    mna_config: Mapped[str | None] = mapped_column(Text, nullable=True)
    board_config: Mapped[str | None] = mapped_column(Text, nullable=True)
    public_config: Mapped[str | None] = mapped_column(Text, nullable=True)
    entity_config: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Compiled Markdown profile (the "CLAUDE.md equivalent" used as agent
    # system-prompt input).
    profile_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Output / notification preferences.
    alert_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    output_destination: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CorporateProfile(id={self.id}, user_id={self.user_id}, "
            f"setup_status={self.setup_status})>"
        )
