"""Service agreement review rule definitions — 12 rules across 3 categories."""

SERVICE_RULES = {
    # A. 基本要素审查
    "A1": {
        "id": "A1",
        "category": "基本要素",
        "title": "服务双方信息",
        "level": "中风险",
        "check": "委托方和受托方名称、地址、联系方式是否完整；受托方资质或许可证是否载明；签约代表授权是否有效",
        "suggestion_template": "载明双方完整工商信息；受托方应提供相关资质证明；授权代理人需附授权委托书",
    },
    "A2": {
        "id": "A2",
        "category": "基本要素",
        "title": "服务内容与范围",
        "level": "高风险",
        "check": "服务内容描述是否具体明确；服务范围边界是否清晰；是否包含排除事项；服务成果的交付标准",
        "suggestion_template": "详细描述服务内容和交付物；明确服务范围的边界和排除事项；约定服务成果的验收标准",
    },
    "A3": {
        "id": "A3",
        "category": "基本要素",
        "title": "服务期限",
        "level": "中风险",
        "check": "服务起止日期是否明确；是否分阶段交付；延期条件和程序是否约定；提前终止条件",
        "suggestion_template": "明确服务起止日期和各阶段里程碑；约定延期的条件和审批程序；提前终止需合理通知期",
    },
    "A4": {
        "id": "A4",
        "category": "基本要素",
        "title": "服务费用与支付",
        "level": "高风险",
        "check": "服务费用（固定费用/按时间计费/按成果计费）是否明确；付款节点与服务里程碑是否挂钩；差旅等额外费用承担",
        "suggestion_template": "明确计费方式和总费用；付款节点与服务交付里程碑挂钩；约定差旅等额外费用的承担方式和上限",
    },
    # B. 权利义务与风险
    "B1": {
        "id": "B1",
        "category": "权利义务",
        "title": "服务标准与考核",
        "level": "中风险",
        "check": "服务质量标准是否量化或可衡量；KPI或SLA是否约定；不合格服务的处理方式",
        "suggestion_template": "约定可量化的服务质量标准（KPI/SLA）；不合格服务应有整改期和扣款机制；定期进行服务评估",
    },
    "B2": {
        "id": "B2",
        "category": "权利义务",
        "title": "人员配置与替换",
        "level": "中风险",
        "check": "服务团队核心成员是否指定；人员替换条件和审批程序；关键人员变更的通知义务",
        "suggestion_template": "指定核心服务团队成员；人员替换需提前通知并经委托方同意；约定人员资质要求",
    },
    "B3": {
        "id": "B3",
        "category": "权利义务",
        "title": "保密与数据保护",
        "level": "高风险",
        "check": "保密范围是否明确；受托方接触的数据和信息的保护义务；数据泄露的责任和通知义务",
        "suggestion_template": "明确保密信息范围和保护措施；约定数据泄露的通知时限和赔偿责任；服务终止后的信息返还或销毁",
    },
    "B4": {
        "id": "B4",
        "category": "权利义务",
        "title": "知识产权归属",
        "level": "高风险",
        "check": "服务成果的知识产权归属是否明确；背景知识产权的许可使用；受托方工具和方法的知识产权",
        "suggestion_template": "服务成果知识产权归委托方所有；背景知识产权各自保留；受托方保留其工具和方法的知识产权",
    },
    # C. 法律合规
    "C1": {
        "id": "C1",
        "category": "法律合规",
        "title": "违约责任",
        "level": "中风险",
        "check": "违约情形是否列举完整；违约金或赔偿计算方式是否合理；违约救济措施是否充分",
        "suggestion_template": "列举主要违约情形和对应责任；违约金不超过合同总额的30%；保留要求继续履行的权利",
    },
    "C2": {
        "id": "C2",
        "category": "法律合规",
        "title": "合同终止与交接",
        "level": "中风险",
        "check": "合同终止条件是否完整；终止后的交接期安排；未完成工作的处理；知识转移义务",
        "suggestion_template": "约定终止通知期（建议30天）；明确交接期的工作安排和费用；约定知识转移和文档移交义务",
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

SERVICE_RULE_IDS_BY_CATEGORY = {
    "基本要素": ["A1", "A2", "A3", "A4"],
    "权利义务": ["B1", "B2", "B3", "B4"],
    "法律合规": ["C1", "C2", "C3"],
}


def get_service_rule(rule_id: str) -> dict:
    """Look up a single service rule definition."""
    return SERVICE_RULES.get(rule_id, {})


def get_all_service_rules() -> list:
    """Return all service rules sorted by category."""
    result = []
    for category in ["基本要素", "权利义务", "法律合规"]:
        for rule_id in SERVICE_RULE_IDS_BY_CATEGORY[category]:
            result.append(SERVICE_RULES[rule_id])
    return result
