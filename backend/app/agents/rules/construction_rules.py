"""Construction contract review rule definitions — 13 rules across 3 categories."""

CONSTRUCTION_RULES = {
    # A. 基本要素审查
    "A1": {
        "id": "A1",
        "category": "基本要素",
        "title": "发包方与承包方信息",
        "level": "中风险",
        "check": "发包方和承包方名称、资质等级是否完整；承包方是否具备相应施工资质；项目经理是否指定",
        "suggestion_template": "确认承包方资质等级与工程规模匹配；载明项目经理信息；附承包方资质证书复印件",
    },
    "A2": {
        "id": "A2",
        "category": "基本要素",
        "title": "工程范围与内容",
        "level": "高风险",
        "check": "工程名称、地点、规模、内容是否明确；施工图纸和技术标准是否作为合同附件；工程量清单是否完整",
        "suggestion_template": "详细描述工程范围和内容；施工图纸和技术标准作为合同附件；附完整的工程量清单",
    },
    "A3": {
        "id": "A3",
        "category": "基本要素",
        "title": "工期与进度",
        "level": "高风险",
        "check": "开工日期、竣工日期是否明确；工期延误的责任和免责情形；关键节点的进度要求；工期顺延条件",
        "suggestion_template": "明确开工和竣工日期；约定工期延误的违约责任和免责情形；明确工期顺延的条件和审批程序",
    },
    "A4": {
        "id": "A4",
        "category": "基本要素",
        "title": "工程价款与支付",
        "level": "高风险",
        "check": "合同价款（固定总价/固定单价/成本加酬金）是否明确；预付款比例和扣回方式；进度款支付节点和比例；结算方式",
        "suggestion_template": "明确计价方式和合同价款；预付款不超过合同价的30%；进度款按月或按节点支付；约定竣工结算时限",
    },
    # B. 质量与风险
    "B1": {
        "id": "B1",
        "category": "质量与风险",
        "title": "质量标准与验收",
        "level": "高风险",
        "check": "质量标准（合格/优良）是否明确；验收程序和时限；质量保修期和保修范围；不合格工程的处理",
        "suggestion_template": "明确质量标准和验收程序；约定质量保修期（基础设施工程和房屋建筑的地基基础和主体结构为设计文件规定的合理使用年限）；不合格工程应返工",
    },
    "B2": {
        "id": "B2",
        "category": "质量与风险",
        "title": "安全施工与文明施工",
        "level": "中风险",
        "check": "安全施工责任划分；安全事故的处理和赔偿；文明施工要求；环境保护措施",
        "suggestion_template": "承包方负责施工现场安全；约定安全事故的处理程序和赔偿责任；明确文明施工和环保要求",
    },
    "B3": {
        "id": "B3",
        "category": "质量与风险",
        "title": "工程变更",
        "level": "中风险",
        "check": "工程变更的审批程序；变更引起的工期和费用调整；签证管理要求",
        "suggestion_template": "约定工程变更的审批程序和权限；变更引起的工期和费用调整应书面确认；明确签证管理要求",
    },
    "B4": {
        "id": "B4",
        "category": "质量与风险",
        "title": "分包管理",
        "level": "中风险",
        "check": "是否允许分包；分包范围和限制；分包方的资质要求；承包方对分包方的管理责任",
        "suggestion_template": "分包须经发包方同意；分包方应具备相应资质；承包方对分包工程承担连带责任",
    },
    # C. 法律合规
    "C1": {
        "id": "C1",
        "category": "法律合规",
        "title": "违约责任",
        "level": "中风险",
        "check": "工期延误、质量不合格、逾期付款的违约责任；违约金计算方式；违约解除权",
        "suggestion_template": "约定工期延误和质量不合格的违约责任；逾期付款违约金不超过LPR的四倍；明确违约解除条件",
    },
    "C2": {
        "id": "C2",
        "category": "法律合规",
        "title": "竣工验收与结算",
        "level": "高风险",
        "check": "竣工验收程序和时限；结算审核期限；发包方逾期审核的后果；质保金比例和返还条件",
        "suggestion_template": "约定竣工验收程序和时限；结算审核不超过28日；逾期审核视为认可结算报告；质保金不超过结算价的3%",
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

CONSTRUCTION_RULE_IDS_BY_CATEGORY = {
    "基本要素": ["A1", "A2", "A3", "A4"],
    "质量与风险": ["B1", "B2", "B3", "B4"],
    "法律合规": ["C1", "C2", "C3"],
}


def get_construction_rule(rule_id: str) -> dict:
    """Look up a single construction rule definition."""
    return CONSTRUCTION_RULES.get(rule_id, {})


def get_all_construction_rules() -> list:
    """Return all construction rules sorted by category."""
    result = []
    for category in ["基本要素", "质量与风险", "法律合规"]:
        for rule_id in CONSTRUCTION_RULE_IDS_BY_CATEGORY[category]:
            result.append(CONSTRUCTION_RULES[rule_id])
    return result
