"""Tests for Stage 4: Cross Checker."""

from unittest.mock import MagicMock

from app.agents.lpa.cross_checker import CrossChecker


class TestCollectFindings:
    def test_collects_findings_from_reviews(self):
        reviews = [
            {
                "chapter": "第一章",
                "complexity": "simple",
                "findings": [
                    {
                        "rule_id": "A1",
                        "level": "中风险",
                        "finding": "test1",
                        "evidence": "",
                        "suggestion": "",
                    },
                    {
                        "rule_id": "B1",
                        "level": "高风险",
                        "finding": "test2",
                        "evidence": "",
                        "suggestion": "",
                    },
                ],
            },
            {
                "chapter": "第二章",
                "complexity": "complex",
                "findings": [
                    {
                        "rule_id": "D1",
                        "level": "高风险",
                        "finding": "test3",
                        "evidence": "",
                        "suggestion": "",
                    },
                ],
            },
        ]
        checker = CrossChecker(llm_client=MagicMock(), labeled_facts={})
        collected = checker._collect_findings(reviews)
        assert len(collected) == 3
        assert collected[0]["chapter"] == "第一章"
        assert collected[2]["chapter"] == "第二章"

    def test_skips_error_findings(self):
        reviews = [
            {
                "chapter": "第一章",
                "findings": [
                    {
                        "rule_id": "ERROR",
                        "level": "审查失败",
                        "finding": "error",
                        "evidence": "",
                        "suggestion": "",
                    },
                    {
                        "rule_id": "A1",
                        "level": "中风险",
                        "finding": "ok",
                        "evidence": "",
                        "suggestion": "",
                    },
                ],
            }
        ]
        checker = CrossChecker(llm_client=MagicMock(), labeled_facts={})
        collected = checker._collect_findings(reviews)
        assert len(collected) == 1
        assert collected[0]["rule_id"] == "A1"

    def test_empty_reviews(self):
        checker = CrossChecker(llm_client=MagicMock(), labeled_facts={})
        collected = checker._collect_findings([])
        assert collected == []


class TestCheckOffline:
    def test_returns_empty_on_no_findings(self):
        checker = CrossChecker(llm_client=MagicMock(), labeled_facts={})
        result = checker.check([])
        assert result["contradictions"] == []
        assert result["consistency_issues"] == []
        assert result["missing_items"] == []

    def test_returns_error_on_llm_failure(self):
        mock_llm = MagicMock()
        mock_llm.call.side_effect = Exception("API error")
        checker = CrossChecker(llm_client=mock_llm, labeled_facts={})
        reviews = [
            {
                "chapter": "第一章",
                "findings": [
                    {
                        "rule_id": "A1",
                        "level": "中风险",
                        "finding": "test",
                        "evidence": "",
                        "suggestion": "",
                    },
                ],
            }
        ]
        result = checker.check(reviews)
        assert len(result["missing_items"]) == 1
        assert "错误" in result["missing_items"][0]["item"]
