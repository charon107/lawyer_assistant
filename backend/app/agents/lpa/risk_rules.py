"""LPA contract review rule definitions — 18 rules across 3 categories."""

LPA_RULES = {
    # A. 基金基本要素提取
    "A1": {
        "id": "A1",
        "category": "基本要素",
        "title": "基金名称、类型、注册地",
        "level": "中风险",
        "check": "注册地是否涉及跨境合规冲突；名称是否含误导性表述",
        "suggestion_template": "确认基金名称与备案名称一致；如涉及跨境（如开曼注册+中国运营），需增加跨境合规说明",
    },
    "A2": {
        "id": "A2",
        "category": "基本要素",
        "title": "存续期（投资期+退出期+延长期）",
        "level": "中风险",
        "check": "延长期是否 GP 单方决定（缺少 LP 同意门槛）；延长期是否影响 LP 退出选择权",
        "suggestion_template": "延长期决策应经 LP 或 LPAC 同意（建议 ≥50% 出资比例）；明确延长期内 LP 是否可单独退出",
    },
    "A3": {
        "id": "A3",
        "category": "基本要素",
        "title": "GP/管理人名称及角色",
        "level": "中风险",
        "check": "GP 与管理人权责是否清晰划分；管理人是否为第三方（独立管理人）",
        "suggestion_template": "明确区分 GP（执行事务）与管理人（投资管理）的职责；第三方管理人应单独签署管理协议",
    },
    "A4": {
        "id": "A4",
        "category": "基本要素",
        "title": "基金规模（总承诺出资额）",
        "level": "低风险",
        "check": "首次/最终交割期限是否过长；是否有 LP 不同轮次出资的不平等安排",
        "suggestion_template": "首次交割与最终交割间隔不宜超过 12 个月；不同轮次 LP 应享有同等权利",
    },
    "A5": {
        "id": "A5",
        "category": "基本要素",
        "title": "LP 最低出资额",
        "level": "低风险",
        "check": "不同 LP 类别是否存在歧视性条件；优先权 LP 与普通 LP 差异",
        "suggestion_template": "LP 类别之间的差异应在 PPM 中充分披露；确保不违反公平对待义务",
    },
    # B. 费用结构审查
    "B1": {
        "id": "B1",
        "category": "费用结构",
        "title": "管理费率",
        "level": "高风险",
        "check": "是否超过 2%（行业上限）；与市场平均水平对比是否显著偏高",
        "suggestion_template": "建议管理费率不超过 2%；如因特殊策略需要更高费率，应在 PPM 中充分披露理由",
    },
    "B2": {
        "id": "B2",
        "category": "费用结构",
        "title": "管理费计算基数",
        "level": "高风险",
        "check": "committed capital / called capital / net invested capital 定义是否清晰；GP 是否有权单方选择最有利基数",
        "suggestion_template": "明确管理费基数定义；建议投资期按 committed capital、退出期按 net invested capital；GP 不应有权单方切换基数",
    },
    "B3": {
        "id": "B3",
        "category": "费用结构",
        "title": "管理费减免（step-down）",
        "level": "中风险",
        "check": "投资期结束后费率是否自动下调；是否有触发机制（如第一个退出后）",
        "suggestion_template": "建议投资期结束后管理费自动减半或按 net invested capital 计算；明确 step-down 的触发时间点",
    },
    "B4": {
        "id": "B4",
        "category": "费用结构",
        "title": "费用分担",
        "level": "中风险",
        "check": "GP 承担 vs 基金承担的费用分类是否明确；是否存在 GP 向基金转嫁运营成本的模糊条款；费用种类是否详细列明",
        "suggestion_template": "明确列举 GP 承担的费用（组织费、办公费、人员薪酬等）和基金承担的费用（托管费、审计费、法律费等）",
    },
    "B5": {
        "id": "B5",
        "category": "费用结构",
        "title": "关联方费用",
        "level": "中风险",
        "check": "GP 关联方向基金收取的服务费是否豁免管理费；关联方收费是否透明并经独立审核（LPAC 审批）",
        "suggestion_template": "关联方服务费应在管理费之外单独披露并经 LPAC 审批；或采用管理费全额覆盖模式（不另收关联方费用）",
    },
    # C. 分配/瀑布
    "C1": {
        "id": "C1",
        "category": "分配/瀑布",
        "title": "分配瀑布结构",
        "level": "高风险",
        "check": "是 European waterfall 还是 American waterfall；LP 是否优先回收全部出资+优先回报后再分配 carry",
        "suggestion_template": "建议采用 European waterfall，LP 优先回收全部出资+优先回报后再分配 carry；避免 American waterfall 下 GP 过早获得分配",
    },
    "C2": {
        "id": "C2",
        "category": "分配/瀑布",
        "title": "优先回报率 (Preferred Return / Hurdle)",
        "level": "高风险",
        "check": "hurdle rate 是否 ≥ 8%（行业标准）；是单利还是复利；计算基准是否明确",
        "suggestion_template": "建议 hurdle rate 不低于 8%，按复利计算；明确以实际出资日为起算基准",
    },
    "C3": {
        "id": "C3",
        "category": "分配/瀑布",
        "title": "Carry 计算与分配",
        "level": "高风险",
        "check": "carry 比例是否超过 20%；是否有 catch-up 条款及其速度；carry 是否与业绩挂钩",
        "suggestion_template": "carry 比例建议不超过 20%；catch-up 速度不应超过 100%；建议设置 clawback 机制",
    },
    "C4": {
        "id": "C4",
        "category": "分配/瀑布",
        "title": "Clawback 条款",
        "level": "高风险",
        "check": "是否有 clawback 机制；clawback 触发条件是否明确；GP 是否提供担保",
        "suggestion_template": "建议设置 clawback 条款，GP 应就超额分配提供银行保函或 escrow 担保；明确 clawback 计算方式和期限",
    },
    "C5": {
        "id": "C5",
        "category": "分配/瀑布",
        "title": "GP 共同投资",
        "level": "中风险",
        "check": "GP 是否有共同投资义务（skin in the game）；共同投资比例是否合理；共同投资是否享有优先权",
        "suggestion_template": "建议 GP 出资不低于基金总规模的 1-2%；共同投资不应享有优于 LP 的条款",
    },
    # D. GP/LP 权利义务
    "D1": {
        "id": "D1",
        "category": "GP/LP权利义务",
        "title": "Key man 条款",
        "level": "高风险",
        "check": "是否有 key man 事件明确定义；触发后投资期是否自动暂停；是否有替代 key man 的提名程序",
        "suggestion_template": "明确 key man 事件（如主要人员离职/无法履职 ≥90 日）；触发后自动暂停投资期；替代人选需 LPAC 批准",
    },
    "D2": {
        "id": "D2",
        "category": "GP/LP权利义务",
        "title": "GP 除名机制",
        "level": "高风险",
        "check": "for cause 除名门槛是否清晰；no-fault removal 投票比例（<75% 有利 GP，≥75% 有利 LP）；除名后管理费处理",
        "suggestion_template": "for cause 门槛应明确列举（欺诈、重大过失、违反信义义务等）；no-fault removal 建议 ≥75% LP 出资比例；除名后管理费按 net invested capital 计算直至清算",
    },
    "D3": {
        "id": "D3",
        "category": "GP/LP权利义务",
        "title": "关联交易",
        "level": "中风险",
        "check": "审批是否仅需 GP 同意（缺少 LPAC 或独立委员会审议）；利益冲突披露义务是否充分",
        "suggestion_template": "关联交易需经 LPAC 或独立第三方审议；GP 应在交易前充分披露利益冲突",
    },
    "D4": {
        "id": "D4",
        "category": "GP/LP权利义务",
        "title": "投资限制",
        "level": "中风险",
        "check": "单一项目/行业集中度上限是否合理；是否允许后续基金共同投资（需豁免 GP 利益冲突）；风险控制措施是否充足",
        "suggestion_template": "单一项目不超过基金总规模的 20-25%；后续基金共同投资需 LPAC 豁免；设定杠杆上限",
    },
    "D5": {
        "id": "D5",
        "category": "GP/LP权利义务",
        "title": "LP 转让/退伙",
        "level": "中风险",
        "check": "转让限制是否过于严苛；是否存在 LP 违约强制转让条款（惩罚性转让折扣）；退伙后未出资承诺的清算处理",
        "suggestion_template": "GP 不应不合理拒绝 LP 转让；取消或限制惩罚性转让折扣；退伙 LP 的未出资承诺应予豁免",
    },
    "D6": {
        "id": "D6",
        "category": "GP/LP权利义务",
        "title": "报告义务",
        "level": "低风险",
        "check": "季度/年度报告内容是否明确；LP 是否可查阅底层资产详情；报告延迟是否有罚则",
        "suggestion_template": "明确季度和年度报告的最低内容要求；LP 有权在合理通知后查阅底层资产信息和账册",
    },
    "D7": {
        "id": "D7",
        "category": "GP/LP权利义务",
        "title": "风险管理框架",
        "level": "中风险",
        "check": "是否建立风险评估和监控机制",
        "suggestion_template": "建议增加风险管理条款，建立定期风险评估、风险限额和风险报告机制；明确风险事件的应对程序",
    },
    "D8": {
        "id": "D8",
        "category": "GP/LP权利义务",
        "title": "GP/LP 退出机制",
        "level": "中风险",
        "check": "双方退出路径是否对等；GP 退出后管理费/收益分成处理",
        "suggestion_template": "确保 GP 和 LP 退出路径基本对等；GP 退出后已产生但未分配的 carry 应合理处理；清算期间管理费计算方式应明确",
    },
    # E. 投资条款
    "E1": {
        "id": "E1",
        "category": "投资条款",
        "title": "投资集中度限制",
        "level": "中风险",
        "check": "单一项目/行业/地区集中度上限是否合理；是否有分散投资的硬性约束",
        "suggestion_template": "单一项目不超过基金总规模的 20-25%；单一行业不超过 30%；建议设置地域分散要求",
    },
    "E2": {
        "id": "E2",
        "category": "投资条款",
        "title": "共同投资权",
        "level": "中风险",
        "check": "GP 是否有义务向 LP 提供共同投资机会；共同投资的费用分担是否公平",
        "suggestion_template": "共同投资机会应平等提供给所有 LP；共同投资不应另行收取管理费或 carry",
    },
    "E3": {
        "id": "E3",
        "category": "投资条款",
        "title": "跟投权与后续基金限制",
        "level": "中风险",
        "check": "GP 对已投项目的跟投权是否受限；后续基金是否受投资限制约束以避免利益冲突",
        "suggestion_template": "后续基金投资同一家公司应经 LPAC 审批；GP 的跟投权不应优先于 LP 的跟投机会",
    },
    "E4": {
        "id": "E4",
        "category": "投资条款",
        "title": "杠杆与担保限制",
        "level": "中风险",
        "check": "基金层面是否设置杠杆上限；GP 是否有权以基金资产提供担保",
        "suggestion_template": "基金层面杠杆不应超过承诺出资的 50%；以基金资产提供担保需经 LPAC 批准",
    },
    # F. 清算/解散/争议
    "F1": {
        "id": "F1",
        "category": "清算/解散/争议",
        "title": "清算优先级",
        "level": "高风险",
        "check": "清算时 LP 是否优先回收出资；清算分配顺序是否明确",
        "suggestion_template": "清算分配应按以下顺序：(1) LP 出资回收 (2) 优先回报 (3) GP catch-up (4) carry 分配；建议在 LPA 中明确列明",
    },
    "F2": {
        "id": "F2",
        "category": "清算/解散/争议",
        "title": "解散触发条件",
        "level": "中风险",
        "check": "解散触发条件是否明确；GP 违约/除名后基金是否自动进入清算",
        "suggestion_template": "明确解散触发条件：(1) GP 除名 (2) LP 超级多数投票 (3) 基金目的无法实现 (4) 法律要求",
    },
    "F3": {
        "id": "F3",
        "category": "清算/解散/争议",
        "title": "争议解决机制",
        "level": "中风险",
        "check": "争议解决方式（仲裁/诉讼）是否明确；仲裁机构和适用法律是否指定；LP 是否有集体诉讼权",
        "suggestion_template": "建议约定仲裁作为争议解决方式（如 HKIAC 或 SIAC）；明确适用法律和仲裁地",
    },
    "F4": {
        "id": "F4",
        "category": "清算/解散/争议",
        "title": "清算期限与管理费",
        "level": "中风险",
        "check": "清算期是否设置上限；清算期间管理费是否减免",
        "suggestion_template": "清算期建议不超过 2-3 年；清算期间管理费应减半或按实际管理资产计算",
    },
}

LPA_RULE_IDS_BY_CATEGORY = {
    "基本要素": ["A1", "A2", "A3", "A4", "A5"],
    "费用结构": ["B1", "B2", "B3", "B4", "B5"],
    "分配/瀑布": ["C1", "C2", "C3", "C4", "C5"],
    "GP/LP权利义务": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"],
    "投资条款": ["E1", "E2", "E3", "E4"],
    "清算/解散/争议": ["F1", "F2", "F3", "F4"],
}


def get_lpa_rule(rule_id: str) -> dict:
    """Look up a single LPA rule definition."""
    return LPA_RULES.get(rule_id, {})


def get_all_lpa_rules() -> list:
    """Return all LPA rules sorted by category."""
    result = []
    for category in [
        "基本要素",
        "费用结构",
        "分配/瀑布",
        "GP/LP权利义务",
        "投资条款",
        "清算/解散/争议",
    ]:
        for rule_id in LPA_RULE_IDS_BY_CATEGORY[category]:
            result.append(LPA_RULES[rule_id])
    return result


def get_lpa_rule_ids_by_category() -> dict:
    return LPA_RULE_IDS_BY_CATEGORY
