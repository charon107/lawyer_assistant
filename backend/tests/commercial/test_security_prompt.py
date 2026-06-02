"""The shared security block carries the three differentiation guardrails.

Every review skill appends `SECURITY_MECHANISMS`, so these three sections
(depth gate / side consistency / role + UPL) reach vendor / nda / saas
uniformly.
"""

from app.agents.commercial.prompts.nda_review import build_nda_review_system_prompt
from app.agents.commercial.prompts.security import SECURITY_MECHANISMS


def test_security_block_has_depth_gate():
    # §5 depth gate — defaults-only config must not be auto-greenlit.
    assert "授权等级" in SECURITY_MECHANISMS
    assert "绿色" in SECURITY_MECHANISMS or "可签" in SECURITY_MECHANISMS


def test_security_block_has_side_consistency():
    # §6 — never cross-apply a side's playbook.
    assert "方向" in SECURITY_MECHANISMS
    assert "跨侧" in SECURITY_MECHANISMS or "另一侧" in SECURITY_MECHANISMS


def test_security_block_has_role_upl_guardrail():
    # §7 — role drives header + non-lawyer hard stop.
    assert "研究框架" in SECURITY_MECHANISMS
    assert "法律后果" in SECURITY_MECHANISMS


def test_nda_prompt_includes_security_block():
    prompt = build_nda_review_system_prompt(practice_profile_markdown="# 画像")
    assert "授权等级" in prompt
    assert "研究框架" in prompt
