"""ModuleConfig database model — per-user setup state for any legal module.

Generic state machine for the cold-start wizard of any future legal module
(commercial-legal, employment-legal, ip-legal, ...). Phase A uses only
`module_name = 'commercial-legal'`; later phases will add more rows per
user as additional modules ship.

`setup_data` is intentionally JSON-text so each module can store its own
intermediate wizard state without schema migrations. The compiled output
of cold-start (Markdown profile) is stored both here (`config_content`)
and on the module-specific table (e.g. `commercial_profiles.profile_content`).
The duplication is deliberate: this row is the source of truth for the
wizard's mid-flight state; the module-specific table is what the agent
actually reads at runtime.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ModuleConfig(Base, TimestampMixin):
    """Per-user, per-module cold-start configuration state."""

    __tablename__ = "module_configs"
    __table_args__ = (
        UniqueConstraint("user_id", "module_name", name="uq_module_configs_user_module"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    setup_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="not_started",
    )  # not_started / in_progress / completed
    setup_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    config_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ModuleConfig(id={self.id}, user_id={self.user_id}, "
            f"module_name={self.module_name}, setup_status={self.setup_status})>"
        )
