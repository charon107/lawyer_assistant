# 隐私数据模块（Privacy-Legal）开发计划

**版本：** 1.0
**日期：** 2026-06-07
**目标：** 将 claude-for-legal-zh 的**隐私数据（个人信息保护）模块**完整融入 LexMind，作为第 4 个法律模块，**严格复用 employment（劳动用工）/ corporate（公司并购）已验证的真实架构模式**。

---

## Context（为什么做这件事）

LexMind 已落地 3 个法律模块（commercial→corporate→employment），均遵循同一套"四层移植 + 传输层三分"的真实架构。本次新增**隐私数据模块**（第 4 个），把 claude-for-legal-zh 的 `privacy-legal` 插件的能力，通过 LexMind 的产品形态（后端 API + Web UI）交付给中国律师与法务人员。

**最关键的事实澄清（务必先读）：**

- 真正的移植源是 **`~/.claude/plugins/marketplaces/claude-for-legal-zh/privacy-legal/`**（中文本地化版，`version: 1.0.2-zh`，作者"陈石 律师"）。
- 它覆盖的是**中国法**：**《个人信息保护法》（个保法）、《数据安全法》、《网络安全法》**及配套规章；**不是** GDPR/CCPA。
  - PIA = 个人信息保护影响评估（**个保法第 55 条**）
  - DSAR = 个人信息主体权利响应（**个保法第 44–50 条**，时限见**第 45 条**）
  - DPA = 个人信息处理协议审查（**双向**：受托处理者 ↔ 个人信息处理者）
- ⚠️ 不要使用英文上游缓存 `~/.claude/plugins/cache/claude-for-legal/privacy-legal/`（那是 GDPR/CCPA 版）。一切以 `claude-for-legal-zh` marketplace 为准。
- 因为是中国法，**可直接复用 LexMind 现有中文法条 RAG**（`search_law` / `get_law_article`），与 employment 一致。

**最终效果**：隐私数据模块的后端 Agent / 提示词 / 工具 / 工作流**完全遵循** `claude-for-legal-zh` 的 ZH `SKILL.md` 定义，LexMind 只提供用户友好的前端 UI 和把"配置文件 CLAUDE.md"换成"数据库画像表"的产品化封装。

---

## 目录

1. [总体目标与范围](#1-总体目标与范围)
2. [模块全景（技能按传输层三分）](#2-模块全景技能按传输层三分)
3. [复用既有架构（镜像 corporate / employment）](#3-复用既有架构镜像-corporate--employment)
4. [数据模型设计](#4-数据模型设计)
5. [后端开发任务](#5-后端开发任务)
6. [前端开发任务](#6-前端开发任务)
7. [技能实现详解](#7-技能实现详解)
8. [定时代理实现](#8-定时代理实现)
9. [法条检索与知识库前置条件](#9-法条检索与知识库前置条件)
10. [开发排期](#10-开发排期)
11. [附录：关键文件清单](#11-附录关键文件清单)

---

## 1. 总体目标与范围

### 1.1 目标

将 `claude-for-legal-zh` 隐私数据模块的 **7 个核心技能 + customize + 冷启动基础设施** 移植到 LexMind：

- 用户访问「隐私数据」模块时，若未配置则引导冷启动访谈
- 配置完成后，用户可通过前端界面使用全部技能
- 后端 Agent / 提示词 / 工具 **完全遵循** ZH `SKILL.md`（中国法实质内容 + 共享护栏 + 双向 DPA 理念）
- **架构上逐项镜像 employment 模块**（最新、最近的同构样板；employment 又镜像 corporate）
- 1 个轻量定时代理（policy-monitor 周度扫描提醒，纯算术，无 LLM）

### 1.2 范围

**包含（用户列出的 7 个核心技能 + 必要基础设施）：**

| 技能 | 中文 | 落地形态 |
|------|------|---------|
| cold-start-interview | 冷启动访谈 | 冷启动**服务状态机** + 前端向导（**非 Agent**） |
| use-case-triage | 处理活动分诊 | WS Agent |
| dpa-review | 个人信息处理协议审查（双向） | WS Agent |
| dsar-response | 个人信息主体权利响应 | REST 建档 + WS Agent 起草两函 |
| pia-generation | 个人信息保护影响评估 | WS Agent |
| reg-gap-analysis | 法规差距分析 | WS Agent |
| policy-monitor | 处理规则漂移监控（扫描 + 直接查询） | WS Agent（2 action）+ cron 提醒 |
| customize | 修改画像某一项 | 前端**设置页** + `PUT /privacy/profile`（非 Agent） |

**明确延后（不在本期）：**

- `matter-workspace`（事项工作区）— **不在用户列出的 7 技能内**；且照 employment 先例，企业法务默认隐藏 matter 概念，本期统一用 **practice-level（实践级）上下文**。后续如需私人执业多客户隔离再引入（届时照 `CorporateDeal` 建 `privacy_matters`）。
- **元典 MCP 检索** — 本期用 LexMind 现有 RAG（`search_law`）替代；ZH 提示词里的 `[元典检索]` 标签改为 `[本地知识库]/[法条原文]`（见 §7.10）。
- **外部 MCP 集成**（Drive / SharePoint / 飞书文档 / 即时通讯）— 本期不接；冷启动「可用集成」一节统一标记为不可用，按 ZH 的降级路径处理（输出存库、通知内嵌）。

### 1.3 与 commercial / corporate / employment 的关系

| 维度 | commercial | corporate | employment | **privacy（本期）** |
|------|-----------|-----------|------------|---------------------|
| 路由前缀 | `/commercial` | `/corporate` | `/employment` | `/privacy` |
| module_configs.module_name | `commercial-legal` | `corporate-legal` | `employment-legal` | `privacy-legal` |
| 独立 profile 表 | `commercial_profiles` | `corporate_profiles` | `employment_profiles` | `privacy_profiles`（新建，**非共享**） |
| Agent 工厂 | `agents/commercial/agent.py` | `agents/corporate/agent.py` | `agents/employment/agent.py` | `agents/privacy/agent.py`（镜像 employment） |
| WS 端点 | `/ws/commercial` | `/ws/corporate` | `/ws/employment` | `/ws/privacy` |
| 定时任务 | renewal_watcher, deal_debrief | dataroom_watcher | leave_tracker | privacy_policy_sweep_reminder |
| 前端页面 | `/commercial/*` | `/corporate/*` | `/employment/*` | `/privacy/*` |

---

## 2. 模块全景（技能按传输层三分）

**核心原则（来自 corporate/employment 真实代码）：** REST 端点**全部是 CRUD（纯 service 调用）**；所有 Agent 驱动的技能**只走 WebSocket**，前端用显式 `action` 字段选择技能，**后端不做 LLM / 关键词意图路由**（见 `employment_ws.py` / `corporate_ws.py`："skill chosen explicitly by the client — no LLM intent routing"）。

### 2.1 技能 → 传输层映射矩阵

| # | 技能 | 传输层 | 入口 | 落库表 |
|---|------|--------|------|--------|
| 1 | cold-start-interview | **REST**（service 状态机）+ 前端向导 | `POST /privacy/setup` | module_configs → privacy_profiles |
| 2 | customize | **REST** | `PUT /privacy/profile` | privacy_profiles |
| 3 | use-case-triage | **WS** `action=triage` | `/ws/privacy` | privacy_reviews（type=triage） |
| 4 | dpa-review | **WS** `action=dpa` | `/ws/privacy` | privacy_reviews（type=dpa） |
| 5 | pia-generation | **WS** `action=pia` | `/ws/privacy` | privacy_reviews（type=pia） |
| 6 | reg-gap-analysis | **WS** `action=gap` | `/ws/privacy` | privacy_reviews（type=gap） |
| 7 | dsar-response | **REST 建档** + **WS** `action=dsar` 起草 | `POST /privacy/dsar` → `/ws/privacy` | privacy_dsar |
| 8 | policy-monitor（扫描） | **WS** `action=policy_sweep` | `/ws/privacy` | privacy_reviews（type=policy_sweep）+ privacy_notifications |
| 9 | policy-monitor（直接查询） | **WS** `action=policy_query` | `/ws/privacy` | （问答，可选存 review） |
| 10 | policy-monitor（周度提醒） | **cron**（纯算术） | scheduler job | privacy_notifications |

WS `action` 合计 **7 个**：`triage / dpa / pia / gap / dsar / policy_sweep / policy_query`。

### 2.2 技能依赖关系

```
cold-start-interview ──写入──> privacy_profiles（practice profile / CLAUDE.md 等价物）

所有 WS Agent 技能 ──读取──> privacy_profiles（前置条件；未配置则 /status 引导冷启动）
所有 WS Agent 技能 ──若未配置 LLM──> 报错 llm_not_configured（绝不兜底）

use-case-triage(WS) ──分类──> 🟢直接推进 / 🟡需PIA / 🟠强制评估(个保法第55条) / 🔴停止(政策冲突)
    └─ 若需 PIA ──提示"是否现在开始PIA"──> pia-generation（同一对话续跑）

dpa-review(WS) ──读 prior triage/PIA(同对方当事人)──> 继承严重性底线 ──双向审查──> 写 review(type=dpa)
pia-generation(WS) ──读 prior triage(同活动)──> 继承严重性底线 ──写──> review(type=pia)
    └─ 若发现处理规则不一致 ──交接──> policy-monitor

reg-gap-analysis(WS) ──新法规 vs 当前画像──> 写 review(type=gap)（差距 + 整改计划）

dsar-response：REST POST 建 privacy_dsar 档（含 PII 最小化）──> WS action=dsar 起草两函（确认函 + 实质函）──> 回写 privacy_dsar

policy-monitor(扫描) ──读 privacy_reviews(自上次扫描)──> diff 处理规则承诺 ──> 必须/建议更新 + 通知
policy_sweep_reminder(cron) ──纯算术：数自 last_policy_sweep 以来的新 review 条数──> 写提醒通知（不调 LLM）
```

### 2.3 双向 DPA 核心理念保真（本模块的灵魂）

`dpa-review` 是整个模块最具特色的技能，**必须保真移植**。同一套画像操作手册，按方向应用相反的行：

- **方向=受托处理者**（`entrusted`）：客户/委托方把其个人信息处理协议发给我们 → **防守性审查**，捍卫运营弹性（审计权、泄露通知时限、转委托、数据存储位置、终止后删除、责任上限）。
- **方向=个人信息处理者**（`handler`，即委托方/控制者）：我们把协议发给供应商/受托方 → **保护性审查**，确保拿到我们履行个保法义务所需（转委托清单、审计权、泄露通知、删除承诺、跨境机制）。

自动识别方向；不明确时**问一次**（识别错则每条修订标记反向）。落库 `privacy_reviews.direction`。

### 2.4 定时代理

| 代理 | 调度 | 功能 | 是否调 LLM |
|------|------|------|-----------|
| privacy_policy_sweep_reminder | 每周一 09:23（错峰；09:07/09:37 已被 renewal/leave 占用） | 数 `privacy_reviews` 自画像 `last_policy_sweep` 以来的新增条数，>0 则推"有 N 项新输出待政策扫描"通知 | **否**（纯算术，照 dataroom_watcher） |

> 说明：ZH 的 policy-monitor 扫描本身是语义比对（需 LLM），因此扫描走 **WS `action=policy_sweep`**（用户主动触发）；cron 只做"该跑扫描了"的纯算术提醒，符合 cron 不调 LLM 的既有惯例（leave-tracker / dataroom-watcher）。

---

## 3. 复用既有架构（镜像 corporate / employment）

### 3.1 直接复用的公共引擎（不新建）

| 组件 | 路径 | 复用方式 |
|------|------|---------|
| 模型工厂 | `agents/model_factory.py` → `create_pydantic_model()` | 直接调用 |
| Agent 流式引擎 | `services/agent_stream.py` → `stream_agent_run()` | 直接调用 |
| WS 连接管理 | `services/agent.py` → `AgentConnectionManager` | 直接复用 |
| WS 鉴权 | `api/deps.py` → `get_current_user_ws` | 直接复用 |
| 调度器 | `scheduler.py`（APScheduler，已挂在 lifespan） | **只新增一个 job**，不改 lifespan |
| module_configs 表 | `db/models/module_config.py` | 直接复用，`module_name="privacy-legal"` |
| 法律检索工具 | `agents/tools/law_tools.py` → `search_law / get_law_article` | 按需挂到需法条的技能 |
| 领域异常 | `core/exceptions.py`（NotFoundError 等） | 直接复用 |
| 冷启动状态机基类 | `services/cold_start_service.py`（commercial 版状态机） | 复制为 privacy 版 |

### 3.2 复制 corporate/employment 模式新建的组件（**复制而非共享**）

profile / cold-start / WS / route 在各模块间是**逐字并行的多份代码**（如 `employment_profile_service.py` 与 `corporate_profile_service.py` 结构一致），不存在共享 company-profile。privacy 同样新建自己的一套：

| 组件 | 镜像来源 | privacy 新建 |
|------|---------|----------------|
| Agent 工厂 | `agents/employment/agent.py` | `agents/privacy/agent.py` |
| Agent Deps | `agents/employment/deps.py` | `agents/privacy/deps.py` |
| 提示词 | `agents/employment/prompts/` | `agents/privacy/prompts/` |
| 工具 | `agents/employment/tools/` | `agents/privacy/tools/` |
| WS 端点 | `api/routes/v1/employment_ws.py` | `api/routes/v1/privacy_ws.py` |
| REST 端点 | `api/routes/v1/employment.py` | `api/routes/v1/privacy.py` |
| profile service | `services/employment_profile_service.py` | `services/privacy_profile_service.py` |
| cold-start service | `services/employment_cold_start_service.py` | `services/privacy_cold_start_service.py` |
| 子服务 | `services/employment_*_service.py` | `services/privacy_*_service.py` |
| 通知模型 | `db/models/employment_notification.py` | `db/models/privacy_notification.py` |
| 定时任务 | `tasks/employment_leave_tracker.py` | `tasks/privacy_policy_sweep_reminder.py` |
| 前端 API 客户端 | `lib/employment.ts` | `lib/privacy.ts` |
| 前端聊天 Hook | `hooks/use-employment-chat.ts` | `hooks/use-privacy-chat.ts` |
| 前端类型 | `types/employment.ts` | `types/privacy.ts` |
| 前端代理路由 | `app/api/employment/[[...path]]/route.ts` | `app/api/privacy/[[...path]]/route.ts` |

---

## 4. 数据模型设计

### 4.1 ORM 约定（强制）

所有模型用 SQLAlchemy `Mapped` 风格 + 继承 `Base, TimestampMixin`（见 `db/models/employment_profile.py`），**不手写 created_at/updated_at**；`String(36)` 主键 + `default=lambda: str(uuid.uuid4())`；FK `ondelete="CASCADE"`。下文用字段表描述结构，**不用裸 `CREATE TABLE`**。复杂结构一律 JSON 文本列（repo 序列化、schema 用 `field_validator` 反序列化）。

### 4.2 表清单（4 张新表 + 复用 module_configs）

> 设计取舍：分诊/PIA/DPA/法规差距/政策扫描这 5 类**分析产出**结构相近且需互相引用（跨技能严重性底线 + 同对方当事人/同活动的 prior-context 检索），故统一进 **`privacy_reviews`**（`review_type` 判别 + `result_json`），照 employment `employment_reviews` 的成功做法。**DSAR 生命周期独特**（两函、期限、豁免、审计日志），单独建 **`privacy_dsar`**。

#### 4.2.1 `privacy_profiles`（个人信息保护实践画像，1:1 用户）

镜像 ZH `CLAUDE.md` 各节，JSON 列承载：

- 基本：`regulatory_footprint` JSON（个保法/数安法/网安法/行业监管，仅列实际适用）、`data_residency`、`dpo_info`、`open_reg_matters`
- 使用者：`user_role`（lawyer / non_lawyer_with_counsel / non_lawyer_without）、`lawyer_contact`、`practice_setting`
- 集成：`integrations` JSON（doc_storage / im / scheduled_tasks，本期多为 ✗）
- DPA 操作手册：`dpa_playbook` JSON（`entrusted` 受托处理者侧表 + `handler` 个人信息处理者侧表 + `auto_reject` 自动拒绝条款）
- 处理规则承诺：`policy_commitments` JSON（data_categories / purposes / retention / third_parties / user_rights）
- PIA 内部规范：`pia_house_style` JSON（trigger_criteria / structure / depth / approver）
- DSAR 流程：`dsar_process` JSON（volume / handler / systems_list / verification_method / response_sla）
- 升级路径：`escalation_matrix` JSON
- 种子文件：`seed_docs` JSON（privacy_policy / dpa_template / reference_pia 的位置 + 审阅状态 + `[立场未测试]` 标记）
- 输出与表面：`output_config` JSON（naming / policy_file / policy_last_updated / **last_policy_sweep** / surfaces[CMP, AppStore, Google, in-product, sectoral_notices]）
- 状态：`setup_status`（not_started/in_progress/completed）、`setup_progress` JSON、`setup_depth`（quick/full）
- `profile_content`（Markdown，编译后的画像，注入系统提示词）
- `work_product_header`（按 user_role 派生：律师=「保密 — 律师工作成果 — 应律师指示编制」；非律师=「研究笔记 — 非法律建议 …」）
- `UNIQUE(user_id)`

#### 4.2.2 `privacy_reviews`（分析产出统一表，N）

- `user_id`(FK, index)
- `review_type`：`triage` / `pia` / `dpa` / `gap` / `policy_sweep`
- `subject`（处理活动名 / 对方当事人 / 法规名 / "处理规则扫描"——用于 prior-context 检索与严重性底线）
- `counterparty`（可空，DPA/PIA 上下文匹配）
- `direction`（可空：`entrusted` / `handler`——仅 DPA）
- `classification`（可空：`PROCEED`/`PIA_REQUIRED`/`DPIA_MANDATORY`/`STOP`——仅 triage）
- `severity`（可空：🔴/🟠/🟡/🟢——跨技能严重性底线）
- `recommendation`（可空：`APPROVED`/`WITH_CONDITIONS`/`CHANGES_REQUIRED`/`NOT_APPROVED`——仅 PIA）
- `result_summary`（text，底线一两句）、`result_memo`（Markdown 全文）、`result_json`（结构化：conditions / redlines / risks / remediation / gaps）
- `status`（draft/final）
- 由 WS Agent 经 `save_review` 工具写入；REST 仅读历史。`index(user_id, subject)`。

#### 4.2.3 `privacy_dsar`（个人信息主体权利请求，N）

- `user_id`(FK, index)
- `request_types` JSON（access/copy/delete/correct/explain/restrict，可组合；对应个保法第 44–50 条）
- `data_subject_ref`（**最小化标识，禁止把主体姓名写进文件名/主键**——见 ZH 技能开头的 PII 处理要求）
- `date_received`、`date_verified`（可空）、`date_responded`（可空）
- `response_deadline` DATE（按内部 SLA 或法定推算的具体日期；个保法第 45 条为"及时"，以实践 SLA 落具体日）
- `identity_verified` BOOL、`verification_method`
- `systems_checked` JSON（逐系统定位结果）、`exemptions` JSON（主张的豁免 + 依据 + `[提议——需律师审核]`）
- `ack_letter`（Markdown 确认函）、`response_letter`（Markdown 实质回复函）
- `status`（received/verifying/locating/exemption_analysis/drafted/responded/escalated）
- `escalation_flag` BOOL、`escalation_reason`
- `log` JSON（审计：收到/验证/回复日期、提供或删除内容、豁免及依据、处理人）

#### 4.2.4 `privacy_notifications`（通知，N）

照 `employment_notification.py`：`notification_type`（policy_sweep_reminder / manual）、`title`、`content`（Markdown）、`priority`、`is_read`、`action_url`。

### 4.3 实体关系图

```
users (1) ── (1) privacy_profiles
users (1) ── (N) privacy_reviews        [review_type: triage/pia/dpa/gap/policy_sweep]
users (1) ── (N) privacy_dsar
users (1) ── (N) privacy_notifications
users (1) ── (1) module_configs [module_name="privacy-legal"]
```

---

## 5. 后端开发任务

### 5.1 Phase 1：数据层

#### 任务 1.1：Alembic 迁移（**幂等守护强制**）

照 employment 拆 **2 个迁移文件**，链在当前 head 之后（先 `uv run alembic heads` 确认，当前最新为 `2026-06-03_add_*`）：

1. `2026-06-xx_add_privacy_profile_table.py`
2. `2026-06-xx_add_privacy_core_tables.py`（reviews / dsar / notifications）

每个 `upgrade()` 用 inspector 守护（**create_all + Alembic 双轨**，否则 `test_migrations` 红），`downgrade()` 名称无关、逆 FK 顺序 drop：

```python
def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "privacy_profiles" in inspector.get_table_names():   # 锚点表守护
        return
    op.create_table("privacy_profiles", ..., *_ts_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE",
                                name="fk_privacy_profiles_user_id"))
    op.create_index("ix_privacy_profiles_user_id", "privacy_profiles", ["user_id"])

def downgrade() -> None:
    op.drop_table("privacy_profiles")
```

#### 任务 1.2：数据模型（4 文件）
`db/models/privacy_profile.py`、`privacy_review.py`、`privacy_dsar.py`、`privacy_notification.py`。在 `db/models/__init__.py` 导入并加入 `__all__`（`main.py` 启动时 `from app.db import models` 触发 create_all 注册）。

#### 任务 1.3：Repository 层（无状态函数，`db.flush()`+`db.refresh()`，**绝不 commit**）
`privacy_profile_repo.py`、`privacy_review_repo.py`、`privacy_dsar_repo.py`、`privacy_notification_repo.py`。列表函数返回 `(items, total)`；`privacy_review_repo` 提供 `list_by_subject(user_id, subject)` 供 prior-context 检索。JSON 列在 repo 内用 `_to_json` 序列化。

#### 任务 1.4：Schema 层 `schemas/privacy/`
`__init__.py`、`profile.py`、`cold_start.py`、`review.py`、`dsar.py`、`notification.py`。遵循 `*Create/*Update/*Read/*List` + `ConfigDict(from_attributes=True)`；JSON-text 列用 `@field_validator(mode="before")` 解码。

### 5.2 Phase 2：技能引擎

#### 任务 2.1：Agent 工厂（镜像 `employment/agent.py`）
`agents/privacy/agent.py`：

```python
PrivacySkillName = Literal[
    "triage", "dpa", "pia", "gap", "dsar", "policy_sweep", "policy_query",
]
_PROMPT_BUILDERS: dict[PrivacySkillName, Callable[..., str]] = {...}
_SKILL_TOOLS:    dict[PrivacySkillName, tuple[Callable, ...]] = {...}
# 需要法条检索的技能挂 search_law / get_law_article：
_LAW_TOOL_SKILLS: frozenset[PrivacySkillName] = frozenset(
    {"triage", "dpa", "pia", "gap", "dsar"}   # policy_* 主要比对内部画像，可不挂
)

def create_privacy_agent(skill, *, practice_profile_markdown=None,
                         model_name=None, provider=None, api_key=None,
                         base_url=None, temperature=None) -> Agent[PrivacyDeps, str]:
    ...  # 同 employment：查 builder、create_pydantic_model、挂 _SKILL_TOOLS[skill]、按需挂 law tools、tool_retries=3
```

`agents/privacy/deps.py`：

```python
@dataclass
class PrivacyDeps:
    user_id: str
    db: Session
    review_id: str | None = None     # PIA/DPA/gap/triage/sweep 预建行后回填
    dsar_id: str | None = None       # DSAR 起草目标
    output_dir: str | None = None
```

#### 任务 2.2：提示词提取 `agents/privacy/prompts/`
从 `~/.claude/plugins/marketplaces/claude-for-legal-zh/privacy-legal/skills/*/SKILL.md` **逐段提取，保留全部实质内容**（中国法条引用、四分类、双向 DPA 表、两函流程、六维度风险、多表面扫描等）：

| 文件 | 来源 SKILL.md |
|------|-------------|
| `security.py` | 共享护栏（来源溯源三层 / 三值处理 / 严重性底线 / 工作成果抬头-中国法 / 审阅备注 / 目的地检查 / 决策树 / 关口） |
| `use_case_triage.py` | use-case-triage |
| `dpa_review.py` | dpa-review（双向，核心见 §7.3） |
| `pia_generation.py` | pia-generation（个保法第 55/13/28-30/38 条） |
| `reg_gap_analysis.py` | reg-gap-analysis |
| `dsar_response.py` | dsar-response（两函 + 第 44-50 条） |
| `policy_monitor.py` | policy-monitor（sweep + query 两模式） |

> cold-start 提示词**不在此**——它是 service 状态机（任务 2.4）。

#### 任务 2.3：工具 `agents/privacy/tools/`
签名一律 `async def tool(ctx: RunContext[PrivacyDeps])`，内部做归属校验（照 employment `tools/*` 的 `_load_owned_*` 模式）。

| 文件 | 工具 |
|------|------|
| `profile_tools.py` | `read_privacy_profile`（读画像；未配置则提示去设置） |
| `review_tools.py` | `save_review`（写 privacy_reviews，含 type/severity/classification/direction/recommendation）、`read_prior_reviews`（按 subject/counterparty 查 prior triage/PIA/DPA，支撑严重性底线） |
| `dsar_tools.py` | `read_dsar`、`save_dsar_letters`（回写 ack_letter/response_letter/exemptions/log/status） |
| `policy_tools.py` | `read_policy_commitments`、`list_recent_reviews`（扫描自 last_policy_sweep 的 reviews）、`save_policy_sweep`（写 review+notification，更新 last_policy_sweep） |
| `law_tools.py`（封装复用） | `research_privacy_rules(topic, regime)`：先读画像 regulatory_footprint，再 RAG `search_law`（个保法/数安法/网安法），标注来源标签（见 §7.10、§9） |

#### 任务 2.4：cold-start service（**非 Agent**）
`services/privacy_cold_start_service.py` 复制 `employment_cold_start_service.py` 状态机，6 步（对照 ZH cold-start-interview）：

```
0 角色 + 执业环境 + 集成        1 监管覆盖范围（个保法/数安法/网安法/行业，多选）+ 业务模式（处理者/受托处理者/两者）
2 DPA 谈判立场（受托侧 + 处理者侧 + 自动拒绝）   3 内部规范（PIA 触发/格式/审批 + DSAR 量级/处理人/系统清单/SLA）
4 种子文件（处理规则 / DPA 模板 / 参考 PIA）     5 输出与表面 + 生成画像
QUICK_PLAN=(0,1,5)   FULL_PLAN=(0,1,2,3,4,5)
```
`MODULE_NAME="privacy-legal"`，终步 `_materialize_profile` 编译并写 `privacy_profiles.profile_content` + 各 JSON 字段；跳过项写 `[占位符]`/`[立场未测试]`（绝不静默缺口）。

### 5.3 Phase 3：API 端点

#### 任务 3.1：REST（`api/routes/v1/privacy.py`，全部 CRUD，照 employment.py 签名）
处理器签名 `(... , user: CurrentUser, svc: PrivacyXxxSvc) -> Any`，声明 `response_model` + 必要 `status_code`，分页 `skip/limit`：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/privacy/status` | GET | 模块配置状态（驱动前端"去设置 vs 主界面"） |
| `/privacy/setup` | POST | 冷启动步骤提交 |
| `/privacy/setup/status` | GET | 冷启动进度 |
| `/privacy/profile` | GET / PUT | 实践画像（PUT 即 customize） |
| `/privacy/reviews` | GET | 分析产出列表（可按 type 过滤） |
| `/privacy/reviews/{id}` | GET | 产出详情 |
| `/privacy/dsar` | GET / POST | DSAR 列表 / 建档（POST 落 PII 最小化档 + 算 response_deadline） |
| `/privacy/dsar/{id}` | GET / PUT | DSAR 详情 / 更新（验证状态、升级标记） |
| `/privacy/notifications` | GET | 通知列表 |
| `/privacy/notifications/{id}/read` | POST | 标记已读 |

#### 任务 3.2：WS（`api/routes/v1/privacy_ws.py`，镜像 employment_ws.py）
- `_SKILL_BY_ACTION` 显式映射 7 个 action → `create_privacy_agent(skill)`
- `_require_llm_configured`：未配置 LLM → 推 `error / llm_not_configured`（**绝不兜底**）
- 归属预校验（review_id / dsar_id 属于该用户）
- `triage/pia/dpa/gap/policy_sweep` 仿 tabular **预建 privacy_reviews 行**并推 `review_started`；`dsar` 需先解析 dsar_id
- 复用 `stream_agent_run`，事件名一致（见 §6.7）

#### 任务 3.3：DI / 注册 / 挂载
- `api/deps.py`：加 `get_privacy_*_service` + `Annotated` 别名（`PrivacyProfileSvc` / `PrivacyReviewSvc` / `PrivacyDsarSvc` / `PrivacyNotificationSvc`）
- `api/routes/v1/__init__.py`：在 employment 之后加
  ```python
  from app.api.routes.v1 import privacy, privacy_ws
  v1_router.include_router(privacy.router, prefix="/privacy", tags=["privacy"])
  v1_router.include_router(privacy_ws.router, tags=["privacy-ws"])
  ```
- `main.py` lifespan **无需改**（scheduler 已挂）

### 5.4 Phase 4：定时代理
`tasks/privacy_policy_sweep_reminder.py`，照 `dataroom_watcher.py` 写 `run(db) -> int`：遍历 `iter_active_user_ids`、数 `privacy_reviews` 自画像 `last_policy_sweep` 以来的新增条数、>0 写 `privacy_notifications`。**不调 LLM。** `scheduler.py` 新增 job（周一 09:23）。

### 5.5 Phase 5：服务层
`privacy_profile_service.py`、`privacy_cold_start_service.py`（任务 2.4 已起）、`privacy_review_service.py`、`privacy_dsar_service.py`（含建档时算 response_deadline、升级触发判定）、`privacy_notification_service.py`。可按 employment 把小服务合并到 `privacy_child_services.py`。

---

## 6. 前端开发任务

### 6.1 页面结构 `frontend/src/app/[locale]/(dashboard)/privacy/`

```
privacy/
├── page.tsx                      # 概览（未配置 → 引导冷启动）
├── setup/page.tsx                # 冷启动向导（ColdStartWizard）
├── triage/page.tsx               # 处理活动分诊（WS 流式 + 四分类结果，支持续跑 PIA）
├── reviews/
│   ├── page.tsx                  # 分析产出列表（triage/pia/dpa/gap/sweep 分 tab）
│   └── [id]/page.tsx             # 产出详情
├── dpa/page.tsx                  # DPA 审查入口（方向选择 + 上传/粘贴 + WS）
├── pia/page.tsx                  # PIA 生成入口（录入 + WS）
├── gap/page.tsx                  # 法规差距分析入口（WS）
├── dsar/
│   ├── page.tsx                  # DSAR 列表（按期限/状态分组）
│   └── [id]/page.tsx             # DSAR 详情（分类/验证/定位/豁免/两函/日志）
├── policy-monitor/page.tsx       # 处理规则监控（扫描 + 直接查询双入口）
└── settings/page.tsx             # 实践画像设置（customize）
```

### 6.2 关键页面
- **概览**：SetupStatusCard / QuickActions（分诊/DPA/PIA/DSAR）/ StatsCards / DsarDeadlineSummary / RecentReviewsList / NotificationArea。
- **冷启动**：`ColdStartWizard`（镜像 `components/employment` 或 `commercial/cold-start-wizard.tsx`），6 步，调 `privacyApi.submitSetupStep`，服务端 materialize 后跳概览。**纯表单，非 WS。**
- **分诊**：描述活动 → WS `triage` 流式 → 四分类徽章（🟢🟡🟠🔴）+ 条件表 + "是否现在开始 PIA"续跑按钮。
- **DPA 审查**：先选**方向**（受托处理者 / 个人信息处理者，或"自动识别"）→ 上传/粘贴协议 → WS `dpa` → 逐条 term-by-term + 双轴风险 + 修订建议 + 一致性检查。
- **DSAR**：列表按 `response_deadline` 紧急度分组；详情走"建档(REST) → 起草两函(WS `dsar`)"，展示确认函 + 实质函 + 豁免清单（带 `[提议——需律师审核]`）+ 审计日志；**对外函件不带工作成果抬头**（UI 文案区分）。
- **PIA / 法规差距 / 政策监控**：录入/描述 → WS 流式 → 结构化结果 + 详情存 reviews。

### 6.3 通用组件 `frontend/src/components/privacy/`
`TriageClassificationBadge`（🟢🟡🟠🔴）、`SeverityBadge`、`DpaDirectionSelector`（受托/处理者）、`DsarDeadlineBadge`、`DsarLetterView`（确认函/实质函双栏）、`ExemptionList`、`ReviewTypeTabs`、`RiskMatrix`（六维度/双轴）、`ConditionsChecklist`、`NotificationArea`、`ColdStartWizard`、`ReviewerNote`（审阅备注区块）、`WorkProductHeader`（按角色）。

### 6.4 导航注册
- `components/layout/app-sidebar.tsx`：`navigation` 数组加 `{ name: t("privacy"), href: ROUTES.PRIVACY, icon: ShieldCheck }`（Lucide）
- `lib/constants.ts`：加 `PRIVACY: "/privacy"` 等 ROUTES
- i18n 文案（`messages/zh.json` + `en.json`）加 `privacy` key（zh 为主）

### 6.5 类型 `types/privacy.ts`
镜像 `types/employment.ts`：枚举（ReviewType / TriageClassification / DpaDirection / DsarRequestType / DsarStatus / Severity / UserRole）、实体接口、`PrivacyWsMessage`（`{action, ...}`）、`PrivacyWsEvent` 联合类型。

### 6.6 API 客户端 `lib/privacy.ts` + 代理 `app/api/privacy/[[...path]]/route.ts`
`privacyApi` 对象包 `apiClient`（GET/POST/PUT/upload）；catch-all 代理转发到 `/api/v1/privacy/*`，从 cookie 取 `access_token` 注入 Bearer（照 employment 代理，支持 multipart 以便种子文件/协议上传）。

### 6.7 聊天 Hook `hooks/use-privacy-chat.ts`
镜像 `use-employment-chat.ts`：WS URL `${getWsUrl()}/api/v1/ws/privacy`，subprotocols `[`access_token.${token}`, "privacy"]`；发送 `{ action, review_id?/dsar_id?, prompt/payload }`；处理事件 `text_delta` / `tool_call` / `tool_result` / `final_result` / `complete` / `error`（+ `review_started`）。

---

## 7. 技能实现详解

### 7.1 技能分发（显式 action，无意图路由）
前端按用户选择的功能直接发对应 `action`（点「审查 DPA」→ `action=dpa`）。后端 `_SKILL_BY_ACTION` 校验后建 Agent。**不做关键词意图识别**——与 corporate/employment 一致，避免中文意图歧义与隐性兜底。

### 7.2 use-case-triage（处理活动分诊）
四分类：🟢 PROCEED / 🟡 PIA_REQUIRED / 🟠 DPIA_MANDATORY（**个保法第 55 条**强制评估情形）/ 🔴 STOP（与处理规则冲突或无合法性基础）。流程：读画像 → 理解活动（模糊则追问）→ 行业监管叠加询问（金融/医疗/儿童等）→ 各适用制度强制评估检索 → 处理规则冲突检查 → 分类 + 条件表。结果落 `privacy_reviews(type=triage, classification, severity)`；若需 PIA，结尾提供续跑入口。

### 7.3 dpa-review（双向，核心）
1. 加载画像 DPA 操作手册（受托侧/处理者侧两张表）。
2. **定方向**（受托处理者/个人信息处理者；不明确问一次）→ 落 `direction`。
3. 读 prior triage/PIA/DPA（同对方当事人）→ **继承严重性底线**。
4. 行业监管叠加（金融/医疗/儿童/汽车数据等）先问。
5. **逐条 term-by-term**（角色、处理范围、转委托、安全措施、泄露通知、审计权、跨境、删除、责任），用 ZH 表里的具体立场。
6. **六维度风险评价 + 双轴风险表**（法律风险 / 商业摩擦，🔴🟠🟡⚪）——这是 ZH CLAUDE.md「风险评价方法论（中国法适用）」的硬要求，必须进提示词。
7. 处理规则一致性检查 → 修订建议（**最小粒度 redline**：词→短语→子句→整句→整条）。
8. 跨境：检索现行出境机制（安全评估 / 标准合同 / 认证，个保法第 38 条）；缺失即 🔴。
9. 关口：非律师签署前生成 1 页简报。落 `privacy_reviews(type=dpa)`。

### 7.4 pia-generation（个人信息保护影响评估）
读画像 PIA 内部规范 + prior triage（继承严重性底线）→ 第 0 步"是否需要 PIA"（**个保法第 55 条**四类情形 + 数据出境安全评估 + 算法安全评估，检索主源）→ 录入（什么/为什么/合法性基础**个保法第 13 条**/敏感个人信息**第 28-30 条**/出境**第 38 条**/谁和哪里/什么可能出错）→ 用种子 PIA 结构撰写（摘要/处理活动描述/合法性基础表/数据流转/处理规则一致性/风险与缓解/主体权利**第 44-50 条**/建议）→ **风险质量标准**（2-5 个具体风险，禁止"数据泄露"泛述）→ 条件清单（带负责人+截止）。关口：向网信办提交前非律师出简报。落 `privacy_reviews(type=pia, recommendation)`。

### 7.5 dsar-response（个人信息主体权利响应）
**两函规则强制**：5a 确认函（数日内）+ 5b 实质回复函（法定/SLA 期限内）。流程：分类请求（查阅第45/复制第45/删除第47/更正第46/解释第48/限制第44 条）→ 验证身份（按风险校准）→ 遍历系统清单定位 → **豁免分析**（善意依据即提议、不主观缩小、每项带 `[提议——需律师审核]`）→ 起草两函 → 记录审计日志。**对外两函不带工作成果抬头**；内部豁免分析/日志带抬头。关口：非律师发函前出简报。落 `privacy_dsar`。

### 7.6 reg-gap-analysis（法规差距分析）
新法规 vs 当前画像（处理规则承诺 / 监管覆盖 / DSAR 系统）：第 1 步界定（是否适用/何时生效/新增什么）→ 第 2 步抽取要求（逐条引法条）→ 第 3 步差距对比（无/部分/完全 + 工作量）→ 第 4 步优先级（硬期限+执法+罚则）→ 第 5 步整改计划（必做/应做/已合规/已接受差距，带负责人+截止日）。即便"无差距"也写一份带日期的备忘录留痕。落 `privacy_reviews(type=gap)`。

### 7.7 policy-monitor（处理规则漂移监控）
**扫描模式（WS `policy_sweep`）**：读自 `last_policy_sweep` 以来的 `privacy_reviews` → 逐类抽取已批准做法 → diff 处理规则承诺 → 分类**必须更新**（构成不实陈述）/**建议更新** → 起草建议语言 → 写 review + 通知 + 更新 `last_policy_sweep`。**多表面扫描**：网站处理规则 + CMP/Cookie 横幅 + App Store/Google 标签 + 产品内同意流程 + **行业通知**（金融/医疗/儿童/汽车数据，缺失则每次标示）。
**直接查询模式（WS `policy_query`）**：解析拟议实践 → 六检查点 diff（数据类别/目的/第三方/保留/用户权利/披露）→ 已覆盖/缺失/冲突 + 建议语言 + 时机。
**cron 提醒**：纯算术数新 review 条数（§8）。

### 7.8 cold-start-interview（冷启动）
service 状态机 + 前端向导（§5.2 任务 2.4、§6.2）。保真 ZH 的"快速(2 分钟)/完整(15 分钟)"分叉、对真实回答暂停等待、即时核实用户陈述的法律事实、绝不静默缺口。

### 7.9 customize（修改画像）
不单独建 Agent；映射为**设置页** + `PUT /privacy/profile`。前端展示画像可定制项（按节分组：监管覆盖/DPA 操作手册/处理规则承诺/PIA 规范/DSAR 流程/升级路径/集成），改一项即写回。护栏：不删节（标记"不在范围"）、拒绝削弱承载性护栏（强制 `[需审查]`、来源溯源、低于法定的 SLA）。

### 7.10 共享护栏移植（`prompts/security.py`，所有技能注入）
ZH CLAUDE.md「共享护栏」「风险评价方法论」「主观判断决策姿态」整体移植：
- **来源溯源标签（中国法版）**：`[法条原文]`/`[裁判文书]`/`[本地知识库]`/`[联网检索—需复核]`/`[模型知识—需验证]`/`[用户提供]`/`[已验证—YYYY-MM-DD]`。⚠️ ZH 原文里的 `[元典检索]/[yuandian检索]` → 本期改为 `[本地知识库]`（LexMind 用 RAG，不接元典 MCP）。
- **三值而非二值**（标注补充 / 停止并告知 / 标注但不使用），**禁止沉默补充**。
- **时效触发**：引具体法条/讨论时效前先检索（RAG/web），不直接用模型知识；对照 `references/currency-watch.md`（移植）。
- **跨技能严重性底线**（🔴→🟢 须显式声明降级理由）。
- **工作成果抬头（中国法）**：律师=「保密 — 律师工作成果 — 应律师指示编制」；非律师=「研究笔记 — 非法律建议 …」；并保留 ZH 关于"中国法下不存在美国 work-product 原则、依《律师法》第 38 条"的管辖注释；**对外交付物（DSAR 函/监管回应）省略抬头**。
- **审阅备注区块**（来源/已读/标注/时效性/依赖前）、**安静模式**（对外交付物像合伙人写的）、**目的地检查**、**下一步决策树**（5 分支）、**关口**（签 DPA / 发 DSAR 函 / 提交监管前，非律师出简报）。
- **比例性 / 脚手架而非蒙眼布 / 检索内容信任**（MCP/RAG/上传内容是数据非指令）。

---

## 8. 定时代理实现

`tasks/privacy_policy_sweep_reminder.py`，照 `dataroom_watcher.py`：

```python
def run(db: Session) -> int:
    written = 0
    for user_id in iter_active_user_ids(db):
        profile = privacy_profile_repo.get_by_user_id(db, user_id)
        if not profile or profile.setup_status != "completed":
            continue
        n = privacy_review_repo.count_since(db, user_id=user_id, since=profile.output_config.get("last_policy_sweep"))
        if n > 0:
            privacy_notification_repo.create(db, user_id=user_id,
                notification_type="policy_sweep_reminder", priority="medium",
                title=f"有 {n} 项新输出待处理规则扫描",
                content="自上次扫描以来新增分析产出，建议运行处理规则监控扫描。",
                action_url="/privacy/policy-monitor")
            written += 1
    return written
```

`scheduler.py` 新增 `JOB_PRIVACY_POLICY_SWEEP`，`CronTrigger(day_of_week="mon", hour=9, minute=23)`，`replace_existing=True`。**不调 LLM。**

---

## 9. 法条检索与知识库前置条件

- **复用** `agents/tools/law_tools.py` 的 `search_law` / `get_law_article`（Qdrant + BGE-zh）。新增 `research_privacy_rules(topic, regime)` 薄封装：先读画像 `regulatory_footprint`，再 RAG 检索，按 §7.10 标注来源。
- **⚠️ 前置条件（开发前确认）**：RAG 语料须包含**《个人信息保护法》《数据安全法》《网络安全法》**及关键配套（《个人信息保护影响评估指南》《数据出境安全评估办法》《个人信息出境标准合同办法》《儿童个人信息网络保护规定》等）。若缺，按 `docs/howto/add-rag-source.md` 先行入库，否则 `research_privacy_rules` 命中率不足、技能将频繁"禁止沉默补充"停下。
- **移植 references**：把 `claude-for-legal-zh/privacy-legal/references/pipil-core-provisions.md`（个保法核心条款）与 `currency-watch.md`（时效监测）作为模块参考数据（照 employment 的 `references/labor-core-rules.md` 处理）——可放 `backend/app/agents/privacy/references/` 供提示词/工具引用。

---

## 10. 开发排期

### 总工期：约 3.5–4.5 周（比 employment 略省——4 张表 vs 9 张、7 action vs 11）

```
Week 1  数据层 + 技能引擎起步
  D1 迁移(2文件,幂等守护) + 模型(4)    D2 Repository + Schema
  D3 服务层(profile + cold-start 状态机)    D4 Agent工厂+Deps + 提示词(security, triage)
  D5 提示词(dpa, pia)

Week 2  技能引擎完成 + API
  D1 提示词(dsar, gap, policy_monitor)    D2 工具(profile/review/dsar/policy/law)
  D3 REST(~12端点) + DI/注册/挂载    D4 WS(7 action,预建行)    D5 cron + API 集成测试

Week 3  前端
  D1 冷启动向导 + 分诊页(WS)    D2 DPA审查页(方向+双轴风险) + PIA页
  D3 DSAR列表/详情(两函+豁免+日志)    D4 reviews列表/详情 + 政策监控 + 设置页
  D5 导航/代理/Hook/类型 + 通用组件(徽章/RiskMatrix/ReviewerNote)

Week 4  联调 + 测试 + 部署
  D1-2 全链路联调（7 技能手测 + 冷启动）    D3 集成测试(tests/privacy/: repo/service/scheduler/migrations)
  D4-5 Bug 修复 + 部署
```

### 里程碑
| 里程碑 | 目标 | 交付物 |
|--------|------|--------|
| M1 数据层就绪 | W1 D2 | 4 表 + Repo + Schema（迁移幂等过 test_migrations） |
| M2 冷启动可运行 | W1 D3 | cold-start 状态机贯通 |
| M3 双向 DPA 可运行 | W1 D5 | dpa WS 技能手测通过（两方向） |
| M4 全部 Agent 技能可用 | W2 D2 | 7 个 WS action 手测通过 |
| M5 API 完成 | W2 D5 | REST + WS + cron |
| M6 前端完成 | W3 D5 | 所有页面可用 |
| M7 验收通过 | W4 D5 | 全功能 + tests/privacy 绿 |

---

## 11. 附录：关键文件清单

### 11.1 需读取的源文件（claude-for-legal-zh，**以 -zh 为准**）
`~/.claude/plugins/marketplaces/claude-for-legal-zh/privacy-legal/`：`CLAUDE.md`（画像模板 + 共享护栏 + 风险方法论）、`references/pipil-core-provisions.md`、`references/currency-watch.md`、`skills/{cold-start-interview,customize,use-case-triage,dpa-review,dsar-response,pia-generation,reg-gap-analysis,policy-monitor}/SKILL.md`。

### 11.2 需新建的后端文件
```
backend/app/
├── agents/privacy/
│   ├── __init__.py  agent.py  deps.py
│   ├── tools/  (profile_tools, review_tools, dsar_tools, policy_tools, law_tools)
│   ├── prompts/ (security, use_case_triage, dpa_review, pia_generation,
│   │             reg_gap_analysis, dsar_response, policy_monitor)
│   └── references/ (pipil-core-provisions.md, currency-watch.md  ← 移植)
├── api/routes/v1/  privacy.py  privacy_ws.py
├── db/models/  privacy_profile.py  privacy_review.py  privacy_dsar.py  privacy_notification.py
├── repositories/  privacy_profile_repo.py  privacy_review_repo.py  privacy_dsar_repo.py  privacy_notification_repo.py
├── schemas/privacy/  __init__.py profile.py cold_start.py review.py dsar.py notification.py
├── services/  privacy_profile_service.py  privacy_cold_start_service.py  privacy_review_service.py
│              privacy_dsar_service.py  privacy_notification_service.py
├── tasks/  privacy_policy_sweep_reminder.py
└── alembic/versions/  (2 个迁移文件，幂等守护)
更新：db/models/__init__.py  api/deps.py  api/routes/v1/__init__.py  scheduler.py
```

### 11.3 需新建的前端文件
```
frontend/src/
├── app/[locale]/(dashboard)/privacy/  (page + setup + triage + reviews[/id] + dpa + pia + gap + dsar[/id] + policy-monitor + settings)
├── app/api/privacy/[[...path]]/route.ts
├── components/privacy/  (TriageClassificationBadge, SeverityBadge, DpaDirectionSelector, DsarDeadlineBadge,
│                         DsarLetterView, ExemptionList, ReviewTypeTabs, RiskMatrix, ConditionsChecklist,
│                         NotificationArea, ColdStartWizard, ReviewerNote, WorkProductHeader)
├── hooks/use-privacy-chat.ts
├── lib/privacy.ts
└── types/privacy.ts
更新：components/layout/app-sidebar.tsx  lib/constants.ts  messages/{zh,en}.json
```

### 11.4 Required Verification（每阶段完成前）
后端：`uv run ruff check . --fix && uv run ruff format . && uv run ty check && uv run pytest`（含 `tests/privacy/` 与 `test_migrations`）。
前端：`bun run lint && bun test`。
端到端手测：① 冷启动向导贯通写画像；② 未配置 LLM 时 WS 报 `llm_not_configured`（不兜底）；③ 7 个 WS action 各跑一次（重点：dpa 两方向、dsar 两函 + 对外无抬头、triage→PIA 续跑、severity floor）；④ cron 手动触发产出提醒通知；⑤ 设置页改一项画像写回生效。

---

## 设计决策小结（供审阅）

1. **法域 = 中国法**（个保法/数安法/网安法）：源为 `claude-for-legal-zh` 中文本地化版，非英文 GDPR/CCPA 上游。复用现有中文 RAG。
2. **范围 = 用户列的 7 技能 + customize(设置页) + 冷启动基础设施**；`matter-workspace` 延后（不在 7 技能内 + 照 employment 先例用实践级上下文）。
3. **架构 = 逐项镜像 employment**（最新同构样板）：传输层三分（WS 显式 action / REST CRUD / cron 纯算术）、独立 profile 表（复制非共享）、迁移幂等守护、绝不兜底。
4. **数据模型 = 4 张表**（profile / reviews 统一 / dsar 独立 / notifications）。
5. **保真重点**：双向 DPA（受托↔处理者）、六维度+双轴风险、两函 DSAR、个保法条文引用、共享护栏（来源标签改 `[本地知识库]`、工作成果抬头中国法版、严重性底线、关口）。

*文档生成时间：2026-06-07（v1.0）*
*基于 claude-for-legal-zh 隐私数据模块（v1.0.2-zh）+ LexMind 现行架构*
*架构逐项镜像 employment（劳动用工）模块的真实实现*
