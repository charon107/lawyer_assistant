"""Tests for the LPA Review Orchestrator."""

from app.agents.lpa.orchestrator import LPAReviewOrchestrator


class TestOrchestratorNoLLM:
    """Test orchestrator when no LLM is configured (api_key=None)."""

    def test_review_returns_error_without_llm(self):
        orchestrator = LPAReviewOrchestrator(api_key=None)

        class FakeFile:
            name = "test.txt"

            def read(self):
                return b"some content"

        result = orchestrator.review(FakeFile())
        assert "error" in result
        assert "未配置 AI 模型" in result["error"]
        assert result["stage"] == 0

    def test_review_with_progress_callback_still_errors(self):
        orchestrator = LPAReviewOrchestrator(api_key=None)

        class FakeFile:
            name = "test.txt"

            def read(self):
                return b"some content"

        progress_calls = []
        result = orchestrator.review(
            FakeFile(), progress_callback=lambda pct, msg: progress_calls.append((pct, msg))
        )
        assert "error" in result
        assert len(progress_calls) == 0


class TestRuleKeywordMap:
    def test_lpa_config_has_keyword_map(self):
        from app.agents.lpa.document_types import get_document_type_config

        config = get_document_type_config("lpa")
        kw_map = config.get("rule_keyword_map", {})
        assert len(kw_map) > 0, "LPA config should have rule_keyword_map"
        for rule_id in ["B1", "D1"]:
            assert rule_id in kw_map, f"Rule {rule_id} missing from LPA keyword map"
            assert len(kw_map[rule_id]) > 0, f"Rule {rule_id} has no keywords"
