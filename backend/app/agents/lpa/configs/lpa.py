"""Configuration for LPA (Limited Partnership Agreement) document type."""

from pathlib import Path

from app.agents.lpa.risk_rules import LPA_RULES

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "prompts"

CHAPTER_KEYWORDS = [
    "定义",
    "definitions",
    "interpretation",
    "释义",
    "出资",
    "capital contribution",
    "capital commitment",
    "认缴",
    "管理费",
    "management fee",
    "报酬",
    "分配",
    "distribution",
    "allocation",
    "waterfall",
    "投资",
    "investment",
    "investments",
    "普通合伙人",
    "general partner",
    "有限合伙人",
    "limited partner",
    "合伙人会议",
    "咨询委员会",
    "advisory committee",
    "lpac",
    "转让",
    "transfer",
    "退伙",
    "withdrawal",
    "解散",
    "清算",
    "dissolution",
    "liquidation",
    "违约责任",
    "default",
    "争议解决",
    "dispute resolution",
    "其他",
    "miscellaneous",
    "签署",
    "signature",
    "execution",
]

ENTITY_PATTERNS = [
    r"(?:甲方|乙方|丙方|普通合伙人|有限合伙人|基金管理人|执行事务合伙人|GP|LP|管理人)[：:\s]*([^\n,，。；;]+?(?:公司|企业|基金|合伙|Co\.|Ltd\.|LLP|Inc\.|Corp\.))",
]

RULE_KEYWORD_MAP = {
    "B1": ["管理费", "management fee", "报酬"],
    "B2": ["管理费", "management fee", "基数", "basis"],
    "B3": ["管理费", "management fee", "step-down", "减免"],
    "B4": ["费用", "expense", "分担", "allocation"],
    "B5": ["关联方", "related party", "费用"],
    "C1": ["分配", "distribution", "waterfall", "瀑布"],
    "C2": ["优先回报", "preferred return", "hurdle"],
    "C3": ["carry", "业绩报酬", "超额收益"],
    "C4": ["回拨", "clawback"],
    "C5": ["跟投", "co-investment"],
    "D1": ["关键人士", "key man", "key person"],
    "D2": ["除名", "removal", "罢免"],
    "D3": ["关联交易", "related party transaction"],
    "D4": ["投资限制", "investment restriction"],
    "D5": ["转让", "transfer", "退伙", "withdrawal"],
    "D7": ["风险管理", "risk management"],
    "E1": ["集中度", "concentration"],
    "E2": ["跟投", "co-investment"],
    "E3": ["后续投资", "follow-on"],
    "E4": ["杠杆", "leverage"],
}

SIMPLE_RULE_IDS = {"A1", "A2", "A3", "A4", "A5", "D6", "D8"}
COMPLEX_RULE_IDS = {
    "B1",
    "B2",
    "B3",
    "B4",
    "B5",
    "C1",
    "C2",
    "C3",
    "C4",
    "C5",
    "D1",
    "D2",
    "D3",
    "D4",
    "D5",
    "D7",
    "E1",
    "E2",
    "E3",
    "E4",
    "F1",
    "F2",
    "F3",
    "F4",
}


def _build_fact_tool_schema() -> dict:
    """Build the JSON Schema for the LPA fact-labeling tool."""
    return {
        "type": "object",
        "properties": {
            "fund_name": {"type": "string", "description": "基金名称"},
            "fund_type": {"type": "string", "description": "基金类型"},
            "domicile": {"type": "string", "description": "注册地"},
            "gp_name": {"type": "string", "description": "普通合伙人名称"},
            "manager_name": {"type": "string", "description": "管理人名称"},
            "gp_is_manager": {"type": "boolean", "description": "GP是否同时担任管理人"},
            "committed_capital": {"type": "string", "description": "认缴出资总额"},
            "management_fee_rate": {"type": "number", "description": "管理费率（小数）"},
            "management_fee_basis": {"type": "string", "description": "管理费计算基数类型"},
            "hurdle_rate": {"type": "number", "description": "优先回报率（小数）"},
            "gp_carry": {"type": "number", "description": "GP业绩报酬比例（小数）"},
            "investment_period_years": {"type": "integer", "description": "投资期（年）"},
            "exit_period_years": {"type": "integer", "description": "退出期（年）"},
            "extension_period_years": {"type": "integer", "description": "延长期（年）"},
            "lpac_approval_threshold": {"type": "number", "description": "LPAC审批门槛比例"},
            "lp_min_commitment": {"type": "string", "description": "LP最低出资额"},
            "gp_removal_for_cause": {"type": "string", "description": "GP有因除名条款"},
            "gp_removal_nofault_threshold": {
                "type": "number",
                "description": "GP无过错除名投票比例",
            },
            "key_persons": {
                "type": "array",
                "items": {"type": "string"},
                "description": "关键人士列表",
            },
            "dispute_resolution": {"type": "string", "description": "争议解决机构"},
        },
        "required": ["fund_name", "gp_name"],
    }


CONFIG = {
    "name": "有限合伙协议 (LPA)",
    "report_title": "AI LPA 合同审查报告",
    "chapter_keywords": CHAPTER_KEYWORDS,
    "entity_patterns": ENTITY_PATTERNS,
    "fact_tool_schema": _build_fact_tool_schema(),
    "risk_rules": LPA_RULES,
    "rule_keyword_map": RULE_KEYWORD_MAP,
    "simple_rule_ids": SIMPLE_RULE_IDS,
    "complex_rule_ids": COMPLEX_RULE_IDS,
    "prompt_templates": {
        "chapter_split": str(PROMPTS_DIR / "lpa" / "chapter_split.md"),
        "fact_labeling": str(PROMPTS_DIR / "lpa" / "fact_labeling.md"),
        "simple_review": str(PROMPTS_DIR / "lpa" / "simple_review.md"),
        "complex_review": str(PROMPTS_DIR / "lpa" / "complex_review.md"),
        "cross_check": str(PROMPTS_DIR / "lpa" / "cross_check.md"),
    },
}
