"""LLM output validation — ensure agent-generated enum values are in the allowed set.

LLM-generated fields like ``severity``, ``classification``, ``direction`` are
written to ``String(20)``/``String(30)`` columns. A wrong value would be stored
silently. These validators reject unknown values so the caller (tool function)
can substitute a safe default or skip the field.
"""

from collections.abc import Container

_ALLOWED_SEVERITY: Container[str | None] = {"blocking", "high", "medium", "low"}
_ALLOWED_CLASSIFICATION: Container[str | None] = {
    "PROCEED",
    "PIA_REQUIRED",
    "DPIA_MANDATORY",
    "STOP",
}
_ALLOWED_DIRECTION: Container[str | None] = {"entrusted", "handler"}
_ALLOWED_RECOMMENDATION: Container[str | None] = {
    "APPROVED",
    "WITH_CONDITIONS",
    "CHANGES_REQUIRED",
    "NOT_APPROVED",
}
_ALLOWED_REVIEW_STATUS: Container[str | None] = {"draft", "final"}
_ALLOWED_DSAR_STATUS: Container[str | None] = {
    "received",
    "verifying",
    "locating",
    "exemption_analysis",
    "drafted",
    "responded",
    "escalated",
}


def check_severity(value: str | None) -> str | None:
    if value is not None and value not in _ALLOWED_SEVERITY:
        return None
    return value


def check_classification(value: str | None) -> str | None:
    if value is not None and value not in _ALLOWED_CLASSIFICATION:
        return None
    return value


def check_direction(value: str | None) -> str | None:
    if value is not None and value not in _ALLOWED_DIRECTION:
        return None
    return value


def check_recommendation(value: str | None) -> str | None:
    if value is not None and value not in _ALLOWED_RECOMMENDATION:
        return None
    return value


def check_review_status(value: str | None) -> str | None:
    if value is not None and value not in _ALLOWED_REVIEW_STATUS:
        return None
    return value


def check_dsar_status(value: str | None) -> str | None:
    if value is not None and value not in _ALLOWED_DSAR_STATUS:
        return None
    return value
