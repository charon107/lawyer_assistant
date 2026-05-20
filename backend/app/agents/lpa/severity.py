"""Four-tier severity levels for risk findings."""

from enum import StrEnum


class Severity(StrEnum):
    """Risk severity levels aligned with the claude-for-legal 4-tier system."""

    CRITICAL = "critical"  # 🔴 不可接受 — must fix before signing
    SIGNIFICANT = "significant"  # 🟠 重大风险 — should fix
    NOTE = "note"  # 🟡 需注意 — acceptable with awareness
    ALIGNED = "aligned"  # 🟢 符合要求 — meets or exceeds standard
