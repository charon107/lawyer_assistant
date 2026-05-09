"""Tests for document type configurations — validates all registered types."""

import pytest

from app.agents.lpa.document_types import DOCUMENT_TYPE_CONFIGS, get_document_type_config

# All registered document types — derived from config to prevent drift
ALL_TYPES = sorted(DOCUMENT_TYPE_CONFIGS.keys())

REQUIRED_CONFIG_KEYS = [
    "name",
    "report_title",
    "chapter_keywords",
    "entity_patterns",
    "fact_tool_schema",
    "risk_rules",
    "rule_keyword_map",
    "simple_rule_ids",
    "complex_rule_ids",
    "prompt_templates",
]

REQUIRED_PROMPT_KEYS = [
    "chapter_split",
    "fact_labeling",
    "simple_review",
    "complex_review",
    "cross_check",
]


class TestDocumentTypeConfigs:
    """Test that all document type configs are well-formed."""

    def test_all_types_covers_every_config(self):
        """Drift detection: ALL_TYPES must match DOCUMENT_TYPE_CONFIGS keys."""
        assert set(ALL_TYPES) == set(DOCUMENT_TYPE_CONFIGS.keys()), (
            f"ALL_TYPES drift: {set(DOCUMENT_TYPE_CONFIGS.keys()) - set(ALL_TYPES)} in config but not in ALL_TYPES"
        )

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_config_has_all_required_keys(self, doc_type: str):
        config = DOCUMENT_TYPE_CONFIGS[doc_type]
        for key in REQUIRED_CONFIG_KEYS:
            assert key in config, f"'{doc_type}' missing key '{key}'"

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_config_name_is_nonempty_string(self, doc_type: str):
        config = DOCUMENT_TYPE_CONFIGS[doc_type]
        assert isinstance(config["name"], str)
        assert len(config["name"]) > 0

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_config_report_title_is_nonempty_string(self, doc_type: str):
        config = DOCUMENT_TYPE_CONFIGS[doc_type]
        assert isinstance(config["report_title"], str)
        assert len(config["report_title"]) > 0

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_chapter_keywords_is_nonempty_list(self, doc_type: str):
        config = DOCUMENT_TYPE_CONFIGS[doc_type]
        assert isinstance(config["chapter_keywords"], list)
        assert len(config["chapter_keywords"]) > 0

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_entity_patterns_is_nonempty_list(self, doc_type: str):
        config = DOCUMENT_TYPE_CONFIGS[doc_type]
        assert isinstance(config["entity_patterns"], list)
        assert len(config["entity_patterns"]) > 0

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_fact_tool_schema_has_properties(self, doc_type: str):
        schema = DOCUMENT_TYPE_CONFIGS[doc_type]["fact_tool_schema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert len(schema["properties"]) > 0

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_risk_rules_nonempty(self, doc_type: str):
        config = DOCUMENT_TYPE_CONFIGS[doc_type]
        assert isinstance(config["risk_rules"], dict)
        assert len(config["risk_rules"]) > 0, f"'{doc_type}' has no risk rules"

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_prompt_templates_has_all_keys(self, doc_type: str):
        templates = DOCUMENT_TYPE_CONFIGS[doc_type]["prompt_templates"]
        for key in REQUIRED_PROMPT_KEYS:
            assert key in templates, f"'{doc_type}' prompt_templates missing '{key}'"


class TestRiskRulesStructure:
    """Test that risk rules for all types have required fields."""

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_rules_have_required_fields(self, doc_type: str):
        rules = DOCUMENT_TYPE_CONFIGS[doc_type]["risk_rules"]
        for rule_id, rule in rules.items():
            assert "id" in rule, f"'{doc_type}' rule {rule_id} missing 'id'"
            assert "category" in rule, f"'{doc_type}' rule {rule_id} missing 'category'"
            assert "title" in rule, f"'{doc_type}' rule {rule_id} missing 'title'"
            assert "level" in rule, f"'{doc_type}' rule {rule_id} missing 'level'"
            assert "check" in rule, f"'{doc_type}' rule {rule_id} missing 'check'"
            assert "suggestion_template" in rule, (
                f"'{doc_type}' rule {rule_id} missing 'suggestion_template'"
            )
            assert rule["id"] == rule_id, (
                f"'{doc_type}' rule id mismatch: {rule['id']} != {rule_id}"
            )

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_rule_levels_are_valid(self, doc_type: str):
        valid_levels = {"高风险", "中风险", "低风险"}
        rules = DOCUMENT_TYPE_CONFIGS[doc_type]["risk_rules"]
        for rule_id, rule in rules.items():
            assert rule["level"] in valid_levels, (
                f"'{doc_type}' rule {rule_id} invalid level: {rule['level']}"
            )


class TestRuleKeywordMap:
    """Test that rule_keyword_map entries reference valid rule IDs."""

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_keyword_map_keys_in_rules(self, doc_type: str):
        config = DOCUMENT_TYPE_CONFIGS[doc_type]
        rules = config["risk_rules"]
        kw_map = config["rule_keyword_map"]
        for rule_id in kw_map:
            assert rule_id in rules, (
                f"'{doc_type}' keyword map references non-existent rule '{rule_id}'"
            )


class TestSimpleComplexRuleIds:
    """Test that simple/complex rule IDs are valid and non-overlapping."""

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_simple_ids_in_rules(self, doc_type: str):
        config = DOCUMENT_TYPE_CONFIGS[doc_type]
        rules = config["risk_rules"]
        for rid in config["simple_rule_ids"]:
            assert rid in rules, f"'{doc_type}' simple_rule_id '{rid}' not in risk_rules"

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_complex_ids_in_rules(self, doc_type: str):
        config = DOCUMENT_TYPE_CONFIGS[doc_type]
        rules = config["risk_rules"]
        for rid in config["complex_rule_ids"]:
            assert rid in rules, f"'{doc_type}' complex_rule_id '{rid}' not in risk_rules"

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_simple_and_complex_dont_overlap(self, doc_type: str):
        config = DOCUMENT_TYPE_CONFIGS[doc_type]
        overlap = config["simple_rule_ids"] & config["complex_rule_ids"]
        assert len(overlap) == 0, f"'{doc_type}' simple/complex overlap: {overlap}"

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_all_rules_classified(self, doc_type: str):
        config = DOCUMENT_TYPE_CONFIGS[doc_type]
        rules = config["risk_rules"]
        classified = config["simple_rule_ids"] | config["complex_rule_ids"]
        for rid in rules:
            assert rid in classified, f"'{doc_type}' rule '{rid}' not in simple or complex"


class TestGetDocumentTypeConfig:
    """Test the get_document_type_config function."""

    @pytest.mark.parametrize("doc_type", ALL_TYPES)
    def test_get_existing_type(self, doc_type: str):
        config = get_document_type_config(doc_type)
        assert config["name"] == DOCUMENT_TYPE_CONFIGS[doc_type]["name"]

    def test_get_unknown_type_raises_key_error(self):
        with pytest.raises(KeyError, match="Unknown document type"):
            get_document_type_config("nonexistent_type")


class TestRuleCounts:
    """Verify expected rule counts per document type."""

    def test_lpa_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["lpa"]["risk_rules"]) == 31

    def test_contract_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["contract"]["risk_rules"]) == 15

    def test_nda_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["nda"]["risk_rules"]) == 12

    def test_employment_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["employment"]["risk_rules"]) == 13

    def test_lease_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["lease"]["risk_rules"]) == 11

    def test_loan_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["loan"]["risk_rules"]) == 11

    def test_sales_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["sales"]["risk_rules"]) == 11

    def test_service_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["service"]["risk_rules"]) == 11

    def test_ip_license_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["ip_license"]["risk_rules"]) == 11

    def test_equity_investment_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["equity_investment"]["risk_rules"]) == 11

    def test_construction_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["construction"]["risk_rules"]) == 11

    def test_articles_of_association_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["articles_of_association"]["risk_rules"]) == 11

    def test_marital_property_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["marital_property"]["risk_rules"]) == 10

    def test_will_estate_rule_count(self):
        assert len(DOCUMENT_TYPE_CONFIGS["will_estate"]["risk_rules"]) == 9
