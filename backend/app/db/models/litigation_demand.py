"""LitigationDemand model — 律师函生命周期.

Distinct lifecycle from analyses: demand letters (send/receive) with intake
snapshot, 7-item LOUD GATE pretransmit checklist, dual-draft (internal
letter_draft with work-product header + outbound_letter stripped of header),
and a 4-option triage tree for received letters.

Created by REST intake; WS skills (demand_draft / demand_received) draft
and write back. The system never actually sends: status=sent records user
confirmation of self-dispatch.
"""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class LitigationDemand(Base, TimestampMixin):
    """A demand-letter matter (律师函)."""

    __tablename__ = "litigation_demands"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matter_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("litigation_matters.id", ondelete="SET NULL"),
        nullable=True,
    )

    # payment / breach_cure / stop_infringement / evidence_preservation / settlement / other
    demand_type: Mapped[str] = mapped_column(String(30), nullable=False, default="other")
    # send / receive
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="send")

    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # 委托登记快照 (JSON: 函件类型 / 当事人 / 事实 / 法律依据 / 期望结果 / 截止 / 先前沟通 / 分发 / 筹码 / 不利耐受 / 语气 / 保密过滤 / 自认弃权风险)
    intake_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 涉案主张 (JSON: 权利类型 / 依据 / 状态)
    right_or_claim: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 律师函草稿（内部版带抬头 + 对外版去抬头）
    letter_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    outbound_letter: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 发送前 7 项门禁 (JSON: 保密过滤 / 自认风险 / 权利保留 / 和解姿态 / 事实准确性 / 比例适当 / 授权人签署)
    pretransmit_checklist: Mapped[str | None] = mapped_column(Text, nullable=True)

    response_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    # receive 模式四选项树结论 (JSON)
    triage_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    # intake / drafting / gated / sent / received / responded / escalated / closed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="intake")

    escalation_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    sent_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sent_via: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 邮件 / 快递 / 当面

    # 审计日志 (JSON: 建档/起草/过门禁/标记已发送日期、审批人)
    log: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<LitigationDemand(id={self.id}, demand_type={self.demand_type}, "
            f"mode={self.mode}, status={self.status})>"
        )
