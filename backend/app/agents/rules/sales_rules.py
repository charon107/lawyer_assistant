"""Sales/purchase agreement review rule definitions — 12 rules across 3 categories."""

SALES_RULES = {
    # A. 基本要素审查
    "A1": {
        "id": "A1",
        "category": "基本要素",
        "title": "买卖双方信息",
        "level": "中风险",
        "check": "买卖双方名称、地址、联系方式是否完整；法定代表人或授权代理人是否载明；营业执照信息是否一致",
        "suggestion_template": "载明双方完整工商注册信息；授权代理人需附授权委托书；确认签约主体与实际经营主体一致",
    },
    "A2": {
        "id": "A2",
        "category": "基本要素",
        "title": "标的物信息",
        "level": "高风险",
        "check": "商品名称、规格、型号、数量、质量标准是否明确；是否附技术规格书或样品说明；标的物所有权转移时间",
        "suggestion_template": "详细描述标的物规格参数；附技术规格书作为合同附件；明确所有权转移的时间节点",
    },
    "A3": {
        "id": "A3",
        "category": "基本要素",
        "title": "价格与付款",
        "level": "高风险",
        "check": "单价和总价是否明确；含税/不含税价格是否区分；付款方式、付款节点是否清晰；是否约定价格调整机制",
        "suggestion_template": "明确单价、总价和税率；分阶段付款应明确各节点金额；价格调整需约定触发条件和上限",
    },
    "A4": {
        "id": "A4",
        "category": "基本要素",
        "title": "交付与验收",
        "level": "高风险",
        "check": "交付时间、地点、方式是否明确；运输方式和费用承担；验收标准和验收期限；风险转移时间点",
        "suggestion_template": "明确交付时间和地点；约定运输方式及费用承担；验收期不超过收货后15日；明确风险转移时间点",
    },
    # B. 权利义务与风险
    "B1": {
        "id": "B1",
        "category": "权利义务",
        "title": "质量保证与售后服务",
        "level": "中风险",
        "check": "质量保证期限和范围是否明确；退换货条件是否约定；售后服务内容和响应时限",
        "suggestion_template": "明确质保期限和质保范围；约定退换货条件和流程；售后服务响应时限不超过48小时",
    },
    "B2": {
        "id": "B2",
        "category": "权利义务",
        "title": "违约责任",
        "level": "高风险",
        "check": "逾期交货/逾期付款的违约金是否合理；质量不符的违约责任；根本违约的解除权和赔偿",
        "suggestion_template": "逾期违约金不超过合同总额的万分之五/日；质量不符应约定退换或降价；根本违约可解除合同并要求赔偿",
    },
    "B3": {
        "id": "B3",
        "category": "权利义务",
        "title": "知识产权",
        "level": "中风险",
        "check": "标的物涉及的知识产权归属是否明确；卖方是否提供知识产权不侵权担保；买方的使用范围限制",
        "suggestion_template": "卖方应担保标的物不侵犯第三方知识产权；约定侵权责任的承担方式；明确买方的使用范围",
    },
    "B4": {
        "id": "B4",
        "category": "权利义务",
        "title": "保密条款",
        "level": "低风险",
        "check": "交易信息和商业秘密的保密义务是否约定；保密期限和范围；违反保密义务的责任",
        "suggestion_template": "约定交易信息保密义务；保密期限建议至合同终止后2年；明确违反保密义务的违约责任",
    },
    # C. 法律合规
    "C1": {
        "id": "C1",
        "category": "法律合规",
        "title": "不可抗力",
        "level": "中风险",
        "check": "不可抗力定义是否合理；通知义务和证明义务是否明确；不可抗力对交货和付款的影响",
        "suggestion_template": "不可抗力应包含自然灾害、战争、政策变化等；约定通知期限和证明文件要求；明确不可抗力期间的义务",
    },
    "C2": {
        "id": "C2",
        "category": "法律合规",
        "title": "合同终止与解除",
        "level": "中风险",
        "check": "合同终止条件是否列举完整；单方解除权是否对等；终止后的退货、退款和清算安排",
        "suggestion_template": "明确合同终止情形；双方享有对等解除权；约定终止后的退货退款和清算程序",
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

SALES_RULE_IDS_BY_CATEGORY = {
    "基本要素": ["A1", "A2", "A3", "A4"],
    "权利义务": ["B1", "B2", "B3", "B4"],
    "法律合规": ["C1", "C2", "C3"],
}


def get_sales_rule(rule_id: str) -> dict:
    """Look up a single sales rule definition."""
    return SALES_RULES.get(rule_id, {})


def get_all_sales_rules() -> list:
    """Return all sales rules sorted by category."""
    result = []
    for category in ["基本要素", "权利义务", "法律合规"]:
        for rule_id in SALES_RULE_IDS_BY_CATEGORY[category]:
            result.append(SALES_RULES[rule_id])
    return result
