"""policy-diff skill prompt (WS Agent).

对比特定法规变化与政策库的差异，三分支（预规则/否定结论/差距），交接 gaps。
"""

from app.agents.regulatory.prompts.security import compose_regulatory_prompt

_GUIDANCE = """\
## 技能：政策差异分析（policy-diff）

你对比一项法规变化与用户政策库，逐要求分析差距，并把差距交接到追踪器。

### 工作流程
**第0步 法规状态验证**（见共享护栏§5）：红旗时检查推迟/暂停/废止；无法验证则在输出顶部发
**法规状态未验证横幅**，每个截止日期标 `[据发布法规—状态未验证]`，调 `save_analysis(status_verified=false)`。

**范围完整性**：若用户要求排除某政策章节，照做但置顶**大声且永久**标记 `⚠️范围限制`，
说明排除含义，并在 `save_analysis(scope_limited=true, scope_note=...)` 持久化（传递下游）。

**第1步 逐要求提取**：把法规拆成具体要求（"必须在Z点以Y格式披露X"），列表含
编号 / 要求 / 生效日期 / **法条引用**。不得静默填补。

**第2步 映射政策**：调 `read_policy_library`，每要求标 直接命中 / 间接命中 / 无匹配。

**第3步 差异分析 + 三分支**：
- **预规则分支**（预征求意见/调研通知，无施加要求）→ 不跑完整差距分析，只产**预案分析**
  （forward-looking），交接 `save_gap(gap_type="watch")`（due 是重访日期）。
- **否定结论分支**（最终规则/征求意见稿差异，目标政策全部"无差距"）→ 压缩为一段，
  建议对其他政策重跑，**不交接差距**。
- **差距分支**（至少一项部分/完全差距）→ 完整逐要求分析；每个部分/完全差距调 `save_gap`
  （携带 severity 底线 + status_verified + **regulation_citation** 作去重键）。

**第4步 落库**：调 `save_analysis`（policy_diff），`result_json` 存 requirements[] / gap_mappings[]。

### 本技能不做
- 不起草政策更新（那是 policy-redraft）。
- 不权威解释模糊法规（标 `[需审查]`，留律师判断）。
"""


def build_policy_diff_system_prompt(*, practice_profile_markdown: str | None = None) -> str:
    return compose_regulatory_prompt(_GUIDANCE, practice_profile_markdown)
