"""Loan agreement review rule definitions — 12 rules across 3 categories."""

LOAN_RULES = {
    # A. 基本要素审查
    "A1": {
        "id": "A1",
        "category": "基本要素",
        "title": "借贷双方信息",
        "level": "中风险",
        "check": "出借人和借款人身份信息是否完整；自然人需身份证号，法人需统一社会信用代码；代理人是否有授权委托书",
        "suggestion_template": "载明双方完整身份信息；法人借款需加盖公章并由法定代表人签字；代理人需附授权委托书",
    },
    "A2": {
        "id": "A2",
        "category": "基本要素",
        "title": "借款金额与币种",
        "level": "高风险",
        "check": "借款金额大小写是否一致；币种是否明确；是否包含多种币种或汇率约定",
        "suggestion_template": "借款金额应大小写一致并注明币种；涉及外币的应约定汇率基准和结算方式",
    },
    "A3": {
        "id": "A3",
        "category": "基本要素",
        "title": "借款期限",
        "level": "中风险",
        "check": "借款起止日期是否明确；是否存在提前还款条款；展期条件是否约定",
        "suggestion_template": "明确借款发放日和到期日；约定提前还款的通知期和手续费；展期需双方书面同意",
    },
    "A4": {
        "id": "A4",
        "category": "基本要素",
        "title": "利率与利息",
        "level": "高风险",
        "check": "利率是否明确（年利率/月利率）；是否超过法定上限（LPR四倍）；利息计算方式和付息周期；是否约定复利",
        "suggestion_template": "明确年利率数值；利率不超过合同成立时一年期LPR四倍；约定利息计算方式和付息日期；谨慎约定复利条款",
    },
    # B. 担保与风险
    "B1": {
        "id": "B1",
        "category": "担保与风险",
        "title": "担保方式",
        "level": "高风险",
        "check": "是否约定担保方式（保证/抵押/质押）；担保人信息是否完整；担保范围和期限是否明确",
        "suggestion_template": "明确担保方式和担保范围；保证担保应约定保证期间；抵押/质押应办理登记手续",
    },
    "B2": {
        "id": "B2",
        "category": "担保与风险",
        "title": "还款方式",
        "level": "中风险",
        "check": "还款方式（等额本息/等额本金/到期一次还本付息/分期付息到期还本）是否明确；还款账户信息是否载明",
        "suggestion_template": "明确还款方式和每期还款金额；载明还款账户信息；约定还款顺序（先息后本或先本后息）",
    },
    "B3": {
        "id": "B3",
        "category": "担保与风险",
        "title": "违约责任",
        "level": "高风险",
        "check": "逾期还款的罚息利率是否合理；违约情形是否列举完整；违约救济措施是否充分",
        "suggestion_template": "罚息利率不超过合同利率的1.5倍；列举主要违约情形；约定提前收回借款的权利和条件",
    },
    "B4": {
        "id": "B4",
        "category": "担保与风险",
        "title": "借款用途",
        "level": "中风险",
        "check": "借款用途是否明确约定；是否限制特定用途；出借人是否有监督权",
        "suggestion_template": "明确借款用途并约定不得挪用；出借人有权监督资金使用；挪用借款可视为违约",
    },
    # C. 法律合规
    "C1": {
        "id": "C1",
        "category": "法律合规",
        "title": "合同生效条件",
        "level": "中风险",
        "check": "合同生效条件是否明确（签署生效/附条件生效）；自然人之间的借款合同是否以实际交付为生效要件",
        "suggestion_template": "明确合同生效条件；自然人之间借款以款项实际交付为生效要件；建议通过银行转账交付并保留凭证",
    },
    "C2": {
        "id": "C2",
        "category": "法律合规",
        "title": "争议解决",
        "level": "低风险",
        "check": "争议解决方式是否明确；管辖法院或仲裁机构是否约定",
        "suggestion_template": "明确约定仲裁或诉讼作为争议解决方式；选择仲裁应指定具体仲裁机构",
    },
    "C3": {
        "id": "C3",
        "category": "法律合规",
        "title": "税费承担",
        "level": "低风险",
        "check": "借款相关的税费（印花税等）承担是否明确",
        "suggestion_template": "明确借款合同印花税的承担方；约定其他可能产生的税费承担方式",
    },
}

LOAN_RULE_IDS_BY_CATEGORY = {
    "基本要素": ["A1", "A2", "A3", "A4"],
    "担保与风险": ["B1", "B2", "B3", "B4"],
    "法律合规": ["C1", "C2", "C3"],
}


def get_loan_rule(rule_id: str) -> dict:
    """Look up a single loan rule definition."""
    return LOAN_RULES.get(rule_id, {})


def get_all_loan_rules() -> list:
    """Return all loan rules sorted by category."""
    result = []
    for category in ["基本要素", "担保与风险", "法律合规"]:
        for rule_id in LOAN_RULE_IDS_BY_CATEGORY[category]:
            result.append(LOAN_RULES[rule_id])
    return result
