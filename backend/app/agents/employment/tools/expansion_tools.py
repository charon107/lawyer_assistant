"""Expansion tools for the employment-legal agent (expansion-kickoff analysis)."""

import json
from typing import Any

from pydantic_ai import RunContext

from app.agents.employment.deps import EmploymentDeps
from app.agents.employment.tools.profile_tools import _loads
from app.db.models.employment_expansion import EmploymentExpansion
from app.repositories import employment_expansion_repo


def _load_owned_expansion(deps: EmploymentDeps) -> EmploymentExpansion:
    if deps.expansion_id is None:
        raise RuntimeError(
            "EmploymentDeps.expansion_id is None — the handler must resolve the "
            "active expansion before running this skill."
        )
    exp = employment_expansion_repo.get_by_id(deps.db, deps.expansion_id)
    if exp is None or exp.user_id != deps.user_id:
        raise PermissionError(f"Cannot access expansion {deps.expansion_id}.")
    return exp


async def get_expansion(ctx: RunContext[EmploymentDeps]) -> str:
    """读取当前异地扩张项目的上下文（省份、人数、岗位类型、计划、已有分析与追踪项）。

    Returns:
        JSON 字符串。
    """
    exp = _load_owned_expansion(ctx.deps)
    return json.dumps(
        {
            "expansion_id": exp.id,
            "slug": exp.slug,
            "province": exp.province,
            "headcount": exp.headcount,
            "position_types": _loads(exp.position_types),
            "expected_timeline": exp.expected_timeline,
            "employment_structure": exp.employment_structure,
            "analysis_result": _loads(exp.analysis_result),
            "tracking_items": _loads(exp.tracking_items),
        },
        ensure_ascii=False,
    )


async def update_expansion_analysis(
    ctx: RunContext[EmploymentDeps],
    employment_structure: str | None = None,
    analysis_result: dict[str, Any] | None = None,
    tracking_items: list[dict[str, Any]] | None = None,
) -> str:
    """把扩张结构分析与追踪项写回当前扩张项目（expansion-kickoff 产出时调用）。

    Args:
        employment_structure: direct / labor_dispatch / outsourcing。
        analysis_result: 结构分析详情（dict）。
        tracking_items: 追踪项列表，每项含 item/owner/deadline/status/notes。

    Returns:
        JSON 字符串。
    """
    exp = _load_owned_expansion(ctx.deps)
    fields: dict[str, Any] = {}
    if employment_structure is not None:
        fields["employment_structure"] = employment_structure
    if analysis_result is not None:
        fields["analysis_result"] = json.dumps(analysis_result, ensure_ascii=False)
    if tracking_items is not None:
        fields["tracking_items"] = json.dumps(tracking_items, ensure_ascii=False)
    employment_expansion_repo.update(ctx.deps.db, expansion=exp, **fields)
    return json.dumps({"expansion_id": exp.id, "updated": list(fields)}, ensure_ascii=False)
