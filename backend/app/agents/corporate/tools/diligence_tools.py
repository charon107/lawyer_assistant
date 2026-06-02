"""Diligence-issue write/read tools for the corporate-legal agent."""

import json
from typing import Literal

from pydantic_ai import RunContext

from app.agents.corporate.deps import CorporateDeps
from app.agents.corporate.tools.deal_tools import _load_owned_deal
from app.repositories import diligence_issue_repo

Severity = Literal["blocking", "high", "medium", "low"]


async def write_diligence_issue(
    ctx: RunContext[CorporateDeps],
    title: str,
    severity: Severity,
    finding: str,
    recommendation: str | None = None,
    category: str | None = None,
    source_doc: str | None = None,
    cite: str | None = None,
) -> str:
    """把一条尽调发现写回数据库（diligence-issue-extraction 的每条发现调用一次）。

    Args:
        title: 发现标题。
        severity: blocking / high / medium / low（🔴/🟠/🟡/🟢）。
        finding: 文件说了什么 + 为何重要。
        recommendation: 价格调整 / 赔偿 / 需取得同意 / 陈述与保证 / 退出。
        category: 需求清单类别（重大合同/公司/知识产权/劳动/诉讼…）。
        source_doc: 数据室路径 + 文件名。
        cite: 法律依据，带来源标签。

    Returns:
        JSON 字符串，含 issue_id。
    """
    deal = _load_owned_deal(ctx.deps)
    issue = diligence_issue_repo.create(
        ctx.deps.db,
        deal_id=deal.id,
        title=title,
        severity=severity,
        finding=finding,
        recommendation=recommendation,
        category=category,
        source_doc=source_doc,
        cite=cite,
    )
    return json.dumps({"issue_id": issue.id, "severity": severity}, ensure_ascii=False)


async def list_diligence_issues(ctx: RunContext[CorporateDeps]) -> str:
    """读取当前交易已提取的尽调发现（供 deal-team-summary / material-contract-schedule 消费）。

    Returns:
        JSON 字符串，含发现列表（title / category / severity / finding /
        recommendation / source_doc / status）与总数。
    """
    deal = _load_owned_deal(ctx.deps)
    issues, total = diligence_issue_repo.list_by_deal(ctx.deps.db, deal_id=deal.id, limit=500)
    items = [
        {
            "id": i.id,
            "title": i.title,
            "category": i.category,
            "severity": i.severity,
            "finding": i.finding,
            "recommendation": i.recommendation,
            "source_doc": i.source_doc,
            "status": i.status,
        }
        for i in issues
    ]
    return json.dumps({"total": total, "issues": items}, ensure_ascii=False)
