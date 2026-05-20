"""
Stage 5: Report Generator.

Builds a Markdown review report from the full pipeline output:
  labeled_facts → chapter reviews → cross-check → risk matrix → Markdown
"""

from datetime import UTC, datetime
from typing import Any


def build_report(
    file_name: str,
    labeled_facts: dict[str, Any],
    chapter_reviews: list[dict[str, Any]],
    cross_check: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    rules: dict[str, Any] | None = None,
    report_title: str = "AI LPA 合同审查报告",
    label_map: dict[str, tuple] | None = None,
) -> str:
    """Generate a comprehensive contract review report in Markdown.

    Args:
        file_name: Name of the reviewed file.
        labeled_facts: Extracted facts from the document.
        chapter_reviews: Per-chapter review results.
        cross_check: Cross-chapter consistency check results.
        config: Optional config (firm_name, jurisdiction).
        rules: Risk rules dict for finding enrichment.
        report_title: Report title string.
        label_map: Field-to-label mapping for the facts table.
    """

    config = config or {}
    all_findings = _flatten_findings(chapter_reviews, rules)
    risk_summary = _summarize_risks(all_findings, cross_check)
    facts_md = _format_facts(labeled_facts, label_map)

    sections = [
        _build_header(file_name, config, report_title),
        _build_executive_summary(risk_summary),
        "---\n\n## 二、基金基本信息\n\n" + facts_md,
        "---\n\n## 三、风险评估矩阵\n\n" + _build_risk_matrix(all_findings),
        "---\n\n## 四、逐章审查发现\n\n" + _build_chapter_findings(chapter_reviews),
    ]

    if cross_check:
        sections.append("---\n\n## 五、跨章交叉检查\n\n" + _build_cross_check(cross_check))

    sections.append("---\n\n## 六、免责声明\n\n" + _build_disclaimer())

    return "\n\n".join(sections)


# ── Header ─────────────────────────────────────────────────────────────────


def _build_header(
    file_name: str, config: dict[str, Any], report_title: str = "AI LPA 合同审查报告"
) -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    return f"""# {report_title}

生成时间：{now}
文件名称：{file_name}
律所名称：{config.get("firm_name", "（未填写）")}
适用法域：{config.get("jurisdiction", "中国大陆")}
审查范围：基本要素 / 费用结构 / GP-LP权利义务
说明：本报告由 AI 自动生成，仅供律师辅助参考，不构成正式法律意见。"""


# ── Executive Summary ──────────────────────────────────────────────────────


def _summarize_risks(
    findings: list[dict[str, Any]],
    cross_check: dict[str, Any] | None,
) -> dict[str, Any]:
    high = [f for f in findings if "高风险" in f.get("level", "")]
    mid = [f for f in findings if "中风险" in f.get("level", "")]
    low = [f for f in findings if "低风险" in f.get("level", "")]

    total_issues = len(findings)
    cross_issues = 0
    if cross_check:
        cross_issues = (
            len(cross_check.get("contradictions", []))
            + len(cross_check.get("consistency_issues", []))
            + len(cross_check.get("missing_items", []))
        )

    if high:
        verdict = "存在高风险条款，建议重点复核后决定是否签署"
    elif mid:
        verdict = "存在若干需关注的条款，建议修改后签署"
    elif low:
        verdict = "整体风险可控，可进入下一阶段"
    else:
        verdict = "未发现明显风险，可正常签署"

    return {
        "high_count": len(high),
        "mid_count": len(mid),
        "low_count": len(low),
        "cross_issues": cross_issues,
        "total": total_issues + cross_issues,
        "verdict": verdict,
        "top_risks": [f["finding"] for f in high[:3]],
    }


def _build_executive_summary(rs: dict[str, Any]) -> str:
    top = "\n".join(f"- {r}" for r in rs["top_risks"]) or "- （无高风险项）"
    return f"""## 一、执行摘要

| 维度 | 结果 |
|------|------|
| 高风险项 | {rs["high_count"]} |
| 中风险项 | {rs["mid_count"]} |
| 低风险项 | {rs["low_count"]} |
| 跨章问题 | {rs["cross_issues"]} |
| **合计** | **{rs["total"]}** |

**综合判断**：{rs["verdict"]}

**前三大风险**：
{top}"""


# ── Facts Table ────────────────────────────────────────────────────────────

_DEFAULT_LABEL_MAP = {
    "fund_name": ("基金名称",),
    "fund_type": ("基金类型",),
    "domicile": ("注册地",),
    "gp_name": ("普通合伙人 (GP)",),
    "manager_name": ("管理人",),
    "gp_is_manager": ("GP 兼任管理人",),
    "committed_capital": ("总认缴出资额",),
    "management_fee_rate": ("管理费率",),
    "management_fee_basis": ("管理费计算基数",),
    "hurdle_rate": ("优先回报率 (Hurdle)",),
    "gp_carry": ("GP Carry 比例",),
    "investment_period_years": ("投资期", "年"),
    "exit_period_years": ("退出期", "年"),
    "extension_period_years": ("延长期", "年"),
    "lp_min_commitment": ("LP 最低出资额",),
    "gp_removal_for_cause": ("有因除名条件",),
    "gp_removal_nofault_threshold": ("无因除名投票比例",),
    "key_persons": ("关键人士",),
    "dispute_resolution": ("争议解决机构",),
}


def _format_facts(facts: dict[str, Any], label_map: dict[str, tuple] | None = None) -> str:
    if not facts:
        return "（未能提取到结构化事实信息）\n"

    rows = []
    label_map = label_map or _DEFAULT_LABEL_MAP

    for key, label_info in label_map.items():
        val = facts.get(key)
        if val is None:
            continue
        label = label_info[0]
        suffix = label_info[1] if len(label_info) > 1 else ""

        if isinstance(val, bool):
            val = "是" if val else "否"
        elif isinstance(val, float):
            if key.endswith("_rate") or key.endswith("_carry"):
                val = f"{val * 100:.1f}%"
            else:
                val = f"{val}{suffix}"
        elif isinstance(val, list):
            val = "、".join(str(v) for v in val)
        elif isinstance(val, (int,)):
            val = f"{val}{suffix}"

        rows.append(f"| {label} | {val} |")

    if not rows:
        return "（未能提取到结构化事实信息）\n"

    return "| 项目 | 内容 |\n|------|------|\n" + "\n".join(rows) + "\n"


# ── Risk Matrix ────────────────────────────────────────────────────────────


def _build_risk_matrix(findings: list[dict[str, Any]]) -> str:
    if not findings:
        return "未发现需要标记的风险条款。\n"

    by_category: dict[str, list[dict]] = {}
    for f in findings:
        cat = f.get("category", f.get("rule_id", "")[0] if f.get("rule_id") else "其他")
        by_category.setdefault(cat, []).append(f)

    tables = []
    for cat, items in by_category.items():
        rows = []
        for item in items:
            level_emoji = {
                "高风险": "red",
                "中风险": "orange",
                "低风险": "yellow",
                "未发现问题": "green",
            }
            color = level_emoji.get(item.get("level", ""), "grey")
            rows.append(
                f"| {item.get('rule_id', '')} | {item.get('title', '')} "
                f"| <span style='color:{color}'>**{item.get('level', '')}**</span> "
                f"| {item.get('finding', '')[:100]} |"
            )
        table = (
            f"### {cat}\n\n| ID | 检查项 | 风险等级 | 发现 |\n|----|--------|---------|------|\n"
            + "\n".join(rows)
        )
        tables.append(table)

    return "\n\n".join(tables) + "\n"


# ── Chapter Findings ───────────────────────────────────────────────────────


def _build_chapter_findings(chapter_reviews: list[dict[str, Any]]) -> str:
    parts = []
    for review in chapter_reviews:
        chapter_name = review.get("chapter", review.get("chapter_name", "未知章节"))
        complexity = review.get("complexity", "simple")
        findings = review.get("findings", [])

        badge = "deep" if complexity == "complex" else "quick"
        header = f"### {chapter_name} `[{badge} review]`\n"

        if not findings:
            header += "\n本章未发现需要标记的风险条款。\n"
            parts.append(header)
            continue

        items = []
        for idx, f in enumerate(findings, 1):
            evidence = f.get("evidence", "")
            evidence_block = f"> {evidence}" if evidence else "> （无原文引用）"

            items.append(f"""**{idx}. [{f.get("level", "")}] {f.get("rule_id", "")} — {f.get("finding", "")}**

{evidence_block}

**修改建议**：{f.get("suggestion", "（无）")}
""")

        parts.append(header + "\n".join(items))

    return "\n\n".join(parts) if parts else "（未进行逐章审查）\n"


# ── Cross-Check Section ────────────────────────────────────────────────────


def _build_cross_check(cc: dict[str, Any]) -> str:
    parts = []

    contradictions = cc.get("contradictions", [])
    if contradictions:
        items = []
        for c in contradictions:
            items.append(
                f"- **[{c.get('level', '')}] {c.get('id', '')}** — {c.get('description', '')}\n"
                f"  - {c.get('chapter_a', '?')}: {c.get('text_a', '')}\n"
                f"  - {c.get('chapter_b', '?')}: {c.get('text_b', '')}\n"
                f"  - 建议：{c.get('resolution', '')}"
            )
        parts.append("### 跨章矛盾\n\n" + "\n".join(items))

    consistency = cc.get("consistency_issues", [])
    if consistency:
        items = []
        for ci in consistency:
            chapters = "、".join(ci.get("affected_chapters", []))
            items.append(
                f"- **[{ci.get('level', '')}] {ci.get('id', '')}** — {ci.get('description', '')}\n"
                f"  - 影响章节：{chapters}\n"
                f"  - 分析：{ci.get('detail', '')}\n"
                f"  - 建议：{ci.get('suggestion', '')}"
            )
        parts.append("### 一致性问题\n\n" + "\n".join(items))

    missing = cc.get("missing_items", [])
    if missing:
        items = []
        for mi in missing:
            items.append(
                f"- **[{mi.get('severity', '')}] {mi.get('id', '')}** — {mi.get('item', '')}\n"
                f"  - 行业惯例：{mi.get('market_practice', '')}\n"
                f"  - 建议：{mi.get('suggestion', '')}"
            )
        parts.append("### 建议补充条款\n\n" + "\n".join(items))

    return "\n\n".join(parts) if parts else "交叉检查未发现需要特别关注的问题。\n"


# ── Disclaimer ─────────────────────────────────────────────────────────────


def _build_disclaimer() -> str:
    return """本报告由 AI 自动生成，仅用于合同初审、风险提示和流程提效。

**重要提示**：
1. 本报告不构成正式法律意见，不应替代持证律师的专业判断
2. AI 分析可能存在遗漏、错误或不准确之处
3. 正式签署合同前，应由持证律师或企业法务对合同全文进行复核
4. AI 模型可能对金融法律术语理解存在偏差，建议针对关键条款进行人工验证
5. 本报告中的风险等级仅为建议，实际风险判断应结合具体交易背景和法律环境

生成模型的训练数据截止日期可能早于当前时间，不反映法律法规的最新变动。"""


# ── Helpers ────────────────────────────────────────────────────────────────


def _flatten_findings(
    chapter_reviews: list[dict[str, Any]], rules: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    if rules is None:
        from .risk_rules import LPA_RULES

        rules = LPA_RULES
    all_findings = []
    for review in chapter_reviews:
        for f in review.get("findings", []):
            rule_id = f.get("rule_id", "")
            rule = rules.get(rule_id, {})
            all_findings.append(
                {
                    "rule_id": rule_id,
                    "title": rule.get("title", f.get("finding", "")[:40]),
                    "category": rule.get("category", "其他"),
                    "level": f.get("level", ""),
                    "finding": f.get("finding", ""),
                    "evidence": f.get("evidence", ""),
                    "suggestion": f.get("suggestion", ""),
                }
            )
    return all_findings


# Backward compatibility alias
build_lpa_report = build_report
