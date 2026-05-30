"""Tool that registers an auto-renewing agreement during a review.

When a vendor / SaaS review notices the contract auto-renews, the agent
calls `write_renewal_registration` to log the effective date + term so the
Phase C renewal-watcher can later surface the cancellation deadline. The
three deadline dates are computed here (not by the model) via the pure
`renewal_calc` helpers, so the math is deterministic and testable.
"""

import json
from datetime import date

from pydantic_ai import ModelRetry, RunContext

from app.agents.commercial.deps import CommercialDeps
from app.repositories import renewal_registration_repo
from app.services import renewal_calc as calc


def _parse_iso_date(value: str, field_name: str) -> date:
    """Parse an ISO ``YYYY-MM-DD`` string, raising ModelRetry on bad input.

    Model output is untrusted; a malformed date should let the model fix its
    call rather than crash the run.
    """
    try:
        return date.fromisoformat(value.strip())
    except (ValueError, AttributeError) as exc:
        raise ModelRetry(
            f"参数 {field_name} 必须是 ISO 日期字符串（YYYY-MM-DD），收到的是 {value!r}。"
        ) from exc


async def write_renewal_registration(
    ctx: RunContext[CommercialDeps],
    effective_date: str,
    term_months: int,
    auto_renew: bool = True,
    notice_days: int = 0,
    transit_buffer_days: int = 0,
    counterparty: str | None = None,
    agreement_name: str | None = None,
    matter_id: str | None = None,
) -> str:
    """登记一份自动续约协议，供续约看守代理后续盯期限。

    在审查中发现合同**自动续约**（auto-renew）时调用本工具。三个关键
    截止日期由系统按生效日 + 期限 + 通知期**自动计算**，你不需要自己算：

    - cancel_by_calendar：原始日历截止日（期末 − 通知期）
    - cancel_by_effective：顺延到工作日后的截止日
    - send_by_effective：扣掉寄送在途天数后、仍是工作日的"最晚寄出日"

    Args:
        effective_date: 协议生效日，ISO 字符串（如 "2026-01-01"）。
        term_months: 当前期限的月数（如 12、24）。
        auto_renew: 是否自动续约。默认 True（通常调用本工具就是因为自动续约）。
        notice_days: 取消通知期的日历天数（如 60）。默认 0。
        transit_buffer_days: 寄送在途缓冲天数。默认 0。
        counterparty: 对方名称。
        agreement_name: 协议名称。
        matter_id: 关联事项 ID（可选）。

    Returns:
        JSON 字符串，含 registration_id 和三个计算出的截止日期。
    """
    deps = ctx.deps
    effective = _parse_iso_date(effective_date, "effective_date")
    if term_months < 0:
        raise ModelRetry(f"参数 term_months 不能为负，收到的是 {term_months}。")

    cancel_cal = calc.cancel_by_calendar(effective, term_months, notice_days)
    cancel_eff = calc.cancel_by_effective(effective, term_months, notice_days)
    send_eff = calc.send_by_effective(
        effective, term_months, notice_days, transit_buffer_days=transit_buffer_days
    )

    registration = renewal_registration_repo.create(
        deps.db,
        user_id=deps.user_id,
        matter_id=matter_id,
        counterparty=counterparty,
        agreement_name=agreement_name,
        effective_date=effective,
        term_months=term_months,
        auto_renew=auto_renew,
        notice_days=notice_days,
        cancel_by_calendar=cancel_cal,
        cancel_by_effective=cancel_eff,
        send_by_effective=send_eff,
    )

    return json.dumps(
        {
            "registration_id": registration.id,
            "cancel_by_calendar": cancel_cal.isoformat(),
            "cancel_by_effective": cancel_eff.isoformat(),
            "send_by_effective": send_eff.isoformat(),
        },
        ensure_ascii=False,
    )
