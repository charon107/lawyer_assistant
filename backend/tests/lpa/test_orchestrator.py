"""Tests for the LPA Review Orchestrator (offline mode)."""

from app.agents.lpa.orchestrator import LPAReviewOrchestrator


class TestOrchestratorOffline:
    """Test orchestrator in offline mode (no API key)."""

    def test_review_text_file_offline(self):
        orchestrator = LPAReviewOrchestrator(deepseek_api_key=None)

        class FakeFile:
            name = "test.txt"

            def read(self):
                return (
                    "第一章 总则\n本基金名称为测试基金。\n"
                    "第二章 出资\n认缴出资总额为人民币1000万元。\n"
                    "第三章 管理费\n管理费率为每年2%。\n"
                    "第四章 分配\n分配相关内容。\n"
                    "第五章 争议解决\n适用《合伙企业法》。\n"
                ).encode()

        result = orchestrator.review(FakeFile())
        assert "error" not in result, f"Unexpected error: {result.get('error')}"
        assert "chapters" in result
        assert "facts" in result
        assert "chapter_reviews" in result
        assert "cross_check" in result
        assert "report_markdown" in result
        assert len(result["chapters"]) >= 1
        assert len(result["chapter_reviews"]) >= 1

    def test_review_produces_report(self):
        orchestrator = LPAReviewOrchestrator(deepseek_api_key=None)

        class FakeFile:
            name = "lpa.txt"

            def read(self):
                text = (
                    "第一章 总则\n"
                    "本基金名称为测试基金，普通合伙人：ABC基金管理有限公司。管理费率为每年2%。\n"
                    "第二章 出资\n"
                    "认缴出资总额为人民币1000万元，各合伙人按约定比例出资。\n"
                    "第三章 管理费\n"
                    "管理费率为每年2%的认缴出资额，投资期结束后减半。\n"
                    "第四章 分配\n"
                    "基金收益按瀑布式分配顺序向各合伙人进行分配，优先回报率为8%。\n"
                    "第五章 争议解决\n"
                    "因本协议引起的争议，适用《合伙企业法》相关规定。"
                )
                return text.encode("utf-8")

        result = orchestrator.review(FakeFile())
        assert "error" not in result, f"Unexpected error: {result.get('error')}"
        assert "# AI LPA 合同审查报告" in result["report_markdown"]

    def test_progress_callback_called(self):
        orchestrator = LPAReviewOrchestrator(deepseek_api_key=None)

        class FakeFile:
            name = "test.txt"

            def read(self):
                text = (
                    "第一章 总则\n" + "本基金为有限合伙型私募基金。" * 10 + "\n"
                    "第二章 出资\n" + "认缴出资总额为人民币一亿元。" * 10
                )
                return text.encode("utf-8")

        progress_calls = []
        result = orchestrator.review(
            FakeFile(), progress_callback=lambda pct, msg: progress_calls.append((pct, msg))
        )
        assert len(progress_calls) >= 2
        assert progress_calls[-1][0] == 1.0

    def test_mock_chapter_reviews(self):
        orchestrator = LPAReviewOrchestrator(deepseek_api_key=None)
        chapters = [
            {"title": "管理费条款", "text": "管理费率为每年2%的认缴出资额。"},
            {"title": "总则", "text": "本基金名称为测试基金。"},
        ]
        labeled_facts = {"fund_name": "测试基金"}
        reviews = orchestrator._mock_chapter_reviews(chapters, labeled_facts)
        assert len(reviews) == 2
        assert reviews[0]["chapter"] == "管理费条款"
        assert reviews[0]["complexity"] == "complex"


class TestRuleKeywords:
    def test_lpa_config_has_keyword_map(self):
        from app.agents.lpa.document_types import get_document_type_config

        config = get_document_type_config("lpa")
        kw_map = config.get("rule_keyword_map", {})
        assert len(kw_map) > 0, "LPA config should have rule_keyword_map"
        for rule_id in ["B1", "D1"]:
            assert rule_id in kw_map, f"Rule {rule_id} missing from LPA keyword map"
            assert len(kw_map[rule_id]) > 0, f"Rule {rule_id} has no keywords"

    def test_static_rule_keywords_returns_empty(self):
        assert LPAReviewOrchestrator._rule_keywords("A1", "") == []
        assert LPAReviewOrchestrator._rule_keywords("Z99", "") == []


class TestFindContext:
    def test_finds_keyword_context(self):
        text = "本基金的管理费率为每年2%的认缴出资额。"
        ctx = LPAReviewOrchestrator._find_context(text, "管理费率")
        assert "管理费率" in ctx

    def test_keyword_not_found(self):
        ctx = LPAReviewOrchestrator._find_context("test text", "nonexistent")
        assert ctx == ""
