"""Employment contract (劳动合同) review rule definitions — 12 rules across 3 categories."""

EMPLOYMENT_RULES = {
    # A. 基本要素审查
    "A1": {
        "id": "A1",
        "category": "基本要素",
        "title": "劳动合同期限",
        "level": "中风险",
        "check": "合同期限是否明确（固定期限/无固定期限/以完成一定工作任务为期限）；试用期是否符合法律规定；续签条件是否清晰",
        "suggestion_template": "固定期限合同应明确起止日期；试用期不得超过法定上限（合同1年试用期不超过1个月，3年不超过6个月）；续签应双方协商一致"
    },
    "A2": {
        "id": "A2",
        "category": "基本要素",
        "title": "工作内容与地点",
        "level": "中风险",
        "check": "工作岗位和职责是否明确；工作地点是否具体；调岗调薪条款是否合理",
        "suggestion_template": "明确约定工作岗位和主要职责；工作地点应具体到城市；调岗应经双方协商一致并书面确认"
    },
    "A3": {
        "id": "A3",
        "category": "基本要素",
        "title": "劳动报酬",
        "level": "高风险",
        "check": "工资标准是否不低于当地最低工资；工资构成（基本工资+绩效+津贴）是否清晰；发薪日期和方式是否明确",
        "suggestion_template": "工资标准不得低于当地最低工资标准；明确工资构成及各部分金额；约定发薪日期（建议每月固定日期）"
    },
    "A4": {
        "id": "A4",
        "category": "基本要素",
        "title": "工作时间与休息",
        "level": "中风险",
        "check": "工时制度是否明确（标准/综合计算/不定时）；加班费计算基数是否合法；休息休假权利是否保障",
        "suggestion_template": "明确约定工时制度；加班费计算基数不得低于当地最低工资标准；保障法定带薪年假、婚假、产假等权利"
    },
    "A5": {
        "id": "A5",
        "category": "基本要素",
        "title": "社会保险与福利",
        "level": "中风险",
        "check": "五险一金是否依法缴纳；是否有补充商业保险；福利待遇是否明确",
        "suggestion_template": "依法缴纳五险一金（养老、医疗、失业、工伤、生育保险及住房公积金）；补充福利应书面明确"
    },

    # B. 权利义务与限制
    "B1": {
        "id": "B1",
        "category": "权利义务",
        "title": "竞业限制",
        "level": "高风险",
        "check": "竞业限制范围、地域、期限是否合理；竞业限制补偿金是否约定（不低于月均工资30%）；期限是否超过2年",
        "suggestion_template": "竞业限制应有合理范围和地域限制；期限不超过2年；须约定竞业限制补偿金（不低于离职前12个月平均工资的30%）"
    },
    "B2": {
        "id": "B2",
        "category": "权利义务",
        "title": "保密条款",
        "level": "中风险",
        "check": "保密范围是否明确；保密期限是否合理；保密义务与竞业限制是否有重叠",
        "suggestion_template": "明确保密信息的范围和保密期限；保密义务不因劳动合同终止而免除（合理期限内）；与竞业限制条款相互独立"
    },
    "B3": {
        "id": "B3",
        "category": "权利义务",
        "title": "培训与服务期",
        "level": "中风险",
        "check": "服务期约定是否有专项培训支持；违约金是否超过培训费用；培训费用分摊方式是否合理",
        "suggestion_template": "服务期须有专项培训费用支持；违约金不得超过培训费用总额且按服务期等比例递减；培训费用应有凭证"
    },
    "B4": {
        "id": "B4",
        "category": "权利义务",
        "title": "知识产权归属",
        "level": "中风险",
        "check": "职务发明创造的归属是否明确；员工入职前已有知识产权是否排除；离职后一定期限内的发明归属",
        "suggestion_template": "明确职务发明创造归用人单位所有；员工入职前已有知识产权应列明排除；离职后1年内的相关发明应有合理归属约定"
    },
    "B5": {
        "id": "B5",
        "category": "权利义务",
        "title": "规章制度与纪律",
        "level": "低风险",
        "check": "规章制度是否经民主程序制定并公示；违纪处罚标准是否明确；员工是否签收确认",
        "suggestion_template": "规章制度应经职工代表大会或全体职工讨论并公示；违纪处罚标准应具体明确；员工应签收确认"
    },

    # C. 合同解除与争议
    "C1": {
        "id": "C1",
        "category": "解除与争议",
        "title": "劳动合同解除",
        "level": "高风险",
        "check": "解除条件是否符合劳动法规定；经济补偿金计算方式是否合法；是否存在违法解除的风险条款",
        "suggestion_template": "解除条件应严格依据《劳动合同法》第39-41条；经济补偿金按工作年限每满一年支付一个月工资；避免违法解除条款"
    },
    "C2": {
        "id": "C2",
        "category": "解除与争议",
        "title": "争议解决",
        "level": "中风险",
        "check": "劳动争议处理程序是否合法（仲裁前置）；管辖地是否明确；是否约定排除劳动者权利",
        "suggestion_template": "劳动争议应先经劳动仲裁；管辖地为劳动合同履行地或用人单位所在地；不得约定排除劳动者法定权利"
    },
    "C3": {
        "id": "C3",
        "category": "解除与争议",
        "title": "违约责任",
        "level": "中风险",
        "check": "违约金约定是否合法（仅限服务期和竞业限制）；是否存在违法约定的违约金条款；赔偿范围是否合理",
        "suggestion_template": "劳动合同仅可就服务期和竞业限制约定违约金；不得约定其他形式的违约金；赔偿范围应限于直接经济损失"
    },
}

EMPLOYMENT_RULE_IDS_BY_CATEGORY = {
    "基本要素": ["A1", "A2", "A3", "A4", "A5"],
    "权利义务": ["B1", "B2", "B3", "B4", "B5"],
    "解除与争议": ["C1", "C2", "C3"],
}


def get_employment_rule(rule_id: str) -> dict:
    """Look up a single employment contract rule definition."""
    return EMPLOYMENT_RULES.get(rule_id, {})


def get_all_employment_rules() -> list:
    """Return all employment contract rules sorted by category."""
    result = []
    for category in ["基本要素", "权利义务", "解除与争议"]:
        for rule_id in EMPLOYMENT_RULE_IDS_BY_CATEGORY[category]:
            result.append(EMPLOYMENT_RULES[rule_id])
    return result
