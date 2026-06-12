"""Demand tools — read/write litigation demand letters."""

from pydantic_ai import RunContext

from app.agents.litigation.deps import LitigationDeps
from app.repositories import litigation_demand_repo


def read_demand(ctx: RunContext[LitigationDeps]) -> str:
    """读取律师函详情（intake_snapshot / 草稿 / 门禁检查 / 分流结果）。

    需要 ctx.deps.demand_id 已设置。

    Returns:
        JSON 格式的律师函详情。
    """
    demand_id = ctx.deps.demand_id
    if not demand_id:
        return "## 未指定律师函\n\n请提供 demand_id。"

    demand = litigation_demand_repo.get_by_id(ctx.deps.db, demand_id)
    if demand is None:
        return f"## 律师函不存在\n\ndemand_id `{demand_id}` 未找到。"
    if demand.user_id != ctx.deps.user_id:
        return f"## 无权访问\n\ndemand_id `{demand_id}` 不属于当前用户。"

    return f"""## 律师函详情

- **函件类型：** {demand.demand_type}
- **模式：** {demand.mode}（{"发送" if demand.mode == "send" else "接收"}）
- **对方当事人：** {demand.counterparty or "—"}
- **状态：** {demand.status}
- **回复截止：** {demand.response_deadline.isoformat() if demand.response_deadline else "—"}

### 委托登记快照
```json
{demand.intake_snapshot or "{}"}
```

### 涉案主张
```json
{demand.right_or_claim or "{}"}
```

### 当前草稿
{demand.letter_draft or "（尚无草稿）"}

### 发送前门禁检查
```json
{demand.pretransmit_checklist or "{}"}
```

### 分流结论
- **推荐行动：** {demand.recommended_action or "—"}
- **分流结果：** {demand.triage_result or "—"}
- **是否升级：** {"是" if demand.escalation_flag else "否"}
- **升级原因：** {demand.escalation_reason or "—"}
"""


def save_demand_letter(
    ctx: RunContext[LitigationDeps],
    letter_draft: str,
    outbound_letter: str,
    pretransmit_checklist: str | None = None,
    triage_result: str | None = None,
    recommended_action: str | None = None,
) -> str:
    """保存律师函草稿（内部版 + 对外版）和发送门禁/分流结果。

    Args:
        letter_draft: 内部版律师函草稿（含工作成果抬头），Markdown 格式。
        outbound_letter: 对外版律师函（已去抬头），Markdown 格式。
        pretransmit_checklist: 7 项 LOUD GATE 检查结果 (JSON 字符串)。
        triage_result: 来函分流四选项树结论 (JSON 字符串)。
        recommended_action: 推荐行动（A/B/C/D）。

    Returns:
        确认信息。
    """
    demand_id = ctx.deps.demand_id
    if not demand_id:
        return "## 错误：未指定 demand_id，无法保存。"

    fields: dict = {
        "letter_draft": letter_draft,
        "outbound_letter": outbound_letter,
    }
    if pretransmit_checklist is not None:
        fields["pretransmit_checklist"] = pretransmit_checklist
    if triage_result is not None:
        fields["triage_result"] = triage_result
    if recommended_action is not None:
        fields["recommended_action"] = recommended_action

    litigation_demand_repo.update(
        ctx.deps.db,
        demand=litigation_demand_repo.get_by_id(ctx.deps.db, demand_id),
        **fields,
    )
    return "律师函草稿已保存。"
