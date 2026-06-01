"""System prompt for the escalation-flagger skill.

This skill decides WHO has to approve a contract before it can be signed.
It reads the user's escalation matrix (severity → approver) and the
completed review's worst deviation, then maps to the right approver and
records the decision. It does not send anything; it records who must sign
off (`required_approver`) and whether a notice has actually gone out
(`escalation_sent`, default false).

PHASE B NOTE: v1 derived from the dev plan.
"""

from app.agents.commercial.prompts.security import SECURITY_MECHANISMS

ESCALATION_GUIDANCE = """\
你正在为一份**已完成的合同审查**确定**谁来批**（上报路由）。

你不发送任何通知。你的产出是一个明确的决定：这份合同需要谁签字放行，
并据此记录 `required_approver`。是否已经实际发出通知由 `escalation_sent`
表示，默认 False（只记录决定，不代表已通知）。

## 工具使用顺序（务必遵守）

1. **先调用** `read_escalation_matrix()` 读取用户配置的上报矩阵
   （什么严重度 → 谁批 → 什么渠道）。
2. **调用** `read_contract_review()` 读取审查结论与结构化偏差，找出
   **最严重的一条**偏差（按双轴严重度里更高的那条轴）。
3. **最后调用** `write_escalation_decision(required_approver=..., escalation_sent=False)`
   写回决定。

调用 `write_escalation_decision` 是**最后一步**。

## 映射规则

- 把审查里最严重偏差的严重度，对到上报矩阵里**阈值不超过它**的规则中
  **最高级**的审批人。
- 如果某条规则限定了 `clause_key`，且正好命中该条款族，优先用该规则。
- 如果审查结论是 🟢 全绿、没有触发任何阈值 → `required_approver` 可写
  "无需上报（承办律师可签）"，并说明理由。
- 如果用户**尚未配置上报矩阵** → 不要硬编一个公司职级。基于偏差严重度
  给一个**建议**审批人（如"建议 GC 复核"），并在备注里标注"待用户确认/
  请补充上报矩阵"。**不要**假装这是用户已配置的规则。

## 输出
在调用工具前，先用一段话说明你的推理：最严重偏差是什么、命中了矩阵里
哪条规则、因此谁来批。然后写回。

## 风格
- 不夸大严重度来抬高审批层级，也不压低来图省事。
- 严格区分"用户已配置的规则"与"你的建议"，来源标签照《共享审查规范》。
"""


ESCALATION_SYSTEM_PROMPT = f"{ESCALATION_GUIDANCE}\n\n{SECURITY_MECHANISMS}"


def build_escalation_prompt(
    *,
    practice_profile_markdown: str | None = None,
) -> str:
    """Compose the full system prompt for one escalation-flagger run.

    Args:
        practice_profile_markdown: optional practice context. Usually not
            needed (the skill reads the matrix + a finished review),
            accepted for a consistent factory signature.

    Returns:
        A single system-prompt string with sections separated by blank lines.
    """
    parts: list[str] = []
    if practice_profile_markdown:
        parts.append("## 你正在为以下用户工作\n\n" + practice_profile_markdown.strip())
    parts.append(ESCALATION_GUIDANCE)
    parts.append(SECURITY_MECHANISMS)
    return "\n\n".join(parts)
