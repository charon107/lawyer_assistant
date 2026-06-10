"""IpEnforcement model — an IP enforcement-letter matter (维权信函生命周期).

Distinct lifecycle from ``ip_reviews``: outbound letters (侵权警告函 /
网络传播权通知/反通知) with a send-gate, counterparty due-diligence block, an
optional deadline (the takedown counter-notice triggers a 15-working-day
clock), and a status lifecycle.

Created by REST intake (``POST /ip/enforcement``); the WS ``cease_desist`` /
``takedown`` skills draft the letter and write it back via ``save_letter``.

The system never actually sends anything: ``status=sent`` only records that
the user confirmed they dispatched it themselves (outbound delivery is the
user's action).
"""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class IpEnforcement(Base, TimestampMixin):
    """An IP enforcement-letter matter."""

    __tablename__ = "ip_enforcement"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # cease_desist / takedown
    matter_type: Mapped[str] = mapped_column(String(20), nullable=False, default="cease_desist")
    # cease_desist: send / receive · takedown: send / respond / counter
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="send")

    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Right at issue (类型 + 注册号 + 登记状态) JSON.
    right_at_issue: Mapped[str | None] = mapped_column(Text, nullable=True)
    infringement_facts: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Counterparty due-diligence (实体/资源/IP组合/诉讼史/是否聘律/反诉风险) JSON.
    due_diligence: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Deadline — takedown counter-notice 15-working-day clock / received-letter reply window.
    response_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Letters (Markdown). Internal draft keeps the work-product header; the
    # outbound version drops it.
    letter_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    outbound_letter: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Send-gate checklist outcome (权利有效/主张成立/比例适当/授权人签署/尽调已呈现) JSON.
    send_gate: Mapped[str | None] = mapped_column(Text, nullable=True)

    # receive/respond/counter four-option-tree conclusion.
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="intake"
    )  # intake/drafting/gated/sent/responded/escalated/closed

    escalation_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit log (JSON): intake/draft/gate/sent dates, approver.
    log: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<IpEnforcement(id={self.id}, type={self.matter_type}, "
            f"mode={self.mode}, status={self.status})>"
        )
