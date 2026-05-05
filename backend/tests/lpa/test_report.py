"""Tests for Stage 5: Report Generator."""

from app.agents.lpa.report import (
    build_lpa_report,
    _summarize_risks,
    _flatten_findings,
    _format_facts,
    _build_risk_matrix,
    _build_chapter_findings,
    _build_cross_check,
    _build_disclaimer,
)


def _make_finding(rule_id="A1", level="中风险", finding="test finding"):
    return {"rule_id": rule_id, "level": level, "finding": finding, "evidence": "evidence", "suggestion": "suggestion"}


class TestBuildReport:
    def test_generates_markdown_report(self):
        facts = {"fund_name": "Test Fund", "gp_name": "Test GP"}
        reviews = [
            {"chapter": "第一章", "complexity": "simple", "findings": [_make_finding()]},
        ]
        report = build_lpa_report("test.pdf", facts, reviews)
        assert "# AI LPA 合同审查报告" in report
        assert "test.pdf" in report
        assert "第一章" in report

    def test_report_with_no_findings(self):
        report = build_lpa_report("test.pdf", {}, [])
        assert "未发现" in report or "审查报告" in report

    def test_report_includes_cross_check(self):
        facts = {"fund_name": "Test Fund"}
        reviews = []
        cross_check = {
            "contradictions": [{"id": "C1", "level": "高风险", "description": "矛盾", "chapter_a": "A", "text_a": "x", "chapter_b": "B", "text_b": "y", "resolution": "修改"}],
            "consistency_issues": [],
            "missing_items": [],
        }
        report = build_lpa_report("test.pdf", facts, reviews, cross_check=cross_check)
        assert "跨章矛盾" in report


class TestSummarizeRisks:
    def test_counts_by_level(self):
        findings = [
            _make_finding(level="高风险"),
            _make_finding(level="高风险"),
            _make_finding(level="中风险"),
            _make_finding(level="低风险"),
        ]
        rs = _summarize_risks(findings, None)
        assert rs["high_count"] == 2
        assert rs["mid_count"] == 1
        assert rs["low_count"] == 1
        assert rs["total"] == 4

    def test_verdict_with_high_risks(self):
        findings = [_make_finding(level="高风险")]
        rs = _summarize_risks(findings, None)
        assert "高风险" in rs["verdict"]

    def test_verdict_no_risks(self):
        rs = _summarize_risks([], None)
        assert "未发现" in rs["verdict"]

    def test_cross_issues_count(self):
        cross = {"contradictions": [{"id": "1"}], "consistency_issues": [{"id": "2"}], "missing_items": []}
        rs = _summarize_risks([], cross)
        assert rs["cross_issues"] == 2


class TestFlattenFindings:
    def test_flattens_with_rule_metadata(self):
        reviews = [
            {"chapter": "第一章", "findings": [_make_finding("B1", "高风险", "管理费过高")]},
        ]
        flat = _flatten_findings(reviews)
        assert len(flat) == 1
        assert flat[0]["category"] == "费用结构"
        assert flat[0]["title"] == "管理费率"


class TestFormatFacts:
    def test_formats_known_fields(self):
        facts = {
            "fund_name": "测试基金",
            "management_fee_rate": 0.02,
            "gp_carry": 0.20,
            "investment_period_years": 5,
        }
        md = _format_facts(facts)
        assert "测试基金" in md
        assert "2.0%" in md
        assert "20.0%" in md

    def test_empty_facts(self):
        md = _format_facts({})
        assert "未能提取" in md

    def test_boolean_facts(self):
        facts = {"gp_is_manager": True}
        md = _format_facts(facts)
        assert "是" in md


class TestBuildRiskMatrix:
    def test_groups_by_category(self):
        findings = [
            _make_finding("A1", "中风险"),
            _make_finding("B1", "高风险"),
        ]
        matrix = _build_risk_matrix(findings)
        assert "基本要素" in matrix or "A1" in matrix
        assert "费用结构" in matrix or "B1" in matrix

    def test_empty_findings(self):
        matrix = _build_risk_matrix([])
        assert "未发现" in matrix


class TestBuildChapterFindings:
    def test_formats_findings(self):
        reviews = [
            {
                "chapter": "第一章 总则",
                "complexity": "simple",
                "findings": [_make_finding()],
            },
        ]
        md = _build_chapter_findings(reviews)
        assert "第一章 总则" in md
        assert "quick review" in md

    def test_no_findings(self):
        reviews = [{"chapter": "第一章", "complexity": "simple", "findings": []}]
        md = _build_chapter_findings(reviews)
        assert "未发现" in md


class TestBuildCrossCheck:
    def test_formats_contradictions(self):
        cc = {
            "contradictions": [{"id": "CC1", "level": "高风险", "description": "矛盾", "chapter_a": "A", "text_a": "x", "chapter_b": "B", "text_b": "y", "resolution": "修改"}],
            "consistency_issues": [],
            "missing_items": [],
        }
        md = _build_cross_check(cc)
        assert "跨章矛盾" in md

    def test_empty_cross_check(self):
        md = _build_cross_check({"contradictions": [], "consistency_issues": [], "missing_items": []})
        assert "未发现" in md


class TestDisclaimer:
    def test_contains_legal_disclaimer(self):
        md = _build_disclaimer()
        assert "不构成正式法律意见" in md
