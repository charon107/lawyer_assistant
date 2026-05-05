"""Tests for LPA risk rules — categories, rule integrity, completeness."""

from app.agents.lpa.risk_rules import (
    LPA_RULES,
    LPA_RULE_IDS_BY_CATEGORY,
    get_all_lpa_rules,
    get_lpa_rule,
    get_lpa_rule_ids_by_category,
)


def test_all_rules_have_required_fields():
    for rule_id, rule in LPA_RULES.items():
        assert "id" in rule, f"Rule {rule_id} missing 'id'"
        assert "category" in rule, f"Rule {rule_id} missing 'category'"
        assert "title" in rule, f"Rule {rule_id} missing 'title'"
        assert "level" in rule, f"Rule {rule_id} missing 'level'"
        assert "check" in rule, f"Rule {rule_id} missing 'check'"
        assert "suggestion_template" in rule, f"Rule {rule_id} missing 'suggestion_template'"
        assert rule["id"] == rule_id, f"Rule id mismatch: {rule['id']} != {rule_id}"


def test_rule_levels_are_valid():
    valid_levels = {"高风险", "中风险", "低风险"}
    for rule_id, rule in LPA_RULES.items():
        assert rule["level"] in valid_levels, f"Rule {rule_id} has invalid level: {rule['level']}"


def test_six_categories_exist():
    expected = {"基本要素", "费用结构", "分配/瀑布", "GP/LP权利义务", "投资条款", "清算/解散/争议"}
    assert set(LPA_RULE_IDS_BY_CATEGORY.keys()) == expected


def test_category_rule_ids_match_rules_dict():
    for category, rule_ids in LPA_RULE_IDS_BY_CATEGORY.items():
        for rid in rule_ids:
            assert rid in LPA_RULES, f"Rule {rid} in category '{category}' not in LPA_RULES"
            assert LPA_RULES[rid]["category"] == category, (
                f"Rule {rid} category mismatch: {LPA_RULES[rid]['category']} != {category}"
            )


def test_total_rule_count():
    assert len(LPA_RULES) == 31  # A1-5 + B1-5 + C1-5 + D1-8 + E1-4 + F1-4 = 31


def test_get_lpa_rule_existing():
    rule = get_lpa_rule("A1")
    assert rule["id"] == "A1"
    assert rule["category"] == "基本要素"


def test_get_lpa_rule_missing():
    assert get_lpa_rule("Z99") == {}


def test_get_all_lpa_rules_returns_all():
    rules = get_all_lpa_rules()
    assert len(rules) == 31
    # Verify ordering: A before B before C before D before E before F
    categories = [r["category"] for r in rules]
    cat_order = ["基本要素", "费用结构", "分配/瀑布", "GP/LP权利义务", "投资条款", "清算/解散/争议"]
    prev_idx = -1
    for cat in categories:
        idx = cat_order.index(cat)
        assert idx >= prev_idx, f"Category ordering violated: {cat} after index {prev_idx}"
        prev_idx = idx


def test_get_lpa_rule_ids_by_category():
    result = get_lpa_rule_ids_by_category()
    assert result == LPA_RULE_IDS_BY_CATEGORY


def test_category_c_distribution_waterfall_rules():
    c_rules = LPA_RULE_IDS_BY_CATEGORY["分配/瀑布"]
    assert len(c_rules) == 5
    assert c_rules[0] == "C1"
    assert c_rules[-1] == "C5"
    assert LPA_RULES["C1"]["level"] == "高风险"
    assert "waterfall" in LPA_RULES["C1"]["check"].lower() or "瀑布" in LPA_RULES["C1"]["check"]


def test_category_e_investment_terms_rules():
    e_rules = LPA_RULE_IDS_BY_CATEGORY["投资条款"]
    assert len(e_rules) == 4
    assert LPA_RULES["E1"]["level"] == "中风险"


def test_category_f_liquidation_rules():
    f_rules = LPA_RULE_IDS_BY_CATEGORY["清算/解散/争议"]
    assert len(f_rules) == 4
    assert LPA_RULES["F1"]["level"] == "高风险"
