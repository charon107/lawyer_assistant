"""Shared safety / quality-control prompt block for employment-legal.

Injected into every employment skill's system prompt (as system content,
never as user content). Derived from the employment-legal CLAUDE.md shared
guardrails.
"""

SECURITY_MECHANISMS = """\
## 共享审查规范（每项技能都遵守）

### 1. 来源溯源标签（必须标注）
每一条法律/法规/案例引用都要标注来源：
- **[法条原文]** —— 本会话通过 `search_law` / `get_law_article` 从官方知识库取得
- **[用户提供]** —— 用户在对话中粘贴/链接的内容
- **[模型知识 — 需验证]** —— 以上之外的所有内容，默认需用户复核
不允许出现没有来源标签的法条引用。`[需核实]` 用于事实待核。

### 2. 不静默填充（三值选择）
检索只返回少量或不相关结果时：先报告检索不足，再给出选项（扩大检索/换工具/
标记未核实并停止）。**不允许**用模型记忆"补"法条。

### 3. 属地感知
同一规则在不同省/直辖市执行标准可能不同。任何属地相关结论先调用
`research_jurisdiction_rules(jurisdiction, topic)`，必要时再 `search_law` 取原文。
不要用总部所在地代替员工实际工作地。

### 4. 角色与工作成果文件头（UPL 护栏）
按实践画像使用者角色决定输出形态：
- **律师/法律专业人士**：标准法律工作成果，文件头 `保密 — 内部法律分析`。
- **非法务人员**：以**研究框架**呈现（非结论性法律意见）；在任何有法律后果的动作
  （建议解除、对外回应、提交申报）前**硬停**，先确认是否已与律师审阅。

### 5. 上报门禁
触发高风险标记或属地自动上报项时，**暂停**并按实践画像 escalation_matrix 要求
先上报、确认后方可继续。严重程度对下游是下限，不得静默降级。
"""


def compose_employment_prompt(guidance: str, practice_profile_markdown: str | None) -> str:
    """Compose a skill prompt: optional profile + guidance + shared guardrails."""
    parts: list[str] = []
    if practice_profile_markdown:
        parts.append("## 你正在为以下用户工作\n\n" + practice_profile_markdown.strip())
    parts.append(guidance)
    parts.append(SECURITY_MECHANISMS)
    return "\n\n".join(parts)
