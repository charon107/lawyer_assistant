"""Lease agreement review rule definitions — 12 rules across 3 categories."""

LEASE_RULES = {
    # A. 基本要素审查
    "A1": {
        "id": "A1",
        "category": "基本要素",
        "title": "租赁物信息",
        "level": "高风险",
        "check": "租赁物名称、位置、面积、用途是否明确；产权证号或权属证明是否载明；租赁物现状描述是否完整",
        "suggestion_template": "明确租赁物地址、面积、用途及现状；载明产权证号或权属证明文件编号",
    },
    "A2": {
        "id": "A2",
        "category": "基本要素",
        "title": "租赁期限",
        "level": "中风险",
        "check": "租赁起止日期是否明确；租期是否超过20年（超过部分无效）；续租条件是否约定",
        "suggestion_template": "明确租赁起止日期；租期不超过20年；约定续租优先权及续租条件",
    },
    "A3": {
        "id": "A3",
        "category": "基本要素",
        "title": "租金与支付",
        "level": "高风险",
        "check": "租金金额、支付周期、支付方式是否明确；租金调整机制是否合理；押金金额及退还条件是否约定",
        "suggestion_template": "明确租金金额、币种、支付日期和方式；租金调整应提前通知并约定上限；押金退还条件应具体明确",
    },
    "A4": {
        "id": "A4",
        "category": "基本要素",
        "title": "双方身份信息",
        "level": "中风险",
        "check": "出租方是否为产权人或合法代理人；承租方身份信息是否完整；共有产权是否所有共有人签字",
        "suggestion_template": "确认出租方产权人身份或代理权限；承租方应提供有效身份证明；共有产权需全部共有人签字",
    },
    # B. 权利义务与风险
    "B1": {
        "id": "B1",
        "category": "权利义务",
        "title": "维修与保养责任",
        "level": "中风险",
        "check": "租赁物维修责任划分是否明确；大修与日常维护的责任归属；维修费用承担方式",
        "suggestion_template": "明确出租方负责结构性维修、承租方负责日常维护；约定维修响应时限和费用承担方式",
    },
    "B2": {
        "id": "B2",
        "category": "权利义务",
        "title": "转租与分租",
        "level": "高风险",
        "check": "是否允许转租或分租；转租是否需出租方书面同意；转租期限是否不超过剩余租期",
        "suggestion_template": "明确转租须经出租方书面同意；转租期限不超过原合同剩余租期；承租方对转租方行为承担连带责任",
    },
    "B3": {
        "id": "B3",
        "category": "权利义务",
        "title": "装修与改造",
        "level": "中风险",
        "check": "装修或改造是否需出租方同意；装修费用承担和残值处理；恢复原状的义务和费用",
        "suggestion_template": "装修或结构改造须经出租方书面同意；约定装修残值归属和补偿方式；明确退租时恢复原状的义务",
    },
    "B4": {
        "id": "B4",
        "category": "权利义务",
        "title": "违约责任",
        "level": "高风险",
        "check": "逾期支付租金的违约金是否合理；提前退租的违约责任；出租方提前收回的赔偿责任",
        "suggestion_template": "逾期违约金不超过日万分之五；提前退租应约定合理通知期和违约金；出租方提前收回应赔偿承租方损失",
    },
    # C. 法律合规与终止
    "C1": {
        "id": "C1",
        "category": "法律合规",
        "title": "合同登记备案",
        "level": "低风险",
        "check": "是否约定租赁合同登记备案义务；备案费用承担；未备案的法律风险提示",
        "suggestion_template": "约定双方配合办理租赁登记备案；明确备案费用承担方；提示未备案不得对抗善意第三人",
    },
    "C2": {
        "id": "C2",
        "category": "法律合规",
        "title": "合同终止与交接",
        "level": "中风险",
        "check": "合同终止条件是否列举完整；租赁物交接程序是否明确；押金退还条件和时限",
        "suggestion_template": "明确合同终止情形和通知义务；约定交接验收程序和时限；押金应在验收合格后15日内退还",
    },
    "C3": {
        "id": "C3",
        "category": "法律合规",
        "title": "争议解决",
        "level": "低风险",
        "check": "争议解决方式（仲裁/诉讼）是否明确；管辖法院或仲裁机构是否约定",
        "suggestion_template": "明确约定仲裁或诉讼作为争议解决方式；选择仲裁应指定具体仲裁机构",
    },
}

LEASE_RULE_IDS_BY_CATEGORY = {
    "基本要素": ["A1", "A2", "A3", "A4"],
    "权利义务": ["B1", "B2", "B3", "B4"],
    "法律合规": ["C1", "C2", "C3"],
}


def get_lease_rule(rule_id: str) -> dict:
    """Look up a single lease rule definition."""
    return LEASE_RULES.get(rule_id, {})


def get_all_lease_rules() -> list:
    """Return all lease rules sorted by category."""
    result = []
    for category in ["基本要素", "权利义务", "法律合规"]:
        for rule_id in LEASE_RULE_IDS_BY_CATEGORY[category]:
            result.append(LEASE_RULES[rule_id])
    return result
