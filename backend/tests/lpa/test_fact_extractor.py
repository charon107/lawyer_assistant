"""Tests for Stage 2: Fact Extractor."""

from app.agents.lpa.fact_extractor import FactExtractor


class TestExtractRaw:
    def test_extracts_amounts(self):
        text = "认缴出资总额为人民币1000万元。基金规模为5000万美元。"
        extractor = FactExtractor()
        raw = extractor.extract_raw(text)
        assert len(raw["amounts"]) >= 1

    def test_extracts_percentages(self):
        text = "管理费率为每年2%，优先回报率为8%。"
        extractor = FactExtractor()
        raw = extractor.extract_raw(text)
        assert len(raw["percentages"]) >= 2

    def test_extracts_entity_names(self):
        text = "普通合伙人：上海某某投资管理有限公司"
        extractor = FactExtractor()
        raw = extractor.extract_raw(text)
        assert any("有限公司" in e for e in raw["entity_names"])

    def test_extracts_gp_candidates(self):
        text = "普通合伙人：深圳前海某某基金管理有限公司\n管理人：深圳前海某某基金管理有限公司"
        extractor = FactExtractor()
        raw = extractor.extract_raw(text)
        assert len(raw["gp_manager_candidates"]) >= 1

    def test_extracts_law_references(self):
        text = "依据《合伙企业法》和《私募投资基金监督管理暂行办法》制定。"
        extractor = FactExtractor()
        raw = extractor.extract_raw(text)
        assert "合伙企业法" in raw["law_references"]
        assert "私募投资基金监督管理暂行办法" in raw["law_references"]

    def test_empty_text(self):
        extractor = FactExtractor()
        raw = extractor.extract_raw("")
        assert raw["amounts"] == []
        assert raw["percentages"] == []
        assert raw["entity_names"] == []

    def test_deduplicates_entities(self):
        text = "普通合伙人：ABC有限公司\n管理人：ABC有限公司"
        extractor = FactExtractor()
        raw = extractor.extract_raw(text)
        # Should not have duplicates
        assert len(raw["entity_names"]) == len(set(raw["entity_names"]))


class TestRuleBasedLabel:
    def test_labels_gp_from_candidates(self):
        raw = {
            "gp_manager_candidates": ["深圳某某基金管理有限公司"],
            "entity_names": ["某某基金"],
            "percentages": [],
            "law_references": [],
        }
        extractor = FactExtractor()
        labeled = extractor._rule_based_label(raw, "text")
        assert labeled["gp_name"] == "深圳某某基金管理有限公司"

    def test_labels_management_fee_rate(self):
        raw = {
            "gp_manager_candidates": [],
            "entity_names": [],
            "percentages": ["2%"],
            "law_references": [],
        }
        source = "管理费率为每年2%的认缴出资额"
        extractor = FactExtractor()
        labeled = extractor._rule_based_label(raw, source)
        assert labeled.get("management_fee_rate") == 0.02

    def test_labels_hurdle_rate(self):
        raw = {
            "gp_manager_candidates": [],
            "entity_names": [],
            "percentages": ["8%"],
            "law_references": [],
        }
        source = "优先回报率为8%的门槛收益"
        extractor = FactExtractor()
        labeled = extractor._rule_based_label(raw, source)
        assert labeled.get("hurdle_rate") == 0.08

    def test_no_facts_returns_empty(self):
        raw = {
            "gp_manager_candidates": [],
            "entity_names": [],
            "percentages": [],
            "law_references": [],
        }
        extractor = FactExtractor()
        labeled = extractor._rule_based_label(raw, "")
        assert isinstance(labeled, dict)


class TestFactExtractorOffline:
    def test_extract_without_llm(self):
        text = "普通合伙人：ABC基金管理有限公司。管理费率为每年2%。"
        extractor = FactExtractor(llm_client=None)
        result = extractor.extract(text)
        assert "raw_facts" in result
        assert "labeled_facts" in result
        assert result["labeled_facts"].get("gp_name") is not None
