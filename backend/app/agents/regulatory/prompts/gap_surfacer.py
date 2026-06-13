"""gap-surfacer shared rules (reference, NOT a standalone skill).

源插件中 ``user-invocable: false``. 其规则内化到 regulatory_gaps / regulatory_comments
模型 + gap/comment 服务 + policy-diff 提示词。此处导出规则文本供 policy-diff 引用，
并供 gaps 服务渲染状态报告时的格式规范参考。
"""

GAP_TRACKER_RULES = """\
### 差距追踪器规则（gap-surfacer，内化）
- **gap_type 6 值**：
  - `none`（仅审计，无义务）/ `partial`（到期前30天提醒）/ `full`（30天）/ `new-policy`（30天）
  - `watch`（前瞻性，无合规义务，`due` 是重访日期不是合规截止）
  - `comment-decision`（意见征集决策待定，`due` 是征集截止，截止前21天提醒）
- **观察事项分离**：`watch` + `comment-decision` 进「👀 观察事项（前瞻性——预法规）」分区，
  **不混入合规差距**。
- **去重（A3）**：去重键 = 法条引用 + policy_affected；引用缺失才回退归一化 requirement 文本。
  相同键 = 同一差距，不重复创建。
- **严重性底线**：交接差距时携带上游 policy-diff 的 severity，下游不得无声降级。
- **未验证不进逾期**：`status_verified=false` 的差距即便过期也只进 🟡"需审查"，不进 🔴 逾期。
- **逐次发送确认**：负责人通知逐条确认（本期=站内通知，不外发）；7 天内不重复提醒同一差距。
- **风险接受不删除**：status→risk-accepted，保留但移出开放报告。
"""

COMMENT_TRACKER_RULES = """\
### 意见征集追踪器规则（comment-tracker，内化）
- **decision 5 态**：`undecided` / `filing` / `not-filing` / `filed` / `waived`。
- **提醒节奏**（服务/cron 算术，非 LLM）：截止前 14 天（仍 undecided）、前 3 天（升级紧急度）。
- 决策"提交（filing）"时提示设内部审阅截止（征集截止前 ≥5 工作日）。
"""
