"""Articles of association review rule definitions — 12 rules across 3 categories."""

ARTICLES_OF_ASSOCIATION_RULES = {
    # A. 基本要素审查
    "A1": {
        "id": "A1",
        "category": "基本要素",
        "title": "公司基本信息",
        "level": "中风险",
        "check": "公司名称、住所、经营范围是否明确；注册资本和实缴资本是否载明；公司类型（有限/股份）是否确定",
        "suggestion_template": "载明公司名称、住所和经营范围；明确注册资本和出资方式；确定公司类型",
    },
    "A2": {
        "id": "A2",
        "category": "基本要素",
        "title": "股东信息与出资",
        "level": "高风险",
        "check": "股东姓名/名称、出资额、出资方式、出资时间是否明确；非货币出资的评估和过户；出资瑕疵的责任",
        "suggestion_template": "载明各股东出资额、出资方式和出资时间；非货币出资应经评估并办理过户；约定出资瑕疵的违约责任",
    },
    "A3": {
        "id": "A3",
        "category": "基本要素",
        "title": "组织机构设置",
        "level": "中风险",
        "check": "股东会/股东大会、董事会/执行董事、监事会/监事的职权和议事规则是否明确；法定代表人产生方式",
        "suggestion_template": "明确各组织机构的职权范围和议事规则；约定法定代表人的产生和变更程序",
    },
    "A4": {
        "id": "A4",
        "category": "基本要素",
        "title": "利润分配",
        "level": "中风险",
        "check": "利润分配原则和比例是否明确；分配时间是否约定；是否约定优先分配权或特殊分配安排",
        "suggestion_template": "明确利润分配原则（一般按出资比例）；约定分配时间和频率；特殊分配安排需全体股东同意",
    },
    # B. 股东权利与限制
    "B1": {
        "id": "B1",
        "category": "股东权利",
        "title": "股权转让限制",
        "level": "高风险",
        "check": "股东对外转让股权的限制条件；优先购买权的行使程序和期限；转让价格的确定方式",
        "suggestion_template": "对外转让需其他股东过半数同意；其他股东享有优先购买权；约定转让价格的确定方式（评估或协商）",
    },
    "B2": {
        "id": "B2",
        "category": "股东权利",
        "title": "股东退出机制",
        "level": "中风险",
        "check": "股东退出的方式（转让/回购/减资）；强制退出条件；退出价格的确定",
        "suggestion_template": "约定股东退出的方式和条件；明确强制退出的情形（如违法犯罪）；退出价格应经评估或按约定公式",
    },
    "B3": {
        "id": "B3",
        "category": "股东权利",
        "title": "知情权与监督权",
        "level": "中风险",
        "check": "股东的财务信息获取权；查阅公司账簿和文件的权利；质询权和建议权",
        "suggestion_template": "保障股东查阅公司章程、股东会会议记录和财务报告的权利；约定信息提供的频率和方式",
    },
    "B4": {
        "id": "B4",
        "category": "股东权利",
        "title": "竞业禁止与同业竞争",
        "level": "中风险",
        "check": "股东和高管的竞业禁止义务；同业竞争的限制范围和期限；违反竞业禁止的后果",
        "suggestion_template": "约定股东和高管的竞业禁止义务；明确限制范围和期限；违反竞业禁止应赔偿公司损失",
    },
    # C. 法律合规
    "C1": {
        "id": "C1",
        "category": "法律合规",
        "title": "公司僵局处理",
        "level": "中风险",
        "check": "股东会无法形成有效决议的处理机制；董事会僵局的解决方式；公司解散条件",
        "suggestion_template": "约定股东会僵局的处理机制（如调解、仲裁）；明确公司解散的条件和清算程序",
    },
    "C2": {
        "id": "C2",
        "category": "法律合规",
        "title": "章程修改程序",
        "level": "低风险",
        "check": "章程修改的表决比例是否符合公司法要求；修改程序是否明确；重要条款修改的特别要求",
        "suggestion_template": "章程修改须经代表三分之二以上表决权的股东通过；明确修改提案和通知程序",
    },
    "C3": {
        "id": "C3",
        "category": "法律合规",
        "title": "争议解决",
        "level": "低风险",
        "check": "股东之间争议的解决方式；股东与公司之间争议的解决方式",
        "suggestion_template": "约定股东之间及股东与公司之间的争议解决方式（仲裁或诉讼）",
    },
}

ARTICLES_OF_ASSOCIATION_RULE_IDS_BY_CATEGORY = {
    "基本要素": ["A1", "A2", "A3", "A4"],
    "股东权利": ["B1", "B2", "B3", "B4"],
    "法律合规": ["C1", "C2", "C3"],
}


def get_articles_of_association_rule(rule_id: str) -> dict:
    """Look up a single articles of association rule definition."""
    return ARTICLES_OF_ASSOCIATION_RULES.get(rule_id, {})


def get_all_articles_of_association_rules() -> list:
    """Return all articles of association rules sorted by category."""
    result = []
    for category in ["基本要素", "股东权利", "法律合规"]:
        for rule_id in ARTICLES_OF_ASSOCIATION_RULE_IDS_BY_CATEGORY[category]:
            result.append(ARTICLES_OF_ASSOCIATION_RULES[rule_id])
    return result
