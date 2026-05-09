"""Will and estate review rule definitions — 11 rules across 3 categories."""

WILL_ESTATE_RULES = {
    # A. 基本要素审查
    "A1": {
        "id": "A1",
        "category": "基本要素",
        "title": "立遗嘱人信息",
        "level": "中风险",
        "check": "立遗嘱人姓名、身份证号是否完整；立遗嘱时是否具有完全民事行为能力；是否为遗嘱人真实意思表示",
        "suggestion_template": "载明立遗嘱人完整身份信息；确认立遗嘱时具有完全民事行为能力；建议附精神状态证明（如适用）",
    },
    "A2": {
        "id": "A2",
        "category": "基本要素",
        "title": "遗产范围",
        "level": "高风险",
        "check": "遗产范围是否明确；是否附遗产清单（房产、存款、投资、车辆等）；是否存在遗漏财产；是否处分了他人财产",
        "suggestion_template": "详细列明遗产清单（名称、权属、价值）；确认遗产为遗嘱人个人合法财产；不得处分他人财产",
    },
    "A3": {
        "id": "A3",
        "category": "基本要素",
        "title": "继承人指定",
        "level": "高风险",
        "check": "继承人身份信息是否明确；是否保留了缺乏劳动能力又没有生活来源的继承人的必要份额；遗赠对象是否合法",
        "suggestion_template": "明确继承人身份信息；必须保留缺乏劳动能力又没有生活来源的继承人的必要份额（必留份）",
    },
    # B. 遗嘱形式与效力
    "B1": {
        "id": "B1",
        "category": "遗嘱效力",
        "title": "遗嘱形式",
        "level": "高风险",
        "check": "遗嘱形式（自书/代书/打印/录音录像/口头/公证）是否符合法定要求；各形式的特殊要件是否满足",
        "suggestion_template": "确认遗嘱形式符合民法典要求；自书遗嘱需全文亲笔书写并签名注明年月日；代书/打印遗嘱需两个以上见证人",
    },
    "B2": {
        "id": "B2",
        "category": "遗嘱效力",
        "title": "见证人资格",
        "level": "高风险",
        "check": "见证人是否具备法定资格；见证人人数是否符合要求（两人以上）；是否存在利害关系人作为见证人",
        "suggestion_template": "见证人需具有完全民事行为能力且与继承无利害关系；见证人不得为继承人、受遗赠人及其近亲属",
    },
    "B3": {
        "id": "B3",
        "category": "遗嘱效力",
        "title": "遗嘱内容合法性",
        "level": "中风险",
        "check": "遗嘱内容是否违反法律强制性规定；是否损害社会公共利益；遗嘱附加条件是否合法",
        "suggestion_template": "遗嘱内容不得违反法律强制性规定；不得损害社会公共利益；附加条件不得违法或违背公序良俗",
    },
    # C. 法律合规
    "C1": {
        "id": "C1",
        "category": "法律合规",
        "title": "遗嘱变更与撤销",
        "level": "中风险",
        "check": "是否存在多份遗嘱；多份遗嘱的效力冲突处理；遗嘱的变更和撤销方式",
        "suggestion_template": "立有数份遗嘱内容相抵触的以最后的遗嘱为准；变更或撤销遗嘱应采用与原遗嘱相同或更严格的形式",
    },
    "C2": {
        "id": "C2",
        "category": "法律合规",
        "title": "遗嘱执行",
        "level": "中风险",
        "check": "是否指定遗嘱执行人；遗嘱执行人的职责和权限；遗产分割方式和时间",
        "suggestion_template": "建议指定遗嘱执行人并明确职责；约定遗产分割方式和时间；遗嘱执行人应忠实执行遗嘱",
    },
    "C3": {
        "id": "C3",
        "category": "法律合规",
        "title": "债务清偿",
        "level": "中风险",
        "check": "遗产债务的清偿顺序；继承人是否在继承遗产范围内承担债务；放弃继承的债务处理",
        "suggestion_template": "遗产应先清偿债务再分配；继承人在继承遗产实际价值范围内承担债务；放弃继承的不承担债务",
    },
}

WILL_ESTATE_RULE_IDS_BY_CATEGORY = {
    "基本要素": ["A1", "A2", "A3"],
    "遗嘱效力": ["B1", "B2", "B3"],
    "法律合规": ["C1", "C2", "C3"],
}


def get_will_estate_rule(rule_id: str) -> dict:
    """Look up a single will/estate rule definition."""
    return WILL_ESTATE_RULES.get(rule_id, {})


def get_all_will_estate_rules() -> list:
    """Return all will/estate rules sorted by category."""
    result = []
    for category in ["基本要素", "遗嘱效力", "法律合规"]:
        for rule_id in WILL_ESTATE_RULE_IDS_BY_CATEGORY[category]:
            result.append(WILL_ESTATE_RULES[rule_id])
    return result
