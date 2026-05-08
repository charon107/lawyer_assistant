"""Document type configurations for the review pipeline.

Each document type defines its own:
- chapter_keywords: keywords for chapter boundary detection
- entity_patterns: regex patterns for entity extraction
- fact_tool_schema: JSON Schema for the LLM fact-labeling tool
- fact_tool_handler: callable that handles fact-labeling tool calls
- risk_rules: dict of review rules
- rule_keyword_map: mapping from rule IDs to keywords for complexity classification
- simple_rule_ids / complex_rule_ids: rule ID sets for fast vs deep review
- prompt_templates: paths to prompt template files per stage
"""

from pathlib import Path

from app.agents.lpa.risk_rules import LPA_RULES
from app.agents.rules.contract_rules import CONTRACT_RULES
from app.agents.rules.employment_rules import EMPLOYMENT_RULES
from app.agents.rules.nda_rules import NDA_RULES

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "prompts"

# LPA chapter keywords (Chinese/English bilingual)
_LPA_CHAPTER_KEYWORDS = [
    "定义", "definitions", "interpretation", "释义",
    "出资", "capital contribution", "capital commitment", "认缴",
    "管理费", "management fee", "报酬",
    "分配", "distribution", "allocation", "waterfall",
    "投资", "investment", "investments",
    "普通合伙人", "general partner",
    "有限合伙人", "limited partner",
    "合伙人会议", "咨询委员会", "advisory committee", "lpac",
    "转让", "transfer", "退伙", "withdrawal",
    "解散", "清算", "dissolution", "liquidation",
    "违约责任", "default",
    "争议解决", "dispute resolution",
    "其他", "miscellaneous",
    "签署", "signature", "execution",
]

# LPA entity patterns
_LPA_ENTITY_PATTERNS = [
    r"(?:甲方|乙方|丙方|普通合伙人|有限合伙人|基金管理人|执行事务合伙人|GP|LP|管理人)[：:\s]*([^\n,，。；;]+?(?:公司|企业|基金|合伙|Co\.|Ltd\.|LLP|Inc\.|Corp\.))",
]

# LPA rule-to-keyword mapping for chapter complexity classification
_LPA_RULE_KEYWORD_MAP = {
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

# LPA simple/complex rule IDs
_LPA_SIMPLE_RULE_IDS = {"A1", "A2", "A3", "A4", "A5", "D6", "D8"}
_LPA_COMPLEX_RULE_IDS = {"B1", "B2", "B3", "B4", "B5", "C1", "C2", "C3", "C4", "C5", "D1", "D2", "D3", "D4", "D5", "D7", "E1", "E2", "E3", "E4", "F1", "F2", "F3", "F4"}


def _build_lpa_fact_tool_schema() -> dict:
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
            "gp_removal_nofault_threshold": {"type": "number", "description": "GP无过错除名投票比例"},
            "key_persons": {"type": "array", "items": {"type": "string"}, "description": "关键人士列表"},
            "dispute_resolution": {"type": "string", "description": "争议解决机构"},
        },
        "required": [],
    }


# Document type configurations
DOCUMENT_TYPE_CONFIGS: dict[str, dict] = {
    "lpa": {
        "name": "有限合伙协议 (LPA)",
        "report_title": "AI LPA 合同审查报告",
        "chapter_keywords": _LPA_CHAPTER_KEYWORDS,
        "entity_patterns": _LPA_ENTITY_PATTERNS,
        "fact_tool_schema": _build_lpa_fact_tool_schema(),
        "risk_rules": LPA_RULES,
        "rule_keyword_map": _LPA_RULE_KEYWORD_MAP,
        "simple_rule_ids": _LPA_SIMPLE_RULE_IDS,
        "complex_rule_ids": _LPA_COMPLEX_RULE_IDS,
        "prompt_templates": {
            "chapter_split": str(PROMPTS_DIR / "chapter_split.md"),
            "fact_labeling": str(PROMPTS_DIR / "fact_labeling.md"),
            "simple_review": str(PROMPTS_DIR / "simple_review.md"),
            "complex_review": str(PROMPTS_DIR / "complex_review.md"),
            "cross_check": str(PROMPTS_DIR / "cross_check.md"),
        },
    },
    "contract": {
        "name": "通用合同",
        "report_title": "AI 合同审查报告",
        "chapter_keywords": [
            "定义", "definitions", "interpretation", "释义",
            "标的", "subject matter", "scope",
            "价款", "价格", "price", "payment", "费用",
            "履行", "performance", "交付", "delivery",
            "违约", "default", "breach", "责任",
            "保密", "confidential", "保密条款",
            "知识产权", "intellectual property",
            "不可抗力", "force majeure",
            "争议解决", "dispute resolution", "仲裁", "诉讼",
            "合同终止", "termination", "解除",
            "转让", "assignment", "变更", "amendment",
            "通知", "notice",
            "适用法律", "governing law",
            "其他", "miscellaneous", "一般条款",
            "签署", "signature", "execution",
        ],
        "entity_patterns": [
            r"(?:甲方|乙方|丙方|买方|卖方|委托方|受托方|发包方|承包方|出租方|承租方)[：:\s]*([^\n,，。；;]+?(?:公司|企业|集团|Co\.|Ltd\.|LLP|Inc\.|Corp\.))",
        ],
        "fact_tool_schema": {
            "type": "object",
            "properties": {
                "party_a": {"type": "string", "description": "甲方名称"},
                "party_b": {"type": "string", "description": "乙方名称"},
                "contract_subject": {"type": "string", "description": "合同标的"},
                "contract_value": {"type": "string", "description": "合同金额"},
                "payment_terms": {"type": "string", "description": "付款条件"},
                "contract_term": {"type": "string", "description": "合同期限"},
                "delivery_date": {"type": "string", "description": "交付日期"},
                "governing_law": {"type": "string", "description": "适用法律"},
                "dispute_resolution": {"type": "string", "description": "争议解决方式"},
                "confidentiality": {"type": "boolean", "description": "是否包含保密条款"},
                "termination_conditions": {"type": "string", "description": "终止条件"},
            },
            "required": [],
        },
        "risk_rules": CONTRACT_RULES,
        "rule_keyword_map": {
            "A1": ["主体", "parties", "甲方", "乙方"],
            "A2": ["标的", "subject matter", "scope", "范围"],
            "A3": ["期限", "term", "续期", "renewal"],
            "A4": ["金额", "价格", "price", "payment", "付款"],
            "B1": ["违约", "default", "breach", "责任"],
            "B2": ["保密", "confidential", "保密条款"],
            "B3": ["知识产权", "intellectual property"],
            "B4": ["不可抗力", "force majeure"],
            "B5": ["竞业", "non-compete", "竞业限制"],
            "C1": ["争议", "dispute", "仲裁", "诉讼"],
            "C2": ["终止", "termination", "解除"],
            "C3": ["转让", "assignment", "分包"],
        },
        "simple_rule_ids": {"A5", "C4", "C5"},
        "complex_rule_ids": {"A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4", "B5", "C1", "C2", "C3"},
        "prompt_templates": {
            "chapter_split": str(PROMPTS_DIR / "chapter_split.md"),
            "fact_labeling": str(PROMPTS_DIR / "fact_labeling.md"),
            "simple_review": str(PROMPTS_DIR / "simple_review.md"),
            "complex_review": str(PROMPTS_DIR / "complex_review.md"),
            "cross_check": str(PROMPTS_DIR / "cross_check.md"),
        },
    },
    "nda": {
        "name": "保密协议 (NDA)",
        "report_title": "AI NDA 合同审查报告",
        "chapter_keywords": [
            "定义", "definitions", "保密信息", "confidential information",
            "保密义务", "confidentiality obligation",
            "使用限制", "use restriction", "purpose",
            "期限", "term", "duration", "有效期",
            "返还", "return", "销毁", "destruction",
            "违约", "breach", "default", "责任",
            "救济", "remedy", "禁令", "injunction",
            "争议解决", "dispute resolution", "仲裁", "诉讼",
            "适用法律", "governing law",
            "转让", "assignment",
            "通知", "notice",
            "其他", "miscellaneous",
            "签署", "signature", "execution",
        ],
        "entity_patterns": [
            r"(?:甲方|乙方|丙方|披露方|接收方|Disclosing Party|Receiving Party)[：:\s]*([^\n,，。；;]+?(?:公司|企业|集团|Co\.|Ltd\.|LLP|Inc\.|Corp\.))",
        ],
        "fact_tool_schema": {
            "type": "object",
            "properties": {
                "disclosing_party": {"type": "string", "description": "披露方名称"},
                "receiving_party": {"type": "string", "description": "接收方名称"},
                "confidential_info_scope": {"type": "string", "description": "保密信息范围"},
                "confidentiality_period": {"type": "string", "description": "保密期限"},
                "purpose": {"type": "string", "description": "使用目的"},
                "governing_law": {"type": "string", "description": "适用法律"},
                "dispute_resolution": {"type": "string", "description": "争议解决方式"},
                "non_compete_included": {"type": "boolean", "description": "是否包含竞业限制条款"},
                "non_solicit_included": {"type": "boolean", "description": "是否包含非招揽条款"},
                "remedy_provisions": {"type": "string", "description": "救济措施"},
            },
            "required": [],
        },
        "risk_rules": NDA_RULES,
        "rule_keyword_map": {
            "A1": ["保密信息", "confidential information", "定义"],
            "A2": ["保密义务", "confidentiality obligation", "义务范围"],
            "A3": ["期限", "term", "duration", "保密期限"],
            "A4": ["关联方", "affiliate", "子公司"],
            "B1": ["使用限制", "use restriction", "目的", "purpose"],
            "B2": ["披露", "disclosure", "第三方"],
            "B3": ["返还", "return", "销毁", "destruction"],
            "B4": ["知识产权", "intellectual property"],
            "B5": ["竞业", "non-compete", "非招揽", "non-solicit"],
            "C1": ["违约", "breach", "救济", "remedy"],
            "C2": ["争议", "dispute", "仲裁", "诉讼"],
        },
        "simple_rule_ids": {"A4", "C3"},
        "complex_rule_ids": {"A1", "A2", "A3", "B1", "B2", "B3", "B4", "B5", "C1", "C2"},
        "prompt_templates": {
            "chapter_split": str(PROMPTS_DIR / "chapter_split.md"),
            "fact_labeling": str(PROMPTS_DIR / "fact_labeling.md"),
            "simple_review": str(PROMPTS_DIR / "simple_review.md"),
            "complex_review": str(PROMPTS_DIR / "complex_review.md"),
            "cross_check": str(PROMPTS_DIR / "cross_check.md"),
        },
    },
    "employment": {
        "name": "劳动合同",
        "report_title": "AI 劳动合同审查报告",
        "chapter_keywords": [
            "合同期限", "劳动期限", "contract term", "试用期", "probation",
            "工作内容", "工作岗位", "job description", "职责",
            "工作地点", "work location",
            "劳动报酬", "工资", "薪酬", "salary", "compensation",
            "工作时间", "工时", "working hours", "加班",
            "社会保险", "五险一金", "福利",
            "保密", "confidential",
            "竞业限制", "non-compete",
            "培训", "服务期", "training",
            "知识产权", "intellectual property",
            "合同解除", "termination", "解除",
            "争议", "dispute", "仲裁",
            "其他", "miscellaneous",
            "签署", "signature",
        ],
        "entity_patterns": [
            r"(?:用人单位|甲方|乙方|雇主|Employee|Employer)[：:\s]*([^\n,，。；;]+?(?:公司|企业|集团|个人|Co\.|Ltd\.|LLP|Inc\.|Corp\.))",
        ],
        "fact_tool_schema": {
            "type": "object",
            "properties": {
                "employer_name": {"type": "string", "description": "用人单位名称"},
                "employee_name": {"type": "string", "description": "员工姓名"},
                "position": {"type": "string", "description": "工作岗位"},
                "contract_type": {"type": "string", "description": "合同类型（固定期限/无固定期限）"},
                "contract_term": {"type": "string", "description": "合同期限"},
                "probation_period": {"type": "string", "description": "试用期"},
                "salary": {"type": "string", "description": "工资标准"},
                "work_location": {"type": "string", "description": "工作地点"},
                "working_hours": {"type": "string", "description": "工时制度"},
                "non_compete_included": {"type": "boolean", "description": "是否包含竞业限制"},
                "non_compete_compensation": {"type": "string", "description": "竞业限制补偿金"},
                "social_insurance": {"type": "boolean", "description": "是否约定缴纳社保"},
            },
            "required": [],
        },
        "risk_rules": EMPLOYMENT_RULES,
        "rule_keyword_map": {
            "A1": ["合同期限", "contract term", "试用期", "probation"],
            "A2": ["工作内容", "job description", "工作岗位", "工作地点"],
            "A3": ["工资", "salary", "劳动报酬", "薪酬"],
            "A4": ["工作时间", "working hours", "加班", "工时"],
            "A5": ["社保", "social insurance", "五险一金", "福利"],
            "B1": ["竞业限制", "non-compete", "竞业"],
            "B2": ["保密", "confidential", "保密条款"],
            "B3": ["培训", "training", "服务期"],
            "B4": ["知识产权", "intellectual property"],
            "C1": ["解除", "termination", "终止"],
            "C2": ["争议", "dispute", "仲裁"],
            "C3": ["违约", "breach", "违约金"],
        },
        "simple_rule_ids": {"A5", "B5", "C3"},
        "complex_rule_ids": {"A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4", "C1", "C2"},
        "prompt_templates": {
            "chapter_split": str(PROMPTS_DIR / "chapter_split.md"),
            "fact_labeling": str(PROMPTS_DIR / "fact_labeling.md"),
            "simple_review": str(PROMPTS_DIR / "simple_review.md"),
            "complex_review": str(PROMPTS_DIR / "complex_review.md"),
            "cross_check": str(PROMPTS_DIR / "cross_check.md"),
        },
    },
}


def get_document_type_config(document_type: str) -> dict:
    """Get configuration for a document type.

    Args:
        document_type: The document type key.

    Returns:
        Configuration dict for the given document type.

    Raises:
        KeyError: If the document type is not registered.
    """
    if document_type not in DOCUMENT_TYPE_CONFIGS:
        raise KeyError(f"Unknown document type: {document_type}. Available: {list(DOCUMENT_TYPE_CONFIGS.keys())}")
    return DOCUMENT_TYPE_CONFIGS[document_type]
