"""Backward compatibility shim."""

from app.agents.shared.fact_extractor import (
    AMOUNT_RE,
    CHINESE_PERCENT_RE,
    DATE_RE,
    LAW_REFERENCE_RE,
    PERCENT_RE,
    FactExtractor,
)

__all__ = [
    "AMOUNT_RE",
    "CHINESE_PERCENT_RE",
    "DATE_RE",
    "LAW_REFERENCE_RE",
    "PERCENT_RE",
    "FactExtractor",
]
