"""Deterministic materiality classification — the shared "soul" of the module.

This module is the SINGLE AUTHORITATIVE SOURCE (review decision C1) for the
item_type → tier base mapping. Two consumers share it:

- cron (reg-change-monitor, Phase 4) calls ``classify_materiality`` directly to
  pre-bucket fetched candidates with NO LLM.
- WS reg-feed-watcher injects ``render_tier_table_for_prompt`` into its system
  prompt so the LLM refines ON TOP of the same deterministic base instead of
  re-deriving its own taxonomy (prevents cron/WS drift).

Review decision A2: boundary / no-keyword-match items default to ``review``
(NEVER ``fyi``) so a keyword miss can never silently bury a real 🔴.
"""

from __future__ import annotations

from collections.abc import Iterable

# Materiality tiers (🔴 / 🟡 / 🟢).
ALWAYS = "always"
REVIEW = "review"
FYI = "fyi"

# ---------------------------------------------------------------------------
# C1 AUTHORITATIVE BASE TABLE — item_type → base tier.
# Edit HERE only. The WS prompt renders this; the classifier refines on it.
# ---------------------------------------------------------------------------
ITEM_TYPE_BASE_TIER: dict[str, str] = {
    "regulation": ALWAYS,  # 正式规章 — always IF regulator on watchlist (else → review)
    "normative": ALWAYS,  # 规范性文件 — same watchlist gate
    "nprm": REVIEW,  # 征求意见稿
    "guidance": REVIEW,  # 监管指引
    "enforcement": REVIEW,  # 执法处罚 — refined up/down by keyword
    "pre_rule": REVIEW,  # 预征求意见调研 (前瞻性, 边界→review)
    "speech": FYI,  # 领导讲话
    "settlement": FYI,  # 和解整改
    "other": REVIEW,  # A2: boundary default → review, never fyi
}

_WATCHLIST_GATED = frozenset({"regulation", "normative"})


def _norm(values: Iterable[str] | None) -> set[str]:
    return {v.strip().lower() for v in (values or []) if v and v.strip()}


def _text_hits(text: str, keywords: set[str]) -> bool:
    if not keywords:
        return False
    low = (text or "").lower()
    return any(kw in low for kw in keywords)


def classify_materiality(
    *,
    item_type: str,
    regulator: str | None,
    text: str,
    watchlist_regulators: Iterable[str] | None = None,
    industry_keywords: Iterable[str] | None = None,
    practice_keywords: Iterable[str] | None = None,
) -> str:
    """Deterministically bucket a reg item into always / review / fyi (NO LLM).

    Args:
        item_type: one of ITEM_TYPE_BASE_TIER keys (unknown → treated as "other").
        regulator: publishing regulator name (matched against watchlist).
        text: title + summary, for keyword matching.
        watchlist_regulators: regulators the user monitors.
        industry_keywords: terms that mark an item as directly industry-relevant.
        practice_keywords: terms that mark an item as related-practice-relevant.

    Returns:
        "always" | "review" | "fyi".
    """
    base = ITEM_TYPE_BASE_TIER.get(item_type, REVIEW)
    reg = (regulator or "").strip().lower()
    watch = _norm(watchlist_regulators)
    industry = _norm(industry_keywords)
    practice = _norm(practice_keywords)

    # ① 正式规章 / 规范性文件: always only if the regulator is actually watched.
    if item_type in _WATCHLIST_GATED:
        regulator_watched = bool(reg) and any(w in reg or reg in w for w in watch)
        return ALWAYS if regulator_watched else REVIEW

    # ③ 执法处罚: industry hit → always, practice hit → review, else fyi.
    if item_type == "enforcement":
        if _text_hits(text, industry):
            return ALWAYS
        if _text_hits(text, practice):
            return REVIEW
        return FYI

    # ②④⑤ everything else follows the base table (review/fyi), A2 default = review.
    return base


def render_tier_table_for_prompt() -> str:
    """Render the C1 authoritative base table as text for WS prompt injection.

    The WS reg-feed-watcher LLM refines on this base ("行业匹配 / 关联性钩子") but
    MUST NOT invent its own item_type → tier mapping.
    """
    label = {ALWAYS: "始终重要 🔴", REVIEW: "值得审阅 🟡", FYI: "仅供参考 🟢"}
    type_zh = {
        "regulation": "正式规章",
        "normative": "规范性文件",
        "nprm": "征求意见稿",
        "guidance": "监管指引",
        "enforcement": "执法处罚",
        "pre_rule": "预征求意见调研",
        "speech": "领导讲话",
        "settlement": "和解整改",
        "other": "其他",
    }
    lines = ["### item_type → 重要度层级（确定性基础表，权威定义于 materiality_rules.py）"]
    for item_type, tier in ITEM_TYPE_BASE_TIER.items():
        lines.append(f"- `{item_type}`（{type_zh.get(item_type, item_type)}）→ **{label[tier]}**")
    lines.append(
        "\n精化规则（你在确定性基础上做，不得另立基础映射）：\n"
        "- 正式规章/规范性文件：发布机构命中监测清单才升 🔴，否则 🟡。\n"
        "- 执法处罚：命中行业关键词升 🔴，命中相关实践 🟡，否则 🟢。\n"
        "- 边界/无关键词命中：默认 🟡（值得审阅），**绝不降为 🟢**——宁可多审不可漏判。"
    )
    return "\n".join(lines)
