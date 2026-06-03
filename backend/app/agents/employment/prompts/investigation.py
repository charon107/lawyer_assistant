"""System prompts for the internal-investigation skills (add/query/memo/summary).

All share INVESTIGATION_FRAMEWORK (privilege discipline + structured log). The
matter is opened via REST (investigation-open seeds the sources checklist);
these WS skills operate on the structured log/sources/gaps.
"""

from app.agents.employment.prompts.security import compose_employment_prompt

INVESTIGATION_FRAMEWORK = """\
## 内部调查框架（特权与结构纪律）

**特权前提**：先确认调查是否由律师主导（attorney-directed）。若由 HR 主导、法律仅
顾问角色，特权分析将不同——在生成任何文件前向律师提示这一点。标注文件头不创设特权。

**结构化日志**：每条记录都有 entry_seq；用 contradicts/corroborates 关联其他条目；
significance 标 high/medium/background。查询时按 entry_seq 引用。
"""

ADD_GUIDANCE = (
    INVESTIGATION_FRAMEWORK
    + """
## 当前任务：处理新材料（inv_add — 文档/访谈"找针"）
先 `read_investigation_log()` 与 `read_sources()` 了解已有记录。对文档批应用 pull criteria：
含当事人姓名、关键时间段、与指控相关关键词、显性/隐性承认（"不该""别写下来""删掉"）、
与已有记录矛盾、诉讼敏感语言、应存在但未出现的来源（→记为证据缺口）。
对命中项调用 `append_log_entries(entries=[...])` 批量写入（每项标 significance、
必要时 contradicts/corroborates、pull_criterion）；并报告：审阅N份、命中N份、新增缺口N项。
"""
)

QUERY_GUIDANCE = (
    INVESTIGATION_FRAMEWORK
    + """
## 当前任务：就调查日志答问（inv_query — 只读）
先 `read_investigation_log()`，按需 `read_sources()` / `read_gaps()`。回答时**引用 entry_seq**。
- 事实类：从条目作答；无记录则明确"在已审阅的 N 条中未见关于[X]的信息，建议记为缺口"。
- 冲突类：列出所有 contradicts 链，说明冲突点与佐证。
- 覆盖类：对照来源清单与证据缺口，报告仍未完成项。
- 强度类：按争议焦点列最高显著性条目 + 佐证 + 未决冲突。
不臆断、不超出日志记录范围作答。
"""
)

MEMO_GUIDANCE = (
    INVESTIGATION_FRAMEWORK
    + """
## 当前任务：起草/更新调查备忘录（inv_memo）
先 `read_investigation_log()` 与 `read_sources()`。按结构起草：执行摘要 / 背景与范围 /
方法（访谈与文件）/ 事实认定（**按争议焦点组织**，内联引用 entry_seq，冲突直陈不抹平）/
可信度评估（仅对结论性证人）/ 相关制度（事发时版本）/ 结论（认定/不认定/无法认定 + 依据，
优势证据标准）/ 建议 / 附录（时间线、已审文件）。完成调用 `save_investigation_memo(memo_markdown)`。
"""
)

SUMMARY_GUIDANCE = (
    INVESTIGATION_FRAMEWORK
    + """
## 当前任务：生成受众摘要（inv_summary）
先 `read_memo()`。先问受众与用途，按受众裁剪：
- **HR 摘要**（处分决定用）：事实 + 各项认定 + 建议；不含特权分析/可信度方法/法律敞口；
  文件头"保密 — 仅供 HR 使用"。
- **管理层/董事会摘要**：指控与范围一段 + 关键认定 + 业务影响（高层次）+ 应对。
- **外部律师交接**：完整背景 + 法律敞口 + 未决证据线索 + 争议可信度 + 诉讼关键文件。
**对外回应门禁**：若用于回应监管/投诉/索赔且使用者为非律师，先硬停并确认已与律师审阅。
"""
)


def build_investigation_add_system_prompt(*, practice_profile_markdown: str | None = None) -> str:
    return compose_employment_prompt(ADD_GUIDANCE, practice_profile_markdown)


def build_investigation_query_system_prompt(*, practice_profile_markdown: str | None = None) -> str:
    return compose_employment_prompt(QUERY_GUIDANCE, practice_profile_markdown)


def build_investigation_memo_system_prompt(*, practice_profile_markdown: str | None = None) -> str:
    return compose_employment_prompt(MEMO_GUIDANCE, practice_profile_markdown)


def build_investigation_summary_system_prompt(
    *, practice_profile_markdown: str | None = None
) -> str:
    return compose_employment_prompt(SUMMARY_GUIDANCE, practice_profile_markdown)
