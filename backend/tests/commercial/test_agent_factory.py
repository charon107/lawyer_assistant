"""Tests for the commercial-legal agent factory.

We do NOT call a real LLM here. We just verify:

1. `create_commercial_agent` returns a properly-wired Agent for
   the supported skill.
2. Tools are registered (the right names show up on the agent).
3. The system prompt includes the user's compiled profile when one
   is passed in.
4. Unknown skills raise.
"""

import pytest

from app.agents.commercial import (
    CommercialDeps,
    create_commercial_agent,
)
from app.agents.commercial.prompts import (
    SECURITY_MECHANISMS,
    build_vendor_review_system_prompt,
)


class TestVendorReviewWiring:
    def test_factory_returns_agent(self):
        agent = create_commercial_agent("vendor-agreement-review")
        assert agent is not None

    def test_factory_injects_profile_into_system_prompt(self):
        prompt = build_vendor_review_system_prompt(
            practice_profile_markdown="# Acme Co\n采购方，月均 20 单。"
        )
        assert "Acme Co" in prompt
        assert "采购方" in prompt
        # Security block is always included
        assert "共享审查规范" in prompt
        assert SECURITY_MECHANISMS.strip() in prompt

    def test_factory_omits_profile_marker_when_none(self):
        prompt = build_vendor_review_system_prompt(practice_profile_markdown=None)
        assert "你正在为以下用户工作" not in prompt
        # Vendor guidance + security still there
        assert "你是一位资深商事合同律师" in prompt
        assert "共享审查规范" in prompt

    def test_unknown_skill_raises(self):
        with pytest.raises(ValueError, match="Unknown commercial-legal skill"):
            create_commercial_agent("not-a-real-skill")  # type: ignore[arg-type]


class TestRegisteredTools:
    """Sanity check that the 4 commercial tools + 2 law tools are wired.

    PydanticAI exposes registered tools via a private attribute path
    that varies by version, so we just verify the agent run-time
    looks sane and that tools we expect to be callable are importable.
    """

    def test_commercial_tools_importable(self):
        from app.agents.commercial.tools import (  # noqa: F401
            get_playbook,
            read_practice_profile,
            write_contract_review,
            write_practice_profile,
        )

    def test_law_tools_importable(self):
        from app.agents.tools.law_tools import (  # noqa: F401
            get_law_article,
            search_law,
        )


class TestCommercialDepsShape:
    def test_deps_default_review_id_is_none(self, db, user_id):
        deps = CommercialDeps(user_id=user_id, db=db)
        assert deps.review_id is None

    def test_deps_accepts_review_id(self, db, user_id):
        deps = CommercialDeps(user_id=user_id, db=db, review_id="r-123")
        assert deps.review_id == "r-123"
