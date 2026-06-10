"""LLM output validation — ensure agent-generated enum values are in the allowed set.

LLM-generated fields like ``severity``, ``classification``, ``ip_category`` are
written to ``String(20)`` columns. A wrong value would be stored silently.
These validators reject unknown values so the caller (tool function) can
substitute a safe default or skip the field.
"""

from collections.abc import Container

_ALLOWED_SEVERITY: Container[str | None] = {"blocking", "high", "medium", "low"}
_ALLOWED_CLASSIFICATION: Container[str | None] = {
    # clearance / oss
    "GREEN",
    "YELLOW",
    "RED",
    # invention
    "PURSUE",
    "INVESTIGATE",
    "REJECT",
    # infringement
    "IGNORE",
    "COMMUNICATE",
    "CEASE_DESIST",
    "LITIGATE",
}
_ALLOWED_IP_CATEGORY: Container[str | None] = {
    "trademark",
    "copyright",
    "patent",
    "trade_secret",
    "design",
}
_ALLOWED_REVIEW_STATUS: Container[str | None] = {"draft", "final"}
_ALLOWED_ENFORCEMENT_STATUS: Container[str | None] = {
    "intake",
    "drafting",
    "gated",
    "sent",
    "responded",
    "escalated",
    "closed",
}


def check_severity(value: str | None) -> str | None:
    if value is not None and value not in _ALLOWED_SEVERITY:
        return None
    return value


def check_classification(value: str | None) -> str | None:
    if value is not None and value not in _ALLOWED_CLASSIFICATION:
        return None
    return value


def check_ip_category(value: str | None) -> str | None:
    if value is not None and value not in _ALLOWED_IP_CATEGORY:
        return None
    return value


def check_review_status(value: str | None) -> str | None:
    if value is not None and value not in _ALLOWED_REVIEW_STATUS:
        return None
    return value


def check_enforcement_status(value: str | None) -> str | None:
    if value is not None and value not in _ALLOWED_ENFORCEMENT_STATUS:
        return None
    return value
