# 劳动用工模块（Employment-Legal）开发计划

**版本：** 2.0
**日期：** 2026-06-03
**目标：** 将 claude-for-legal-zh 的劳动用工模块完整融入 LexMind，**严格复用 corporate（公司并购）模块已验证的真实架构模式**

> **v2.0 修订说明（相对 v1.0）**
> v1.0 整体策略成立，但经逐条对照仓库真实代码，修正了 1 处关键架构偏离 + 5 处问题：
> 1. **删除「统一技能注册表 + 关键词意图路由」** → 改为 corporate 的真实三分法：Agent 技能走 WebSocket（显式 `action` 分发，无意图路由）、CRUD/表单走 REST、定时任务走 cron。（见 §2.1、§5.2、§7.1）
> 2. **cold-start 重新定位**为 service 状态机 + 前端向导，**不是 Agent 技能**。（见 §5.2、§6.2.2）
> 3. **去掉「共享 company-profile」措辞** → 每模块独立 `employment_profiles` 表 + service，复制 corporate 模式。（见 §3）
> 4. **内部调查结构化建模** → 拆为 4 张表（matter 头 + 日志条目 + 来源清单 + 证据缺口），保住 investigation-query/memo 的引用与覆盖分析能力。（见 §4、§7.4）
> 5. **leave-tracker 计算模型修正** → 法条相关到期日在 log-leave 交互时算好落库为具体日期，cron 只做纯日期算术（无 LLM），与 dataroom_watcher 一致。（见 §8）
> 6. **迁移幂等 + ORM 约定** → 新建表迁移必须 inspector 守护 + 名称无关 downgrade；模型用 `Mapped`/`String(36)`/`TimestampMixin`，裸 SQL 仅作示意。（见 §4.1、§5.1）
> 范围锁定：**16 技能**，延后 `matter-workspace` 与 `international-expansion`，删除 `overseas_jurisdictions` 字段。

---

## 目录

1. [总体目标与范围](#1-总体目标与范围)
2. [模块全景（技能按传输层三分）](#2-模块全景技能按传输层三分)
3. [复用 corporate 模块的架构模式](#3-复用-corporate-模块的架构模式)
4. [数据模型设计](#4-数据模型设计)
5. [后端开发任务](#5-后端开发任务)
6. [前端开发任务](#6-前端开发任务)
7. [技能实现详解](#7-技能实现详解)
8. [定时代理实现](#8-定时代理实现)
9. [开发排期](#9-开发排期)
10. [附录：关键文件清单](#10-附录关键文件清单)

---

## 1. 总体目标与范围

### 1.1 目标

将 claude-for-legal-zh 劳动用工模块的 **16 个技能 + 1 个定时代理** 移植到 LexMind：

- 用户访问「劳动用工」模块时，若未配置则引导冷启动访谈
- 配置完成后，用户可通过前端界面使用全部 16 个技能
- 1 个定时代理（leave-tracker）在后台自动运行
- 后端 Agent/提示词/工具完全遵循 claude-for-legal-zh 的 SKILL.md 定义
- **架构上逐项镜像 corporate 模块**（最新、最接近的同构样板）

### 1.2 范围

**包含（16 技能）：**
cold-start-interview, hiring-review, termination-review, policy-drafting, wage-hour-qa, worker-classification, expansion-kickoff, expansion-update, investigation-open, investigation-add, investigation-query, investigation-memo, investigation-summary, leave-tracker, log-leave, handbook-updates

**明确延后（不在本期）：**
- `matter-workspace`（事项工作区锚点）— in-house 用户默认隐藏 matter 概念，本期用 practice-level 上下文；后续若需多事项隔离再引入（届时照 corporate 的 `CorporateDeal` 建 `employment_matters`）。
- `international-expansion`（海外扩张）— 本期只做境内异地（省际）扩张；**因此删除 v1 profile 表里的 `overseas_jurisdictions` 字段**。
- MCP 外部集成（HRIS、飞书等）；元典 MCP 检索（当前用 RAG 替代）。

### 1.3 与 commercial / corporate 模块的关系

| 维度 | commercial（已实现） | corporate（已实现） | employment（本期） |
|------|------|------|------|
| 路由前缀 | `/commercial` | `/corporate` | `/employment` |
| module_configs.module_name | `commercial-legal` | `corporate-legal` | `employment-legal` |
| 独立 profile 表 | `commercial_profiles` | `corporate_profiles` | `employment_profiles`（新建，**非共享**） |
| Agent 工厂 | `agents/commercial/agent.py` | `agents/corporate/agent.py` | `agents/employment/agent.py`（镜像 corporate） |
| WS 端点 | `/ws/commercial` | `/ws/corporate` | `/ws/employment` |
| 定时任务 | renewal_watcher, deal_debrief | dataroom_watcher | leave_tracker |
| 前端页面 | `/commercial/*` | `/corporate/*` | `/employment/*` |

---

## 2. 模块全景（技能按传输层三分）

**核心原则（来自 corporate 真实代码）：** `corporate.py` 的 28 个 REST 端点**全部是 CRUD（纯 service 调用）**；所有 Agent 驱动的技能**只走 WebSocket**，前端用显式 `action` 字段选择技能，**后端不做 LLM / 关键词意图路由**（见 `corporate_ws.py` 顶部注释："skill chosen explicitly by the client — no LLM intent routing"）。

因此 16 个技能按传输层划分如下。

### 2.1 技能 → 传输层映射矩阵

| # | 技能 | 传输层 | 入口 | 落库表 |
|---|------|--------|------|--------|
| 1 | cold-start-interview | **REST**（service 状态机）+ 前端向导 | `POST /employment/setup` | module_configs → employment_profiles |
| 2 | hiring-review | **WS** `action=hiring` | `/ws/employment` | employment_reviews |
| 3 | termination-review | **WS** `action=termination` | `/ws/employment` | employment_reviews |
| 4 | worker-classification | **WS** `action=classification` | `/ws/employment` | employment_reviews |
| 5 | policy-drafting | **WS** `action=policy` | `/ws/employment` | employment_reviews（type=policy） |
| 6 | wage-hour-qa | **WS** `action=wage_hour` | `/ws/employment` | （问答，可选存 review） |
| 7 | handbook-updates | **WS** `action=handbook` | `/ws/employment` | employment_reviews（type=handbook） |
| 8 | expansion-kickoff | **WS** `action=expansion_analyze`（预建行后 Agent 填充） | `/ws/employment` | employment_expansions |
| 9 | expansion-update | **REST** | `PUT /employment/expansions/{id}` | employment_expansions |
| 10 | investigation-open | **REST**（创建 + 按类型 seed 来源清单，确定性） | `POST /employment/investigations` | employment_investigations + investigation_sources |
| 11 | investigation-add | **WS** `action=inv_add`（文档 needle-finding）；手动单条走 REST append | `/ws/employment` / `POST .../entries` | investigation_log_entries + investigation_gaps |
| 12 | investigation-query | **WS** `action=inv_query`（只读结构化日志） | `/ws/employment` | —（读 log/sources/gaps） |
| 13 | investigation-memo | **WS** `action=inv_memo` | `/ws/employment` | employment_investigations.memo |
| 14 | investigation-summary | **WS** `action=inv_summary` | `/ws/employment` | —（读 memo） |
| 15 | log-leave | **REST**（落库时算存具体到期日） | `POST /employment/leaves` | leave_registrations |
| 16 | leave-tracker | **cron**（纯 Python 日期算术） | scheduler job `mon 09:37` | employment_notifications |

WS `action` 合计 11 个：`hiring / termination / classification / policy / wage_hour / handbook / expansion_analyze / inv_add / inv_query / inv_memo / inv_summary`。

### 2.2 技能依赖关系

```
cold-start-interview ──写入──> employment_profiles（practice_profile / CLAUDE.md 等价物）

所有 WS Agent 技能 ──读取──> employment_profiles（前置条件；未配置则 /status 引导冷启动）
所有 WS Agent 技能 ──若未配置 LLM──> 报错 llm_not_configured（绝不兜底）

hiring-review ──提示词内路由──> 工时分类 / worker-classification 提示
termination-review ──提示词内──> 高风险标记扫描 + 加班费/补偿金计算
policy-drafting ──交接──> handbook-updates

expansion-kickoff(WS) ──预建──> employment_expansions 行；Agent 填 structure_analysis + tracking_items
expansion-update(REST) ──读写──> employment_expansions.tracking_items

investigation-open(REST) ──创建──> employment_investigations + seed investigation_sources
investigation-add(WS) ──追加──> investigation_log_entries（+ investigation_gaps）
investigation-query(WS) ──读取──> log_entries / sources / gaps（引用 entry_id）
investigation-memo(WS) ──读 log──> 写 employment_investigations.memo
investigation-summary(WS) ──读 memo──> 生成受众摘要

log-leave(REST) ──写入──> leave_registrations（含具体到期日期字段）
leave-tracker(cron) ──读取──> leave_registrations ──写入──> employment_notifications
```

### 2.3 定时代理

| 代理 | 调度 | 功能 | 是否调 LLM |
|------|------|------|-----------|
| leave-tracker | 每周一 09:37（错峰；09:07 已被 renewal_watcher 占用） | 扫描假期登记册的具体到期日期，按紧急度生成预警通知 | **否**（纯日期算术，照 dataroom_watcher） |

---

## 3. 复用 corporate 模块的架构模式

### 3.1 直接复用的公共引擎（不新建）

| 组件 | 路径 | 复用方式 |
|------|------|---------|
| 模型工厂 | `agents/model_factory.py` → `create_pydantic_model()` | 直接调用 |
| Agent 流式引擎 | `services/agent_stream.py` → `stream_agent_run()` | 直接调用 |
| WS 连接管理 | `services/agent.py` → `AgentConnectionManager` | 直接复用 |
| 调度器 | `scheduler.py`（APScheduler，已挂在 lifespan） | **只新增一个 job**，不改 lifespan |
| module_configs 表 | `db/models/module_config.py` | 直接复用，`module_name="employment-legal"` |
| 法律检索工具 | `agents/tools/law_tools.py` → `search_law / get_law_article` | 按需挂到需法条的技能 |

### 3.2 复制 corporate 模式新建的组件（**复制而非共享**）

profile / cold-start / WS / route 在 commercial 与 corporate 之间是**逐字并行的两份代码**（如 `commercial_profile_service.py` 与 `corporate_profile_service.py` 结构完全一致），不存在共享 company-profile。employment 同样新建自己的一套：

| 组件 | 镜像来源 | employment 新建 |
|------|---------|----------------|
| Agent 工厂 | `agents/corporate/agent.py` | `agents/employment/agent.py` |
| Agent Deps | `agents/corporate/deps.py` | `agents/employment/deps.py` |
| 提示词 | `agents/corporate/prompts/` | `agents/employment/prompts/` |
| 工具 | `agents/corporate/tools/` | `agents/employment/tools/` |
| WS 端点 | `api/routes/v1/corporate_ws.py` | `api/routes/v1/employment_ws.py` |
| REST 端点 | `api/routes/v1/corporate.py` | `api/routes/v1/employment.py` |
| profile service | `services/corporate_profile_service.py` | `services/employment_profile_service.py` |
| cold-start service | `services/cold_start_service.py`（commercial 版） | `services/employment_cold_start_service.py` |
| 子服务 | `services/corporate_child_services.py` | `services/employment_*_service.py` |
| 通知模型 | `db/models/corporate_notification.py` | `db/models/employment_notification.py` |
| 前端 API 客户端 | `lib/corporate.ts` | `lib/employment.ts` |
| 前端聊天 Hook | `hooks/use-corporate-chat.ts` | `hooks/use-employment-chat.ts` |
| 前端类型 | `types/corporate.ts` | `types/employment.ts` |
| 前端代理路由 | `app/api/corporate/[[...path]]/route.ts` | `app/api/employment/[[...path]]/route.ts` |

---

## 4. 数据模型设计

### 4.1 ORM 约定（强制）

所有模型用 SQLAlchemy `Mapped` 风格 + 继承 `Base, TimestampMixin`（见 `db/models/corporate_deal.py`），**不要手写 created_at/updated_at**：

```python
import uuid
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin

class EmploymentProfile(Base, TimestampMixin):
    __tablename__ = "employment_profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # ...
```

> 下文各表用字段表描述结构，**不用裸 `CREATE TABLE`**（v1 的 SQL DDL 仅曾作示意）。SQLite 下 `String(36)` 即 TEXT。

### 4.2 表清单（9 张新表 + 复用 module_configs）

#### 4.2.1 `employment_profiles`（实践画像，1:1 用户）
基本信息、管辖地（`jurisdictions` JSON、`default_jurisdiction`、`office_model`）、使用者（`user_role`、`lawyer_contact`）、审查触发器（`hiring_trigger`/`termination_trigger`/`standard_severance`/`high_risk_flags` JSON）、制度配置（`policy_location`/`provincial_supplements`）、`jurisdiction_table` JSON、`leave_management_config` JSON、`escalation_matrix` JSON、`setup_status`/`setup_progress`、`profile_content`（Markdown）。`UNIQUE(user_id)`。
**删除 v1 的 `overseas_jurisdictions`。**

#### 4.2.2 `leave_registrations`（假期登记册，N）
员工信息、`jurisdiction`、`leave_type`（annual/maternity/sick/work_injury/marriage/parental/paternity）、`leave_start`、`expected_return`、工龄字段、审批字段、`entitlement`（检索所得文本）、社保/劳动能力字段、`status`。
**新增具体到期日期字段（cron 据此纯算术判紧急度）：**
`medical_period_end DATE`、`maternity_return_date DATE`、`work_injury_period_end DATE`、`annual_carryover_deadline DATE`。

#### 4.2.3 `employment_reviews`（审查记录，N）
`review_type`（hiring/termination/worker_classification/policy/wage_hour/handbook）、员工/岗位/管辖地、输入（描述/文件）、结果（`result_status`/`result_summary`/`result_memo`/`result_json`）、`high_risk_flags` JSON、上报字段。由 WS Agent 通过 `save_review` 工具写入；REST 仅读历史。

#### 4.2.4 `employment_investigations`（调查 matter 头，N）
`investigation_name`、`allegation`、`investigation_type`（HR/financial/executive/whistleblower/other）、`scope`、`status`（open/investigating/memo_draft/closed）、`attorney_directed BOOLEAN`、`privilege_note`、`memo`（Markdown）、`opened_at`/`closed_at`。`UNIQUE(user_id, investigation_name)`。

#### 4.2.5 `investigation_log_entries`（调查日志条目，N）**【新】**
`investigation_id`(FK)、`entry_seq`(序号)、`entry_type`（interview/document/attorney-note/gap）、`date_of_event`、`source`、`source_type`、`issues` JSON、`significance`（high/medium/background）、`summary`、`quote`、`contradicts_entry_seq`、`corroborates_entry_seq`、`pull_criterion`、`privilege`。

#### 4.2.6 `investigation_sources`（来源清单，N）**【新】**
`investigation_id`(FK)、`source_seq`、`source`、`status`（open/in-progress/complete/na）、`notes`。investigation-open 按调查类型 seed（HR/financial/executive/whistleblower 模板）。

#### 4.2.7 `investigation_gaps`（证据缺口，N）**【新】**
`investigation_id`(FK)、`gap_seq`、`description`、`identified_from`、`source_to_obtain`、`priority`、`status`。

#### 4.2.8 `employment_expansions`（异地扩张追踪，N）
`slug`、`province`、`headcount`、`position_types` JSON、`employment_structure`（direct/labor_dispatch/outsourcing）、`analysis_result` JSON、`tracking_items` JSON（`[{item,owner,deadline,status,notes}]`）、`status`。`UNIQUE(user_id, slug)`。

#### 4.2.9 `employment_notifications`（通知，N）
照 `corporate_notification.py`：`notification_type`（leave_tracker/manual）、`title`、`content`（Markdown）、`priority`、`is_read`、`action_url`。

### 4.3 实体关系图

```
users (1) ── (1) employment_profiles
users (1) ── (N) leave_registrations
users (1) ── (N) employment_reviews
users (1) ── (N) employment_investigations
                      employment_investigations (1) ── (N) investigation_log_entries
                      employment_investigations (1) ── (N) investigation_sources
                      employment_investigations (1) ── (N) investigation_gaps
users (1) ── (N) employment_expansions
users (1) ── (N) employment_notifications
users (1) ── (1) module_configs [module_name="employment-legal"]
```

---

## 5. 后端开发任务

### 5.1 Phase 1：数据层（3.5 天）

#### 任务 1.1：Alembic 迁移（**幂等守护强制**）

照 corporate 拆 **3 个迁移文件**，链在当前 head（`2026-06-03_add_parsed_content_to_vdr_documents`）之后：

1. `2026-06-xx_add_employment_profile_table.py`
2. `2026-06-xx_add_employment_core_tables.py`（reviews / leaves / expansions / notifications）
3. `2026-06-xx_add_employment_investigation_tables.py`（investigations + log_entries + sources + gaps）

每个 `upgrade()` 必须用 inspector 守护（create_all + Alembic 双轨，否则 `test_migrations` 红），`downgrade()` 名称无关（drop_table 自动删索引，逆 FK 顺序）：

```python
def _ts_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    ]

def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "employment_investigations" in inspector.get_table_names():   # 锚点表守护
        return
    op.create_table("employment_investigations", ... , *_ts_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE",
                                name="fk_employment_investigations_user_id"))
    op.create_index("ix_employment_investigations_user_id", "employment_investigations", ["user_id"])
    # ... log_entries / sources / gaps（FK 指向 employment_investigations.id, CASCADE）

def downgrade() -> None:
    op.drop_table("investigation_gaps")
    op.drop_table("investigation_sources")
    op.drop_table("investigation_log_entries")
    op.drop_table("employment_investigations")
```

#### 任务 1.2：数据模型（9 文件）
`db/models/employment_profile.py`、`leave_registration.py`、`employment_review.py`、`employment_investigation.py`（含 `InvestigationLogEntry`/`InvestigationSource`/`InvestigationGap`，或拆文件）、`employment_expansion.py`、`employment_notification.py`。
在 `db/models/__init__.py` 导入并加入 `__all__`。

#### 任务 1.3：Repository 层（无状态函数，`db.flush()`+`db.refresh()`，绝不 commit）
`employment_profile_repo.py`、`leave_registration_repo.py`、`employment_review_repo.py`、`employment_investigation_repo.py`（含 log/sources/gaps 的 append + list）、`employment_expansion_repo.py`、`employment_notification_repo.py`。列表函数返回 `(items, total)`。

#### 任务 1.4：Schema 层 `schemas/employment/`
`profile.py`、`cold_start.py`、`review.py`、`investigation.py`（含 LogEntry/Source/Gap）、`expansion.py`、`leave.py`、`notification.py`。遵循 `*Create/*Update/*Read/*List` + `ConfigDict(from_attributes=True)`。

### 5.2 Phase 2：技能引擎（4.5 天）

#### 任务 2.1：Agent 工厂（镜像 `corporate/agent.py`）
`agents/employment/agent.py`：

```python
EmploymentSkillName = Literal[
    "hiring", "termination", "classification", "policy", "wage_hour",
    "handbook", "expansion_analyze", "inv_add", "inv_query", "inv_memo", "inv_summary",
]
_PROMPT_BUILDERS: dict[EmploymentSkillName, Callable[..., str]] = {...}
_SKILL_TOOLS:    dict[EmploymentSkillName, tuple[Callable, ...]] = {...}
_LAW_TOOL_SKILLS: frozenset[EmploymentSkillName] = frozenset(
    {"termination", "wage_hour", "policy", "handbook", "classification"}
)

def create_employment_agent(skill, *, practice_profile_markdown=None,
                            model_name=None, provider=None, api_key=None,
                            base_url=None, temperature=None) -> Agent[EmploymentDeps, str]:
    ...  # 同 corporate：查 builder、create_pydantic_model、挂 _SKILL_TOOLS[skill]、按需挂 law tools
```

`agents/employment/deps.py`：

```python
@dataclass
class EmploymentDeps:
    user_id: str
    db: Session
    investigation_id: str | None = None
    expansion_id: str | None = None
    review_id: str | None = None
    output_dir: str | None = None
```

#### 任务 2.2：提示词提取 `agents/employment/prompts/`
从 `~/.claude/plugins/marketplaces/claude-for-legal-zh/employment-legal/skills/*/SKILL.md` 提取，保留全部实质内容（高风险标记表、管辖地感知、调查流水线等）：

| 文件 | 来源 SKILL.md |
|------|-------------|
| `security.py` | 共享护栏（来源溯源、三值处理、上报门禁） |
| `hiring_review.py` | hiring-review |
| `termination_review.py` | termination-review（高风险标记扫描为核心，见 §7.2） |
| `worker_classification.py` | worker-classification |
| `policy_drafting.py` | policy-drafting |
| `wage_hour_qa.py` | wage-hour-qa |
| `handbook_updates.py` | handbook-updates |
| `expansion.py` | expansion-kickoff |
| `investigation.py` | internal-investigation（伞）+ 5 子技能的 5 个 mode |

> cold-start 提示词**不在此**——它是 service 状态机（任务 2.4）。

#### 任务 2.3：工具 `agents/employment/tools/`
签名一律 `async def tool(ctx: RunContext[EmploymentDeps])`，内部用 `ctx.deps.db / user_id / ...` 并做归属校验（照 `corporate/tools/deal_tools.py` 的 `_load_owned_*` 模式）。

| 文件 | 工具 |
|------|------|
| `profile_tools.py` | `read_employment_profile` |
| `review_tools.py` | `save_review_result` |
| `jurisdiction_tools.py` | `research_jurisdiction_rules`（RAG + jurisdiction_table；标注来源） |
| `policy_tools.py` | `read_current_policy`, `save_draft_policy` |
| `expansion_tools.py` | `create_expansion`, `update_expansion_analysis` |
| `investigation_tools.py` | `read_investigation_log`, `read_sources`, `read_gaps`, `append_log_entries`, `save_investigation_memo`, `read_memo` |

#### 任务 2.4：cold-start service（**非 Agent**）
`services/employment_cold_start_service.py` 复制 `cold_start_service.py` 的状态机，6 步（比 commercial 多一步管辖地）：

```
0 角色 + 实践场景    1 管辖地范围（省/直辖市多选）   2 审查触发器
3 高风险标记 + 补偿金政策   4 种子文件   5 生成画像
QUICK_PLAN=(0,1,5)  FULL_PLAN=(0,1,2,3,4,5)
```
`MODULE_NAME="employment-legal"`，终步 `_materialize_profile` 写 `employment_profiles`。

### 5.3 Phase 3：API 端点（4 天）

#### 任务 3.1：REST（`api/routes/v1/employment.py`，全部 CRUD，照 corporate.py 签名）
处理器签名 `(... , user: CurrentUser, svc: EmploymentXxxSvc) -> Any`，声明 `response_model` + 必要 `status_code`，分页 `skip/limit`：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/employment/status` | GET | 模块配置状态 |
| `/employment/setup` | POST | 冷启动步骤提交 |
| `/employment/setup/status` | GET | 冷启动进度 |
| `/employment/profile` | GET / PUT | 实践画像 |
| `/employment/reviews` | GET | 审查历史列表 |
| `/employment/reviews/{id}` | GET | 审查详情 |
| `/employment/leaves` | GET / POST | 假期列表 / 记录（POST 落具体到期日） |
| `/employment/leaves/{id}` | PUT | 更新假期 |
| `/employment/investigations` | GET / POST | 调查列表 / 开启（seed 来源清单） |
| `/employment/investigations/{id}` | GET | 调查详情（头 + log + sources + gaps） |
| `/employment/investigations/{id}/entries` | POST | 手动追加单条日志（非文档批） |
| `/employment/expansions` | GET / POST | 扩张列表 / 创建（占位行；分析走 WS） |
| `/employment/expansions/{id}` | PUT | 更新追踪项 |
| `/employment/notifications` | GET | 通知列表 |
| `/employment/notifications/{id}/read` | POST | 标记已读 |

#### 任务 3.2：WS（`api/routes/v1/employment_ws.py`，镜像 corporate_ws.py）
- `_SKILL_BY_ACTION` 显式映射 11 个 action → `create_employment_agent(skill)`
- `_require_llm_configured`：未配置 LLM → 推 `error / llm_not_configured`（**绝不兜底**）
- 归属预校验（investigation_id/expansion_id 属于该用户）
- `expansion_analyze`/`inv_*` 需先解析对应 id；`expansion_analyze` 仿 tabular 预建行并推 `expansion_started`
- 复用 `stream_agent_run`，事件名一致（见 §6.7）

#### 任务 3.3：DI / 注册 / 挂载
- `api/deps.py`：加 `get_employment_*_service` + `Annotated` 别名（`EmploymentProfileSvc` 等）
- `api/routes/v1/__init__.py`：`include_router(employment.router, prefix="/employment", tags=["employment"])` + `include_router(employment_ws.router, tags=["employment-ws"])`
- `main.py` lifespan **无需改**（scheduler 已挂）

### 5.4 Phase 4：定时代理（1.5 天）

`tasks/employment_leave_tracker.py`，照 `dataroom_watcher.py` 写 `run(db) -> int`：遍历 `iter_active_user_ids`、读 `leave_registrations` 的具体到期日期、纯算术判紧急度、写 `employment_notifications`。**不调 LLM。**

`scheduler.py` 新增：

```python
JOB_LEAVE_TRACKER = "employment_leave_tracker"
def _run_leave_tracker() -> None:
    from app.tasks import employment_leave_tracker
    _run_in_session(employment_leave_tracker.run, JOB_LEAVE_TRACKER)
# create_scheduler() 内：
scheduler.add_job(_run_leave_tracker,
    trigger=CronTrigger(day_of_week="mon", hour=9, minute=37),
    id=JOB_LEAVE_TRACKER, name="Employment leave tracker", replace_existing=True)
```

### 5.5 Phase 5：服务层（2.5 天）

`employment_profile_service.py`、`employment_cold_start_service.py`（任务 2.4 已起）、`employment_review_service.py`、`leave_service.py`（含 log-leave 落具体到期日的计算编排）、`investigation_service.py`（open/seed/append/read，含 log/sources/gaps）、`expansion_service.py`。可按 corporate 把小服务合并到 `employment_child_services.py`。

---

## 6. 前端开发任务

### 6.1 页面结构 `frontend/src/app/[locale]/(dashboard)/employment/`

```
employment/
├── page.tsx                      # 概览（未配置 → 引导冷启动）
├── setup/page.tsx                # 冷启动向导（ColdStartWizard）
├── review/
│   ├── page.tsx                  # 审查入口（类型选择 + WS 流式）
│   └── [id]/page.tsx             # 审查详情
├── leaves/page.tsx               # 假期管理（看板 + log-leave 表单）
├── investigations/
│   ├── page.tsx                  # 调查列表
│   └── [id]/page.tsx             # 调查详情（日志/来源/缺口/备忘录/摘要）
├── expansions/
│   ├── page.tsx                  # 扩张列表
│   └── [slug]/page.tsx           # 扩张详情
└── settings/page.tsx             # 实践画像设置
```

### 6.2 关键页面
- **概览（6.2.1）**：SetupStatusCard / QuickActions / StatsCards / LeaveAlertSummary / RecentReviewsList。
- **冷启动（6.2.2）**：`ColdStartWizard`（镜像 `components/commercial/cold-start-wizard.tsx`），6 步，调 `employmentApi.submitSetupStep`，服务端 materialize 后 `onComplete` 跳概览。**纯表单，非 WS。**
- **审查（6.2.3）**：选类型（录用/解除/认定/制度/工资工时/制度更新）→ 经 `use-employment-chat` 发 `{action, ...}` 走 WS 流式 → 展示结果。解除审查结果含高风险标记徽章 + 当日检查清单。
- **假期（6.2.4）**：按紧急度分组看板（🔴🟠🟡✅）、AddLeaveDialog（log-leave）、详情面板（权益/到期日/法律依据）。
- **调查（6.2.5）**：列表 + 详情（BasicInfo / EvidenceSourceList / InvestigationLog（条目）/ AddEvidenceForm / QueryPanel / MemoView / SummaryGenerator）。query/memo/summary/文档批 add 走 WS；单条 add 走 REST。
- **扩张（6.2.6）**：列表 + 详情（StructureAnalysis / TrackingBoard / UpdateForm）。kickoff 分析走 WS，update 走 REST。

### 6.3 通用组件 `frontend/src/components/employment/`
`RiskFlagBadge`、`JurisdictionSelector`、`ReviewTypeSelector`、`LeaveUrgencyBadge`、`LeaveForm`、`InvestigationLogEntry`、`InvestigationQuery`、`ExpansionTrackingItem`、`TerminationChecklist`、`SeveranceCalculator`。

### 6.4 导航注册
- `components/layout/app-sidebar.tsx`：`navigation` 数组加 `{ name: t("employment"), href: ROUTES.EMPLOYMENT, icon: Users }`
- `lib/constants.ts`：加 `EMPLOYMENT: "/employment"` 等 ROUTES
- i18n 文案加 `employment` key

### 6.5 类型 `types/employment.ts`
镜像 `types/corporate.ts`：枚举（ReviewType / LeaveType / InvestigationStatus / UserRole）、实体接口、`EmploymentWsMessage`（`{action, ...}`）、`EmploymentWsEvent` 联合类型。

### 6.6 API 客户端 `lib/employment.ts` + 代理 `app/api/employment/[[...path]]/route.ts`
`employmentApi` 对象包 `apiClient`（GET/POST/PUT/upload）；catch-all 代理转发到 `/api/v1/employment/*`，从 cookie 取 `access_token` 注入 Bearer（照 corporate 代理，支持 multipart 以便种子文件上传）。

### 6.7 聊天 Hook `hooks/use-employment-chat.ts`
镜像 `use-corporate-chat.ts`：
- WS URL `${getWsUrl()}/api/v1/ws/employment`，subprotocols `[`access_token.${token}`, "employment"]`
- 发送 `{ action, investigation_id?/expansion_id?/review_id?, prompt, ... }`
- 处理事件：`text_delta` / `tool_call` / `tool_result` / `final_result` / `complete` / `error`（+ `expansion_started` / `review_started` 等 started 事件）

---

## 7. 技能实现详解

### 7.1 技能分发（显式 action，无意图路由）

前端按用户在 UI 选择的功能直接发对应 `action`（例如点「审查解除」→ `action=termination`）。后端 `_SKILL_BY_ACTION` 校验后建 Agent。**不做关键词意图识别**——这与 corporate/commercial 一致，避免中文意图歧义与隐性兜底。

### 7.2 高风险标记系统（termination-review 核心）

解除审查最关键。提示词内定义标记检测 + 上报门禁；审查结果把触发的标记存入 `employment_reviews.high_risk_flags`；前端用红/黄/绿徽章展示。

```python
HIGH_RISK_FLAGS = [
  {"id":"recent_complaint","name":"近期投诉/举报","risk":"报复索赔","check":"近期有无投诉（HR、监管部门、热线）？"},
  {"id":"protected_leave","name":"受保护休假/医疗期","risk":"法定保护期","check":"当前是否在医疗期、工伤假、或刚休完产假？"},
  {"id":"special_protection","name":"特殊保护群体+时机","risk":"不得解除（第42条）","check":"三期女职工、工伤、医疗期、距退休不足15年？"},
  {"id":"whistleblower","name":"检举/控告","risk":"打击报复","check":"是否举报过违法、安全问题、欺诈？"},
  {"id":"weak_evidence","name":"书面证据薄弱","risk":"\"为什么现在\"","check":"有PIP、书面警告、书面反馈吗？"},
  {"id":"disparate_treatment","name":"差别对待","risk":"选择性解除","check":"他人做了同样的事但没被解除？"},
  {"id":"broken_promise","name":"合同/规章承诺","risk":"违约","check":"有书面承诺的流程但未遵循？"},
  {"id":"hours_misclassification","name":"工时制度分类错误","risk":"加班费争议","check":"综合/不定时工时是否有审批？职位是否符合？"},
]
```

**termination-review 提示词骨架**（5 步：基本事实 → 高风险标记扫描[最重要，任一触发即按 CLAUDE.md 上报后方可继续] → 管辖地要求[最终工资期限/未休年假折算/经济补偿 N 或 2N/经济性裁员第41条] → 补偿金与协商解除协议 → 书面证据），输出含「底线 / 高风险标记 / 上报 / 管辖地要求 / 补偿金 / 书面证据 / 进行不进行 / 解除当日检查清单」。完整文本从 `termination-review/SKILL.md` 提取入 `prompts/termination_review.py`。

### 7.3 管辖地感知系统

不预存规则，每次审查经 `research_jurisdiction_rules(jurisdiction, topic)`：先查 profile 的 `jurisdiction_table`（省级特殊规则 + auto_escalation），再 RAG 检索法条，标注来源。`jurisdiction_table` 示例（北京/上海的 overtime_base、final_pay_deadline、non_compete 等）随冷启动写入。

### 7.4 内部调查系统（结构化）

源 `internal-investigation` 是被 5 个子技能加载的伞框架。本期**结构化建模**以保住其能力：

- **investigation-open（REST）**：创建 `employment_investigations` 头 + 按 `investigation_type` seed `investigation_sources`（HR/financial/executive/whistleblower 各自的来源清单模板，确定性，无 LLM）；记录 `attorney_directed` 与特权提示。
- **investigation-add（WS `inv_add`）**：文档批 needle-finding——按 pull criteria 筛选，命中写 `investigation_log_entries`（带 `significance`/`contradicts`/`corroborates`/`pull_criterion`），未命中入 documents-reviewed 计数；缺口写 `investigation_gaps`。手动单条访谈记录走 REST `POST .../entries`。
- **investigation-query（WS `inv_query`，只读）**：读结构化 log/sources/gaps，按事实/冲突/覆盖/强度/Upjohn 类型回答，**引用 entry_seq**、列出 contradicts 链、对照 sources 清单查覆盖缺口。
- **investigation-memo（WS `inv_memo`）**：从 log 生成/更新 `employment_investigations.memo`（执行摘要/背景范围/方法/事实认定按 issue/可信度/结论/建议/附录）。
- **investigation-summary（WS `inv_summary`）**：从 memo 生成受众摘要（HR/管理层/外部律师），含外部回应的 consequential-action gate。

---

## 8. 定时代理实现

### 8.1 计算模型（关键修正）

法条相关的到期日**在 log-leave 交互时算好并落库为具体日期**（此刻用户已配 LLM，可经 `research_jurisdiction_rules` / law tools 依管辖地与工龄推算）：

| 假期类型 | 落库字段 | 推算依据 |
|---------|---------|---------|
| 病假/医疗期 | `medical_period_end` | 按累计工龄 3–24 月（企业职工患病医疗期规定） |
| 产假 | `maternity_return_date` | 98 天基础 + 省/直辖市奖励假 |
| 工伤假 | `work_injury_period_end` | 停工留薪期（一般≤12 月，工伤保险条例第33条） |
| 年休假 | `annual_carryover_deadline` | 年末结转截止 |
| 婚假 | （并入 expected_return） | 省/直辖市规定 |

`leave-tracker` cron **只做纯日期算术**（照 dataroom_watcher，无 LLM）：

```python
def run(db: Session) -> int:
    written = 0
    for user_id in iter_active_user_ids(db):
        leaves = leave_registration_repo.list_active(db, user_id=user_id)
        alerts = [a for lv in leaves if (a := classify_urgency(lv, today()))]  # immediate/this_week/coming_up
        if alerts:
            employment_notification_repo.create(db, user_id=user_id,
                notification_type="leave_tracker", title=..., content=format_leave_report(alerts),
                priority="high")
            written += 1
    return written
```

**预警阈值**：医疗期/工伤 到期前 30+7+3 天；产假 返岗前 30+7 天；年假 12-01 + 12-15。报告分组 🔴 立即（3 工作日）/ 🟠 本周（7 天）/ 🟡 即将（~30 天）/ ✅ 无需行动。

---

## 9. 开发排期

### 总工期：约 4–5 周（相对 v1 重平衡——技能引擎更省[去掉路由层]，investigation 结构化略增）

```
Week 1  数据层
  D1 迁移(3文件,幂等守护) + 模型(9)        D2 Repository        D3 Schema
  D4 服务层(profile, cold-start状态机)      D5 服务层(review, leave[落日期], investigation, expansion)

Week 2  技能引擎
  D1 Agent工厂+Deps + 提示词(security,hiring,termination)    D2 提示词(classification,policy,wage_hour,handbook)
  D3 提示词(investigation 5 modes + expansion)              D4 工具(profile,review,jurisdiction,policy)
  D5 工具(investigation,expansion) + 工厂联通

Week 3  API + 定时代理
  D1-2 REST(CRUD,~16端点) + DI/注册/挂载    D3 WS(11 action)    D4 leave_tracker(cron) + scheduler 注册    D5 API 集成测试

Week 4  前端
  D1 冷启动向导 + 审查页(WS)   D2 假期看板   D3 调查详情(log/sources/gaps/memo/summary)   D4 扩张 + 设置 + 导航/代理/Hook   D5 通用组件

Week 5  联调 + 测试 + 部署
  D1-2 全链路联调   D3 集成测试(tests/employment/: repo/service/scheduler)   D4-5 Bug 修复 + 部署
```

### 里程碑
| 里程碑 | 目标 | 交付物 |
|--------|------|--------|
| M1 数据层就绪 | W1 D3 | 9 表 + Repo + Schema（迁移幂等通过 test_migrations） |
| M2 冷启动可运行 | W1 D5 | cold-start 状态机贯通 |
| M3 解除审查可运行 | W2 D2 | termination WS 技能手测通过 |
| M4 全部 Agent 技能可用 | W2 D5 | 11 个 WS action 手测通过 |
| M5 API 完成 | W3 D5 | REST + WS + cron |
| M6 前端完成 | W4 D5 | 所有页面可用 |
| M7 验收通过 | W5 D5 | 全功能 + tests/employment 绿 |

---

## 10. 附录：关键文件清单

### 10.1 需读取的源文件（claude-for-legal-zh）
`~/.claude/plugins/marketplaces/claude-for-legal-zh/employment-legal/`：`CLAUDE.md`（画像模板）、`references/labor-core-rules.md`、`skills/{cold-start-interview,hiring-review,termination-review,policy-drafting,wage-hour-qa,worker-classification,expansion-kickoff,expansion-update,internal-investigation,investigation-open,investigation-add,investigation-query,investigation-memo,investigation-summary,leave-tracker,log-leave,handbook-updates}/SKILL.md`、`agents/leave-tracker.md`。

### 10.2 需新建的后端文件
```
backend/app/
├── agents/employment/
│   ├── __init__.py  agent.py  deps.py
│   ├── tools/  (profile_tools, review_tools, jurisdiction_tools, policy_tools, expansion_tools, investigation_tools)
│   └── prompts/ (security, hiring_review, termination_review, worker_classification, policy_drafting,
│                 wage_hour_qa, handbook_updates, expansion, investigation)
├── api/routes/v1/  employment.py  employment_ws.py
├── db/models/  employment_profile.py  leave_registration.py  employment_review.py
│               employment_investigation.py  employment_expansion.py  employment_notification.py
├── repositories/  employment_profile_repo.py  leave_registration_repo.py  employment_review_repo.py
│                  employment_investigation_repo.py  employment_expansion_repo.py  employment_notification_repo.py
├── schemas/employment/  __init__.py profile.py cold_start.py review.py investigation.py expansion.py leave.py notification.py
├── services/  employment_profile_service.py  employment_cold_start_service.py  employment_review_service.py
│              leave_service.py  investigation_service.py  expansion_service.py
├── tasks/  employment_leave_tracker.py
└── alembic/versions/  (3 个迁移文件，幂等守护)
更新：db/models/__init__.py  api/deps.py  api/routes/v1/__init__.py  scheduler.py
```

### 10.3 需新建的前端文件
```
frontend/src/
├── app/[locale]/(dashboard)/employment/  (page + setup + review[/id] + leaves + investigations[/id] + expansions[/slug] + settings)
├── app/api/employment/[[...path]]/route.ts
├── components/employment/  (RiskFlagBadge, JurisdictionSelector, ReviewTypeSelector, LeaveUrgencyBadge,
│                            LeaveForm, InvestigationLogEntry, InvestigationQuery, ExpansionTrackingItem,
│                            TerminationChecklist, SeveranceCalculator, ColdStartWizard)
├── hooks/use-employment-chat.ts
├── lib/employment.ts
└── types/employment.ts
更新：components/layout/app-sidebar.tsx  lib/constants.ts  i18n 文案
```

### 10.4 Required Verification（每阶段完成前）
后端：`uv run ruff check . --fix && uv run ruff format . && uv run ty check && uv run pytest`（含 `tests/employment/` 与 `test_migrations`）。
前端：`bun run lint && bun test`。

---

*文档生成时间：2026-06-03（v2.0）*
*基于 claude-for-legal-zh 劳动用工模块 + LexMind v0.7.1.0 架构*
*架构逐项镜像 corporate（公司并购）模块的真实实现*
