"""Domain-value normalizers — trust boundary for (untrusted) model output.

Out-of-set Literal values from the model would 500 the Read endpoints on
serialization. Normalize at the write boundary before persisting.
"""

_ALLOWED_SEVERITY = {"blocking", "high", "medium", "low"}
_SEVERITY_ALIASES = {
    "严重": "blocking",
    "阻断": "blocking",
    "critical": "blocking",
    "高": "high",
    "优先": "high",
    "中": "medium",
    "常规": "medium",
    "低": "low",
    "监控": "low",
}

_ALLOWED_MATERIALITY = {"always", "review", "fyi"}
_MATERIALITY_ALIASES = {
    "始终重要": "always",
    "立即": "always",
    "🔴": "always",
    "值得审阅": "review",
    "摘要": "review",
    "🟡": "review",
    "仅供参考": "fyi",
    "🟢": "fyi",
}

_ALLOWED_GAP_TYPE = {"none", "partial", "full", "new-policy", "watch", "comment-decision"}
_ALLOWED_ITEM_TYPE = {
    "regulation",
    "normative",
    "nprm",
    "pre_rule",
    "enforcement",
    "guidance",
    "speech",
    "settlement",
    "other",
}


def normalize_severity(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    if s in _ALLOWED_SEVERITY:
        return s
    return _SEVERITY_ALIASES.get(s) or (s.lower() if s.lower() in _ALLOWED_SEVERITY else None)


def normalize_materiality(raw: str | None) -> str:
    """Default to 'review' (A2 — boundary never silently becomes fyi)."""
    if raw is None:
        return "review"
    s = raw.strip()
    if s in _ALLOWED_MATERIALITY:
        return s
    return _MATERIALITY_ALIASES.get(s) or (
        s.lower() if s.lower() in _ALLOWED_MATERIALITY else "review"
    )


def normalize_gap_type(raw: str | None) -> str:
    if raw is None:
        return "partial"
    s = raw.strip().lower()
    return s if s in _ALLOWED_GAP_TYPE else "partial"


def normalize_item_type(raw: str | None) -> str:
    if raw is None:
        return "other"
    s = raw.strip().lower()
    return s if s in _ALLOWED_ITEM_TYPE else "other"
