"""Marital property agreement review rule definitions — 11 rules across 3 categories."""

MARITAL_PROPERTY_RULES = {
    # A. 基本要素审查
    "A1": {
        "id": "A1",
        "category": "基本要素",
        "title": "双方身份信息",
        "level": "中风险",
        "check": "夫妻双方姓名、身份证号、婚姻状况是否完整；是否为合法夫妻关系；结婚证号是否载明",
        "suggestion_template": "载明双方完整身份信息和婚姻状况；附结婚证复印件；确认双方均为完全民事行为能力人",
    },
    "A2": {
        "id": "A2",
        "category": "基本要素",
        "title": "财产范围与清单",
        "level": "高风险",
        "check": "约定的财产范围是否明确；是否附财产清单（房产、车辆、存款、投资等）；财产价值是否注明；是否存在遗漏",
        "suggestion_template": "详细列明各项财产（名称、权属、价值）；附财产清单作为协议附件；约定新取得财产的归属原则",
    },
    "A3": {
        "id": "A3",
        "category": "基本要素",
        "title": "财产归属约定",
        "level": "高风险",
        "check": "各项财产归各自所有/共同所有/部分各自部分共同是否明确；约定是否具体到每项财产；是否存在歧义",
        "suggestion_template": "逐项明确财产归属；约定婚前财产和婚后取得财产的归属原则；避免模糊表述",
    },
    # B. 权利义务
    "B1": {
        "id": "B1",
        "category": "权利义务",
        "title": "债务承担",
        "level": "高风险",
        "check": "婚前债务和婚后债务的承担方式是否明确；共同债务的认定标准；对外债务的连带责任",
        "suggestion_template": "明确婚前债务各自承担；婚后共同债务的认定标准；约定对外债务的清偿责任（注意：不能对抗善意债权人）",
    },
    "B2": {
        "id": "B2",
        "category": "权利义务",
        "title": "收入管理与使用",
        "level": "中风险",
        "check": "双方收入的管理和使用方式；大额支出的决策权；家庭开支的分担比例",
        "suggestion_template": "约定收入管理方式（共同管理或各自管理）；大额支出需双方协商；明确家庭开支的分担方式",
    },
    "B3": {
        "id": "B3",
        "category": "权利义务",
        "title": "赠与和继承财产",
        "level": "中风险",
        "check": "赠与和继承取得的财产归属是否明确；是否排除为夫妻共同财产；遗嘱指定的处理",
        "suggestion_template": "明确赠与和继承财产的归属；约定是否纳入夫妻共同财产；尊重遗嘱或赠与合同中的指定",
    },
    "B4": {
        "id": "B4",
        "category": "权利义务",
        "title": "经济补偿与帮助",
        "level": "中风险",
        "check": "一方因抚育子女、照料老人等付出较多义务的补偿；离婚时的经济帮助条款",
        "suggestion_template": "约定家务劳动补偿机制；离婚时的经济帮助条件和方式；保护弱势一方的合法权益",
    },
    # C. 法律合规
    "C1": {
        "id": "C1",
        "category": "法律合规",
        "title": "协议变更与撤销",
        "level": "中风险",
        "check": "协议变更的条件和程序；是否存在撤销条件；变更是否需公证",
        "suggestion_template": "约定协议变更需双方书面同意；重大变更建议公证；明确协议撤销的条件",
    },
    "C2": {
        "id": "C2",
        "category": "法律合规",
        "title": "协议生效条件",
        "level": "中风险",
        "check": "协议是否约定自签署生效或办理公证后生效；公证是否为必要条件；未公证的法律效力",
        "suggestion_template": "建议办理公证以增强法律效力；约定协议生效条件；明确对双方的约束力",
    },
    "C3": {
        "id": "C3",
        "category": "法律合规",
        "title": "争议解决",
        "level": "低风险",
        "check": "争议解决方式是否明确",
        "suggestion_template": "约定争议解决方式（协商、调解、诉讼）；明确管辖法院",
    },
}

MARITAL_PROPERTY_RULE_IDS_BY_CATEGORY = {
    "基本要素": ["A1", "A2", "A3"],
    "权利义务": ["B1", "B2", "B3", "B4"],
    "法律合规": ["C1", "C2", "C3"],
}


def get_marital_property_rule(rule_id: str) -> dict:
    """Look up a single marital property rule definition."""
    return MARITAL_PROPERTY_RULES.get(rule_id, {})


def get_all_marital_property_rules() -> list:
    """Return all marital property rules sorted by category."""
    result = []
    for category in ["基本要素", "权利义务", "法律合规"]:
        for rule_id in MARITAL_PROPERTY_RULE_IDS_BY_CATEGORY[category]:
            result.append(MARITAL_PROPERTY_RULES[rule_id])
    return result
