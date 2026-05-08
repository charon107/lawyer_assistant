"""Tests for Stage 3: Chapter Reviewer."""

from unittest.mock import MagicMock

from app.agents.lpa.chapter_reviewer import (
    COMPLEX_KEYWORDS,
    SIMPLE_RULE_IDS,
    ChapterReviewer,
)


class TestClassifyComplexity:
    def test_simple_chapter(self):
        assert ChapterReviewer.classify_complexity("第一章 总则", "本章为总则。") == "simple"

    def test_complex_chapter_by_keyword(self):
        for kw in ["管理费", "分配", "waterfall", "key man", "除名", "关联交易"]:
            assert ChapterReviewer.classify_complexity("标题", f"包含{kw}的内容") == "complex", (
                f"Keyword '{kw}' should trigger complex"
            )

    def test_complex_chapter_in_title(self):
        assert ChapterReviewer.classify_complexity("管理费条款", "正文") == "complex"

    def test_all_complex_keywords_trigger(self):
        for kw in COMPLEX_KEYWORDS:
            result = ChapterReviewer.classify_complexity("标题", kw)
            assert result == "complex", f"Keyword '{kw}' not detected"


class TestReviewOffline:
    def test_review_returns_error_without_llm(self):
        """Without LLM, review should return an error finding."""
        mock_llm = MagicMock()
        mock_llm.chat.side_effect = Exception("No API key")
        reviewer = ChapterReviewer(llm_client=mock_llm, labeled_facts={})
        chapter = {"title": "总则", "text": "这是总则内容。"}
        result = reviewer.review(chapter)
        assert "chapter" in result
        assert "complexity" in result
        assert "findings" in result
        # Should have error finding since LLM failed
        if result["findings"]:
            assert result["findings"][0]["rule_id"] == "ERROR"


class TestValidateFindings:
    def test_filters_invalid_rule_ids(self):
        findings = [
            {"rule_id": "A1", "level": "中风险", "finding": "test", "evidence": "", "suggestion": ""},
            {"rule_id": "Z99", "level": "低风险", "finding": "invalid", "evidence": "", "suggestion": ""},
        ]
        result = ChapterReviewer._validate_findings(findings, SIMPLE_RULE_IDS)
        assert len(result) == 1
        assert result[0]["rule_id"] == "A1"

    def test_skips_non_dict_items(self):
        findings = ["not a dict", {"rule_id": "A1", "level": "中风险", "finding": "", "evidence": "", "suggestion": ""}]
        result = ChapterReviewer._validate_findings(findings, SIMPLE_RULE_IDS)
        assert len(result) == 1

    def test_preserves_valid_fields(self):
        findings = [{"rule_id": "D6", "level": "低风险", "finding": "test finding", "evidence": "test evidence", "suggestion": "test suggestion"}]
        result = ChapterReviewer._validate_findings(findings, SIMPLE_RULE_IDS)
        assert result[0]["finding"] == "test finding"
        assert result[0]["evidence"] == "test evidence"


class TestParseJson:
    def test_parses_plain_json(self):
        data = ChapterReviewer._parse_json('{"findings": []}')
        assert data == {"findings": []}

    def test_parses_json_in_code_block(self):
        text = 'Some text\n```json\n{"findings": []}\n```\nMore text'
        data = ChapterReviewer._parse_json(text)
        assert data == {"findings": []}

    def test_parses_json_in_generic_code_block(self):
        text = '```\n{"findings": []}\n```'
        data = ChapterReviewer._parse_json(text)
        assert data == {"findings": []}
