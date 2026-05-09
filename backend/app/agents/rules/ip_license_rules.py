"""IP license agreement review rule definitions — 12 rules across 3 categories."""

IP_LICENSE_RULES = {
    # A. 基本要素审查
    "A1": {
        "id": "A1",
        "category": "基本要素",
        "title": "许可方与被许可方信息",
        "level": "中风险",
        "check": "许可方是否为知识产权权利人或合法代理人；被许可方身份信息是否完整；共有权利是否所有共有人同意",
        "suggestion_template": "确认许可方权利人身份或代理权限；载明双方完整身份信息；共有权利需全部共有人书面同意",
    },
    "A2": {
        "id": "A2",
        "category": "基本要素",
        "title": "许可知识产权描述",
        "level": "高风险",
        "check": "许可的知识产权类型（专利/商标/著作权/商业秘密）是否明确；权利证书编号是否载明；权利范围和有效期",
        "suggestion_template": "明确知识产权类型和权利证书编号；载明权利有效期和保护范围；附权利证书复印件",
    },
    "A3": {
        "id": "A3",
        "category": "基本要素",
        "title": "许可范围与方式",
        "level": "高风险",
        "check": "许可方式（独占/排他/普通）是否明确；许可地域范围是否限定；许可使用领域是否约定；是否允许分许可",
        "suggestion_template": "明确许可方式（独占/排他/普通）；限定许可地域和使用领域；分许可需经许可方书面同意",
    },
    "A4": {
        "id": "A4",
        "category": "基本要素",
        "title": "许可期限",
        "level": "中风险",
        "check": "许可期限是否明确；是否超过知识产权有效期；续期条件是否约定；提前终止条件",
        "suggestion_template": "许可期限不超过知识产权有效期；约定续期条件和费用；提前终止需合理通知期",
    },
    # B. 费用与风险
    "B1": {
        "id": "B1",
        "category": "费用与风险",
        "title": "许可费用",
        "level": "高风险",
        "check": "许可费计算方式（一次性/按销售额提成/固定年费）是否明确；支付周期和方式；审计权是否约定",
        "suggestion_template": "明确许可费计算方式和支付条件；按销售额提成的应约定审计权；明确最低保证金或最低使用费",
    },
    "B2": {
        "id": "B2",
        "category": "费用与风险",
        "title": "知识产权保护义务",
        "level": "高风险",
        "check": "被许可方的知识产权保护义务；侵权发现的通知义务；维权费用的承担方式",
        "suggestion_template": "被许可方有义务保护知识产权完整性；发现侵权应及时通知；约定维权费用的承担方式和比例",
    },
    "B3": {
        "id": "B3",
        "category": "费用与风险",
        "title": "改进技术归属",
        "level": "中风险",
        "check": "被许可方改进技术的知识产权归属；改进技术的回授义务（grant-back）；是否对等",
        "suggestion_template": "明确改进技术的知识产权归属；回授条款应公平对等；被许可方的改进应获得合理补偿",
    },
    "B4": {
        "id": "B4",
        "category": "费用与风险",
        "title": "保密义务",
        "level": "中风险",
        "check": "商业秘密和专有技术的保密义务；保密范围和期限；保密信息的使用限制",
        "suggestion_template": "明确保密信息范围和保护措施；保密期限至合同终止后3-5年；限制保密信息的使用目的",
    },
    # C. 法律合规
    "C1": {
        "id": "C1",
        "category": "法律合规",
        "title": "违约与终止",
        "level": "中风险",
        "check": "违约情形是否列举完整；终止后被许可方的停止使用义务；库存产品的处理；权利回转",
        "suggestion_template": "列举主要违约情形和救济措施；终止后应立即停止使用并销毁相关材料；约定库存产品的处理期限",
    },
    "C2": {
        "id": "C2",
        "category": "法律合规",
        "title": "不侵权保证",
        "level": "中风险",
        "check": "许可方是否保证不侵犯第三方权利；第三方主张权利时的责任分担；被许可方的免责保护",
        "suggestion_template": "许可方应保证知识产权不侵犯第三方权利；第三方主张权利时由许可方负责应对和赔偿",
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

IP_LICENSE_RULE_IDS_BY_CATEGORY = {
    "基本要素": ["A1", "A2", "A3", "A4"],
    "费用与风险": ["B1", "B2", "B3", "B4"],
    "法律合规": ["C1", "C2", "C3"],
}


def get_ip_license_rule(rule_id: str) -> dict:
    """Look up a single IP license rule definition."""
    return IP_LICENSE_RULES.get(rule_id, {})


def get_all_ip_license_rules() -> list:
    """Return all IP license rules sorted by category."""
    result = []
    for category in ["基本要素", "费用与风险", "法律合规"]:
        for rule_id in IP_LICENSE_RULE_IDS_BY_CATEGORY[category]:
            result.append(IP_LICENSE_RULES[rule_id])
    return result
