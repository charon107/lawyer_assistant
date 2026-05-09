"""Equity investment agreement review rule definitions — 13 rules across 3 categories."""

EQUITY_INVESTMENT_RULES = {
    # A. 基本要素审查
    "A1": {
        "id": "A1",
        "category": "基本要素",
        "title": "投资方与目标公司信息",
        "level": "中风险",
        "check": "投资方和目标公司名称、注册信息是否完整；目标公司现有股东结构；创始人信息",
        "suggestion_template": "载明投资方和目标公司完整工商信息；附目标公司股权结构图；明确创始人和实际控制人",
    },
    "A2": {
        "id": "A2",
        "category": "基本要素",
        "title": "投资金额与估值",
        "level": "高风险",
        "check": "投资金额是否明确；投前估值和投后估值是否载明；估值计算方法；股权比例是否与估值一致",
        "suggestion_template": "明确投资金额、投前/投后估值和计算方法；确认股权比例与估值的数学关系一致；约定估值调整机制",
    },
    "A3": {
        "id": "A3",
        "category": "基本要素",
        "title": "交割条件与时间",
        "level": "高风险",
        "check": "交割先决条件是否列举完整；交割日期或期限；工商变更登记义务；资金托管安排",
        "suggestion_template": "列举交割先决条件（尽调满意、审批通过等）；约定交割期限和延期条件；明确工商变更登记时限",
    },
    "A4": {
        "id": "A4",
        "category": "基本要素",
        "title": "资金用途",
        "level": "中风险",
        "check": "投资资金用途是否明确约定；是否限制特定用途；资金使用报告义务",
        "suggestion_template": "明确资金用途和禁止用途；约定资金使用报告义务和频率；投资方有权监督资金使用",
    },
    # B. 权利保护条款
    "B1": {
        "id": "B1",
        "category": "权利保护",
        "title": "反稀释保护",
        "level": "高风险",
        "check": "是否约定反稀释保护条款；反稀释方式（完全棘轮/加权平均）；例外情形是否合理",
        "suggestion_template": "约定反稀释保护条款和具体方式（建议加权平均法）；明确反稀释的例外情形（员工期权池等）",
    },
    "B2": {
        "id": "B2",
        "category": "权利保护",
        "title": "优先权条款",
        "level": "高风险",
        "check": "优先认购权/优先购买权/共同出售权/优先清算权是否约定；触发条件和行使程序",
        "suggestion_template": "约定优先认购权、优先购买权和共同出售权；明确触发条件、行使期限和程序",
    },
    "B3": {
        "id": "B3",
        "category": "权利保护",
        "title": "回购权",
        "level": "高风险",
        "check": "回购触发条件是否明确；回购价格计算方式；回购期限和付款方式",
        "suggestion_template": "明确回购触发条件（对赌未达标、创始人离职等）；回购价格按投资本金加合理回报计算",
    },
    "B4": {
        "id": "B4",
        "category": "权利保护",
        "title": "信息权与检查权",
        "level": "中风险",
        "check": "投资方的财务信息获取权；重大事项知情权；检查权和审计权",
        "suggestion_template": "约定投资方定期获取财务报告的权利；重大事项需投资方事先同意；保留检查和审计权",
    },
    # C. 法律合规
    "C1": {
        "id": "C1",
        "category": "法律合规",
        "title": "创始人承诺与限制",
        "level": "中风险",
        "check": "创始人竞业限制和全职义务；股权锁定和转让限制；关键人条款",
        "suggestion_template": "约定创始人竞业限制和全职义务；股权锁定期内不得转让；明确关键人士条款",
    },
    "C2": {
        "id": "C2",
        "category": "法律合规",
        "title": "陈述与保证",
        "level": "中风险",
        "check": "目标公司和创始人的陈述与保证是否完整；违反陈述保证的赔偿责任；披露义务",
        "suggestion_template": "目标公司和创始人应作出完整的陈述与保证；约定违反保证的赔偿责任和时效",
    },
    "C3": {
        "id": "C3",
        "category": "法律合规",
        "title": "争议解决",
        "level": "低风险",
        "check": "争议解决方式是否明确；适用法律是否约定",
        "suggestion_template": "明确约定仲裁或诉讼作为争议解决方式；约定适用中华人民共和国法律",
    },
}

EQUITY_INVESTMENT_RULE_IDS_BY_CATEGORY = {
    "基本要素": ["A1", "A2", "A3", "A4"],
    "权利保护": ["B1", "B2", "B3", "B4"],
    "法律合规": ["C1", "C2", "C3"],
}


def get_equity_investment_rule(rule_id: str) -> dict:
    """Look up a single equity investment rule definition."""
    return EQUITY_INVESTMENT_RULES.get(rule_id, {})


def get_all_equity_investment_rules() -> list:
    """Return all equity investment rules sorted by category."""
    result = []
    for category in ["基本要素", "权利保护", "法律合规"]:
        for rule_id in EQUITY_INVESTMENT_RULE_IDS_BY_CATEGORY[category]:
            result.append(EQUITY_INVESTMENT_RULES[rule_id])
    return result
