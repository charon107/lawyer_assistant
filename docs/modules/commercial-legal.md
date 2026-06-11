# 商事合同模块（Commercial-Legal）开发计划

**版本：** 1.0
**日期：** 2026-05-28
**目标：** 将 claude-for-legal-zh 的商事合同模块完整融入 LexMind，移除原有的文件审查（LPA review pipeline）和案件管理（Cases）功能

---

## 目录

1. [总体目标与范围](#1-总体目标与范围)
2. [要移除的功能](#2-要移除的功能)
3. [要新建的功能](#3-要新建的功能)
4. [架构设计](#4-架构设计)
5. [数据模型设计](#5-数据模型设计)
6. [后端开发任务](#6-后端开发任务)
7. [前端开发任务](#7-前端开发任务)
8. [技能实现详解](#8-技能实现详解)
9. [定时代理实现](#9-定时代理实现)
10. [开发排期](#10-开发排期)
11. [附录：关键文件清单](#11-附录关键文件清单)

---

## 1. 总体目标与范围

### 1.1 目标

将 claude-for-legal-zh 商事合同模块的 **9 个技能 + 3 个定时代理** 完整移植到 LexMind，实现：

- 用户访问「商事合同」模块时，若未配置则引导冷启动访谈
- 配置完成后，用户可通过前端界面使用全部 9 个技能
- 3 个定时代理在后台自动运行，产生通知
- 后端 Agent/Prompt/工具调用完全遵循 claude-for-legal-zh 的 SKILL.md 定义
- 前端提供用户友好的交互界面

### 1.2 范围

**包含：**
- 9 个技能：cold-start-interview, vendor-agreement-review, nda-review, saas-msa-review, renewal-tracker, escalation-flagger, stakeholder-summary, amendment-history, matter-workspace
- 3 个定时代理：renewal-watcher, deal-debrief, playbook-monitor
- 商事合同专属前端页面
- 配置存储、续约登记册、偏差日志等数据持久化

**不包含：**
- 其他 9 个法律模块（后续独立开发）
- MCP 外部集成（e签宝、法大大、飞书等 — 后续接入）
- 元典 MCP 检索（后续接入，当前用 RAG 替代）

---

## 2. 要移除的功能

### 2.1 后端移除清单

| 文件/目录 | 说明 | 操作 |
|-----------|------|------|
| `backend/app/api/routes/v1/lpa.py` | LPA 审查 REST 端点 | 删除 |
| `backend/app/api/routes/v1/lpa_ws.py` | LPA 审查 WebSocket 进度 | 删除 |
| `backend/app/api/routes/v1/lpa_cases.py` | 案件 CRUD + 文档管理 | 删除 |
| `backend/app/services/lpa_service.py` | LPA 审查业务逻辑 | 删除 |
| `backend/app/services/review_pipeline.py` | 6 阶段审查流水线 | 删除 |
| `backend/app/services/review_*.py` | 各审查阶段实现 | 删除 |
| `backend/app/db/models/lpa_case.py` | Case 数据模型 | 删除 |
| `backend/app/db/models/document_analysis.py` | DocumentAnalysis 模型 | 删除 |
| `backend/app/repositories/case_repo.py` | 案件数据访问层 | 删除 |
| `backend/app/agents/rules/` | 14 种文档类型的风险规则 | 删除 |
| `backend/app/agents/review_agent.py` | 审查 Agent | 删除 |
| `backend/app/schemas/lpa.py` | LPA 相关 Schema | 删除 |
| `backend/app/schemas/case.py` | 案件相关 Schema | 删除 |

### 2.2 前端移除清单

| 文件/目录 | 说明 | 操作 |
|-----------|------|------|
| `frontend/src/app/[locale]/(dashboard)/review/` | 审查页面 | 删除 |
| `frontend/src/app/[locale]/(dashboard)/cases/` | 案件管理页面 | 删除 |
| `frontend/src/components/review/` | 审查相关组件 | 删除 |
| `frontend/src/components/cases/` | 案件相关组件 | 删除 |
| `frontend/src/lib/api/review.ts` | 审查 API 客户端 | 删除 |
| `frontend/src/lib/api/cases.ts` | 案件 API 客户端 | 删除 |
| `frontend/src/stores/review-store.ts` | 审查状态管理 | 删除 |
| `frontend/src/stores/case-store.ts` | 案件状态管理 | 删除 |

### 2.3 导航菜单更新

- 移除侧边栏中的「合同审查」和「案件管理」入口
- 新增「商事合同」模块入口

### 2.4 数据库迁移

```sql
-- 删除不再需要的表
DROP TABLE IF EXISTS document_analyses;
DROP TABLE IF EXISTS lpa_cases;
-- 注意：保留 users, conversations, messages, chat_files 等核心表
```

---

## 3. 要新建的功能

### 3.1 功能总览

```
商事合同模块
├── 配置管理
│   ├── 冷启动访谈（引导式配置）
│   ├── 实践画像存储（CLAUDE.md 等价物）
│   └── 配置状态检测
├── 合同审查（核心）
│   ├── 文件上传 + 类型自动检测
│   ├── 供应商协议审查（vendor-agreement-review）
│   ├── NDA 快速分流（nda-review）
│   ├── SaaS 协议审查（saas-msa-review）
│   └── 审查报告展示
├── 续约管理
│   ├── 续约登记册（renewal-tracker）
│   ├── 续约日历看板
│   └── 续约预警通知
├── 辅助工具
│   ├── 上报路由（escalation-flagger）
│   ├── 业务摘要（stakeholder-summary）
│   └── 修订历史（amendment-history）
├── 事项管理
│   └── 事项工作区（matter-workspace）
└── 后台代理
    ├── 续约监控（renewal-watcher）
    ├── 偏差收集（deal-debrief）
    └── 手册监控（playbook-monitor）
```

---

## 4. 架构设计

### 4.1 整体架构变更

```
┌─────────────────────────────────────────────────┐
│                   Frontend                        │
│         Next.js 15 + React 19 + Tailwind v4       │
├─────────────┬───────────────────────────────────┤
│   Nginx     │          Backend                   │
│  (反向代理)  │    FastAPI + Pydantic v2           │
│             │    SQLite + SQLAlchemy ORM          │
│             │    Alembic 迁移                     │
├─────────────┴───────────────────────────────────┤
│              服务层                               │
│  ┌──────────────────────────────────────────┐   │
│  │  商事合同 Agent（PydanticAI）              │   │
│  │  ├── 技能路由（根据用户意图分发）          │   │
│  │  ├── 工具集（search_law, get_law_article, │   │
│  │  │         get_domain_expertise, +新增）   │   │
│  │  └── 系统提示词（动态加载技能指导）       │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │  配置服务（ConfigService）                 │   │
│  │  ├── 实践画像 CRUD                        │   │
│  │  ├── 续约登记册 CRUD                      │   │
│  │  ├── 偏差日志 CRUD                        │   │
│  │  └── 事项工作区 CRUD                      │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │  定时任务调度器（APScheduler）              │   │
│  │  ├── renewal-watcher（每周一）             │   │
│  │  ├── deal-debrief（每周一）                │   │
│  │  └── playbook-monitor（数据触发）          │   │
│  └──────────────────────────────────────────┘   │
├─────────────────────────────────────────────────┤
│              基础设施层                            │
│  Qdrant (向量数据库)  │  Redis (缓存)             │
│  Sentence Transformers │  PydanticAI              │
└─────────────────────────────────────────────────┘
```

### 4.2 Agent 架构

**核心变更：** 从现有的「单 Agent + 多工具」模式改为「商事合同专用 Agent + 技能路由」模式。

```python
# 商事合同 Agent 系统提示词结构
system_prompt = f"""
{practice_profile}           # 从 CLAUDE.md 等价物加载
{contract_law_reference}     # 从 contract-law-core.md 加载
{skill_guidance}             # 根据用户意图动态加载对应技能的 SKILL.md 内容
{security_mechanisms}        # 共享安全机制（来源溯源、三值选择等）
"""
```

**技能路由逻辑：**

```
用户输入 → 意图识别 → 路由到对应技能 → 加载技能指导 → 执行
```

| 用户意图关键词 | 路由到的技能 |
|---------------|-------------|
| "审查合同", "帮我看看", "review" | vendor-agreement-review（自动检测类型） |
| "NDA", "保密协议", "分流" | nda-review |
| "SaaS", "订阅", "云服务" | saas-msa-review |
| "续约", "到期", "取消窗口" | renewal-tracker |
| "谁批准", "上报", "审批" | escalation-flagger |
| "给业务总结", "摘要", "非法律版" | stakeholder-summary |
| "改了什么", "修订历史", "变更" | amendment-history |
| "新建事项", "切换事项", "事项" | matter-workspace |
| "配置", "设置", "引导" | cold-start-interview |

### 4.3 工具集设计

在现有 3 个工具基础上新增：

| 工具 | 用途 | 状态 |
|------|------|------|
| `search_law` | 向量语义搜索法律条文 | 已有，保留 |
| `get_law_article` | 精确获取指定条文 | 已有，保留 |
| `get_domain_expertise` | 加载领域律师思维方法论 | 已有，保留 |
| `upload_contract` | 上传合同文件（PDF/DOCX/图片） | **新增** |
| `read_practice_profile` | 读取实践画像配置 | **新增** |
| `write_practice_profile` | 写入/更新实践画像 | **新增** |
| `read_renewal_register` | 读取续约登记册 | **新增** |
| `write_renewal_register` | 写入续约登记册条目 | **新增** |
| `read_deviation_log` | 读取偏差日志 | **新增** |
| `write_deviation_log` | 写入偏差日志 | **新增** |
| `read_matter_context` | 读取当前事项上下文 | **新增** |
| `write_matter` | 创建/更新事项 | **新增** |
| `get_playbook` | 读取合同手册（标准/底线/绝不接受） | **新增** |

---

## 5. 数据模型设计

### 5.1 新增数据表

#### 5.1.1 实践画像表（commercial_profiles）

```sql
CREATE TABLE commercial_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    -- 基本信息
    company_name TEXT,
    entity_type TEXT,                    -- 企业类型
    team_size TEXT,
    gc_name TEXT,                        -- 法务负责人
    monthly_volume TEXT,                 -- 月均合同量
    side TEXT DEFAULT 'purchasing',      -- sales / purchasing / both
    -- 配置状态
    setup_status TEXT DEFAULT 'not_started',  -- not_started / in_progress / completed
    setup_progress TEXT,                 -- JSON: 各步骤完成状态
    -- 完整画像内容（Markdown 格式，与 CLAUDE.md 等价）
    profile_content TEXT,                -- 完整的实践画像 Markdown
    -- 合同手册（结构化存储，便于查询）
    playbook_sales TEXT,                 -- JSON: 销售方手册
    playbook_purchasing TEXT,            -- JSON: 采购方手册
    -- 上报矩阵
    escalation_matrix TEXT,              -- JSON: 审批上报矩阵
    -- 设置
    renewal_alert_channel TEXT,          -- 续约预警渠道
    output_destination TEXT,             -- 输出目标
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);
```

#### 5.1.2 续约登记册表（renewal_registrations）

```sql
CREATE TABLE renewal_registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    matter_id INTEGER REFERENCES commercial_matters(id),
    -- 合同信息
    counterparty TEXT NOT NULL,          -- 对方名称
    agreement_type TEXT,                 -- 协议类型
    agreement_name TEXT,                 -- 协议名称
    signed_date DATE,
    -- 续约信息
    initial_term_end DATE,
    current_term_end DATE,
    renewal_mechanism TEXT,              -- 自动续约 / 手动续约
    notice_period_days INTEGER,
    notice_method TEXT,
    transit_buffer_days INTEGER DEFAULT 0,
    -- 计算字段
    cancel_by_calendar DATE,
    cancel_by_effective DATE,
    send_by_effective DATE,
    -- 价格信息
    price_on_renewal TEXT,               -- 续约价格机制
    annual_value REAL,
    currency TEXT DEFAULT 'CNY',
    -- 业务信息
    business_owner TEXT,
    clm_id TEXT,
    status TEXT DEFAULT 'active',        -- active / renewed / cancelled / expired
    notes TEXT,
    -- 来源
    source TEXT DEFAULT 'manual',        -- manual / review_handoff / clm_scan
    source_review_id INTEGER,
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5.1.3 事项工作区表（commercial_matters）

```sql
CREATE TABLE commercial_matters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    slug TEXT NOT NULL,                  -- URL-safe 标识符
    -- 基本信息
    client TEXT,
    counterparty TEXT,
    matter_type TEXT,
    confidentiality_level TEXT DEFAULT 'confidential',
    -- 状态
    status TEXT DEFAULT 'active',        -- active / closed / archived
    -- 关键事实
    key_facts TEXT,                      -- JSON
    -- 配置覆盖（事项级别的手册覆盖）
    playbook_overrides TEXT,             -- JSON
    -- 历史记录
    history TEXT,                        -- Markdown 格式的事件日志
    notes TEXT,                          -- 自由格式工作笔记
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    UNIQUE(user_id, slug)
);
```

#### 5.1.4 合同审查记录表（contract_reviews）

```sql
CREATE TABLE contract_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    matter_id INTEGER REFERENCES commercial_matters(id),
    -- 审查信息
    review_type TEXT NOT NULL,           -- vendor / nda / saas
    counterparty TEXT,
    agreement_name TEXT,
    agreement_type TEXT,
    side TEXT DEFAULT 'purchasing',
    annual_value REAL,
    -- 文件信息
    file_path TEXT,
    file_name TEXT,
    -- 审查结果
    result_status TEXT,                  -- green / yellow / red / in_progress
    result_summary TEXT,                 -- 底线摘要（2句话）
    result_memo TEXT,                    -- 完整审查备忘录（Markdown）
    result_json TEXT,                    -- 结构化审查结果（JSON）
    -- 业务摘要
    stakeholder_summary TEXT,            -- 200字业务摘要
    -- 上报信息
    required_approver TEXT,
    escalation_sent BOOLEAN DEFAULT FALSE,
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5.1.5 偏差日志表（contract_deviations）

```sql
CREATE TABLE contract_deviations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    review_id INTEGER REFERENCES contract_reviews(id),
    -- 合同信息
    deal_id TEXT,
    counterparty TEXT,
    agreement_type TEXT,
    date_signed DATE,
    -- 偏差信息
    clause_name TEXT,
    standard_position TEXT,              -- 手册标准立场
    signed_position TEXT,                -- 实际签署立场
    severity TEXT,                       -- critical / high / medium / low
    basis TEXT,                          -- 偏差原因
    context TEXT,                        -- 补充说明
    -- 排除标记
    exclude_from_patterns BOOLEAN DEFAULT FALSE,
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5.1.6 手册更新提案表（playbook_proposals）

```sql
CREATE TABLE playbook_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    -- 提案信息
    clause_key TEXT NOT NULL,
    current_language TEXT,               -- 当前手册语言
    proposed_language TEXT,              -- 提议的新语言
    pattern_count INTEGER,               -- 偏差次数
    lookback_months INTEGER DEFAULT 12,
    -- 支撑数据
    supporting_data TEXT,                -- JSON: 各次偏差详情
    recommendation TEXT,                 -- revise / clarify / discuss
    -- 状态
    status TEXT DEFAULT 'pending',       -- pending / accepted / rejected / deferred
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5.1.7 模块配置状态表（module_configs）

```sql
CREATE TABLE module_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    module_name TEXT NOT NULL,           -- 'commercial-legal'
    setup_status TEXT DEFAULT 'not_started',
    setup_data TEXT,                     -- JSON: 冷启动访谈中间状态
    config_content TEXT,                 -- 完整配置内容
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, module_name)
);
```

### 5.2 实体关系图

```
users (1) ──── (N) commercial_matters
users (1) ──── (1) commercial_profiles
users (1) ──── (N) renewal_registrations
users (1) ──── (N) contract_reviews
users (1) ──── (N) contract_deviations
users (1) ──── (N) playbook_proposals
users (1) ──── (1) module_configs

commercial_matters (1) ──── (N) contract_reviews
contract_reviews (1) ──── (N) contract_deviations
```

---

## 6. 后端开发任务

### 6.1 Phase 1：基础架构（5 天）

#### 任务 1.1：数据库迁移

- 创建 Alembic 迁移脚本，新增上述 7 张表
- 删除 `document_analyses` 和 `lpa_cases` 表
- 文件：`backend/alembic/versions/xxxx_add_commercial_legal_tables.py`

#### 任务 1.2：移除旧代码

- 删除 `backend/app/api/routes/v1/lpa.py`, `lpa_ws.py`, `lpa_cases.py`
- 删除 `backend/app/services/lpa_service.py`, `review_pipeline.py`, `review_*.py`
- 删除 `backend/app/db/models/lpa_case.py`, `document_analysis.py`
- 删除 `backend/app/repositories/case_repo.py`
- 删除 `backend/app/agents/rules/` 目录
- 删除 `backend/app/agents/review_agent.py`
- 删除 `backend/app/schemas/lpa.py`, `case.py`
- 更新 `backend/app/api/routes/v1/__init__.py` 移除旧路由
- 更新 `backend/app/db/models/__init__.py` 移除旧模型

#### 任务 1.3：数据访问层（Repository）

新建文件：

| 文件 | 功能 |
|------|------|
| `backend/app/repositories/commercial_profile_repo.py` | 实践画像 CRUD |
| `backend/app/repositories/renewal_registration_repo.py` | 续约登记册 CRUD |
| `backend/app/repositories/commercial_matter_repo.py` | 事项工作区 CRUD |
| `backend/app/repositories/contract_review_repo.py` | 审查记录 CRUD |
| `backend/app/repositories/contract_deviation_repo.py` | 偏差日志 CRUD |
| `backend/app/repositories/playbook_proposal_repo.py` | 手册提案 CRUD |
| `backend/app/repositories/module_config_repo.py` | 模块配置 CRUD |

#### 任务 1.4：Pydantic Schema

新建文件：

| 文件 | 内容 |
|------|------|
| `backend/app/schemas/commercial.py` | 商事合同模块全部请求/响应 Schema |

关键 Schema：

```python
# 实践画像
class CommercialProfile(BaseModel):
    company_name: str
    entity_type: str
    side: Literal['sales', 'purchasing', 'both']
    setup_status: Literal['not_started', 'in_progress', 'completed']
    profile_content: str  # Markdown
    playbook_sales: dict | None
    playbook_purchasing: dict | None
    escalation_matrix: list[EscalationRule] | None

# 冷启动访谈
class ColdStartResponse(BaseModel):
    step: int                    # 当前步骤 (0-4)
    answers: dict                # 用户回答
    seed_files: list[str]        # 上传的种子文件路径

# 合同审查请求
class ContractReviewRequest(BaseModel):
    file_path: str
    review_type: Literal['vendor', 'nda', 'saas', 'auto'] = 'auto'
    side: Literal['sales', 'purchasing'] | None = None
    annual_value: float | None = None
    matter_id: int | None = None

# 合同审查结果
class ContractReviewResult(BaseModel):
    id: int
    review_type: str
    result_status: Literal['green', 'yellow', 'red']
    result_summary: str
    result_memo: str             # 完整备忘录 Markdown
    deviations: list[DeviationItem]
    favorable_terms: list[str]
    missing_terms: list[str]
    required_approver: str | None

# NDA 分流结果
class NdaReviewResult(BaseModel):
    classification: Literal['green', 'yellow', 'red']
    checklist: list[CheckItem]           # green: 各项通过/未通过
    flagged_items: list[FlaggedItem]     # yellow: 标记项
    key_problems: list[KeyProblem]       # red: 关键问题

# 续约条目
class RenewalRegistration(BaseModel):
    counterparty: str
    agreement_name: str
    current_term_end: date
    cancel_by_calendar: date | None
    cancel_by_effective: date | None
    annual_value: float | None
    business_owner: str | None
    status: Literal['active', 'renewed', 'cancelled', 'expired']

# 上报路由结果
class EscalationResult(BaseModel):
    approver: str
    channel: str                 # feishu / email / meeting
    urgency: str
    message_draft: str           # 草拟的上报消息

# 业务摘要
class StakeholderSummary(BaseModel):
    audience: Literal['procurement', 'dept_head', 'finance', 'security', 'exec']
    summary: str                 # 200字以内
    checklist: list[str]
    approval_timeline: str
```

### 6.2 Phase 2：技能引擎（7 天）

#### 任务 2.1：技能注册系统

新建 `backend/app/agents/commercial/skills.py`：

```python
"""
商事合同技能注册系统。
每个技能对应 claude-for-legal-zh 中的一个 SKILL.md。
技能的本质是一段系统提示词 + 执行逻辑。
"""

@dataclass
class CommercialSkill:
    name: str
    description: str
    trigger_keywords: list[str]
    requires_config: bool        # 是否需要先完成冷启动
    system_prompt: str           # 从 SKILL.md 提取的核心指导
    tools: list[str]             # 该技能可用的工具列表
    output_schema: str           # 输出格式描述

# 9 个技能实例
COLD_START = CommercialSkill(
    name="cold-start-interview",
    description="冷启动访谈 — 学习你的合同团队如何工作",
    trigger_keywords=["配置", "设置", "引导", "开始"],
    requires_config=False,
    system_prompt="""...""",     # 从 SKILL.md 提取
    tools=["upload_contract", "write_practice_profile"],
    output_schema="practice_profile"
)

VENDOR_REVIEW = CommercialSkill(
    name="vendor-agreement-review",
    description="供应商协议审查 — 逐条对比合同手册",
    trigger_keywords=["审查", "review", "看看", "合同"],
    requires_config=True,
    system_prompt="""...""",
    tools=["upload_contract", "read_practice_profile", "get_playbook",
           "search_law", "get_law_article", "write_renewal_register"],
    output_schema="contract_review_memo"
)

# ... 其余 7 个技能类似
```

#### 任务 2.2：技能提示词提取

从 claude-for-legal-zh 的每个 SKILL.md 文件中提取核心提示词，转换为 Python 字符串常量。

文件：`backend/app/agents/commercial/prompts/`

| 文件 | 内容来源 |
|------|---------|
| `cold_start.py` | cold-start-interview/SKILL.md |
| `vendor_review.py` | vendor-agreement-review/SKILL.md |
| `nda_review.py` | nda-review/SKILL.md |
| `saas_review.py` | saas-msa-review/SKILL.md |
| `renewal_tracker.py` | renewal-tracker/SKILL.md |
| `escalation.py` | escalation-flagger/SKILL.md |
| `stakeholder.py` | stakeholder-summary/SKILL.md |
| `amendment.py` | amendment-history/SKILL.md |
| `matter.py` | matter-workspace/SKILL.md |

每个提示词文件的结构：

```python
VENDOR_REVIEW_SYSTEM_PROMPT = """
你是一位资深商事合同律师，正在审查一份供应商协议。

## 你的工作流程

### Step 1: 定位
快速阅读全文，识别：
- 协议类型（MSA/SOW/订购单等）
- 我方角色（采购方/供应方）
- 对方身份
- 合同金额
- 期限
- 是否附有 DPA
- 是否有订单表

### Step 2: 绝对红线检查
首先检查手册中的"绝不接受"条款。如果命中，立即标记 ⛔ 并停止。

### Step 3: 逐条对比
对于手册中的每个审查类别：
1. 找到合同中对应条款
2. 与手册立场对比
3. 生成偏差分析块：
   - 手册立场 vs 合同原文（精确引用）
   - 偏差分类：缺失 | 弱于标准 | 弱于底线 | 非标准 | 不可接受
   - 法律风险：🔴/🟠/🟡/🟢
   - 商业摩擦：🔴/🟠/🟡/🟢
   - 为什么重要（1-2句白话）
   - 建议修改文字（可直接粘贴）
   - 如果对方不让步：底线方案或上报给 [姓名]

...（完整提示词从 SKILL.md 提取）
"""

SECURITY_MECHANISMS = """
## 共享安全机制

### 来源溯源标签
所有引用必须标注来源：
- [法条原文] — 本会话中从官方来源直接获取
- [本地知识库] — 从 Qdrant RAG 检索
- [用户提供] — 用户粘贴/链接
- [模型知识 — 需验证] — 其他一切（默认）

### 不静默填充
当检索返回少量结果时，报告并停止，不要用模型知识静默填充。

### 双轴严重程度
- 法律风险：🔴 阻断 | 🟠 高 | 🟡 中 | 🟢 低
- 商业摩擦：🔴 阻断交易 | 🟠 拖慢交易 | 🟡 惹恼客户 | 🟢 无感
"""
```

#### 任务 2.3：工具实现

新建 `backend/app/agents/commercial/tools.py`：

每个工具实现为一个 Python 函数，供 PydanticAI Agent 调用：

```python
from pydantic_ai import Tool

async def upload_contract(file_path: str) -> str:
    """上传合同文件，提取文本内容"""
    # 解析 PDF/DOCX/图片 OCR → 纯文本
    pass

async def read_practice_profile(user_id: int) -> str:
    """读取用户的实践画像配置"""
    pass

async def write_practice_profile(user_id: int, content: str) -> str:
    """写入实践画像"""
    pass

async def get_playbook(user_id: int, side: str) -> dict:
    """读取合同手册（标准/底线/绝不接受）"""
    pass

async def read_renewal_register(user_id: int) -> list[dict]:
    """读取续约登记册"""
    pass

async def write_renewal_register(user_id: int, entry: dict) -> str:
    """向续约登记册添加条目"""
    pass

async def read_deviation_log(user_id: int) -> list[dict]:
    """读取偏差日志"""
    pass

async def write_deviation_log(user_id: int, entry: dict) -> str:
    """写入偏差日志"""
    pass

async def read_matter_context(user_id: int) -> dict | None:
    """读取当前活跃事项上下文"""
    pass

async def write_matter(user_id: int, action: str, **kwargs) -> str:
    """事项工作区操作：new/list/switch/close/none"""
    pass
```

#### 任务 2.4：Agent 初始化

新建 `backend/app/agents/commercial/agent.py`：

```python
from pydantic_ai import Agent

def create_commercial_agent(
    user_id: int,
    skill: CommercialSkill,
    profile: CommercialProfile,
    llm_config: UserLLMConfig,
) -> Agent:
    """创建商事合同专用 Agent"""

    # 动态构建系统提示词
    system_prompt = build_system_prompt(
        practice_profile=profile.profile_content,
        contract_law_reference=load_contract_law_reference(),
        skill_guidance=skill.system_prompt,
        security_mechanisms=SECURITY_MECHANISMS,
    )

    # 注册该技能可用的工具
    tools = get_tools_for_skill(skill, user_id)

    # 创建 Agent
    agent = Agent(
        model=llm_config.to_model(),
        system_prompt=system_prompt,
        tools=tools,
        retries=2,
    )

    return agent
```

### 6.3 Phase 3：API 端点（5 天）

#### 任务 3.1：REST API

新建 `backend/app/api/routes/v1/commercial.py`：

| 端点 | 方法 | 功能 | 对应技能 |
|------|------|------|---------|
| `/api/v1/commercial/status` | GET | 获取模块配置状态 | — |
| `/api/v1/commercial/setup` | POST | 冷启动访谈（多步） | cold-start-interview |
| `/api/v1/commercial/setup/status` | GET | 冷启动进度 | cold-start-interview |
| `/api/v1/commercial/review` | POST | 合同审查（上传+审查） | vendor/nda/saas |
| `/api/v1/commercial/reviews` | GET | 审查历史列表 | — |
| `/api/v1/commercial/reviews/{id}` | GET | 单个审查详情 | — |
| `/api/v1/commercial/reviews/{id}/summary` | POST | 生成业务摘要 | stakeholder-summary |
| `/api/v1/commercial/renewals` | GET | 续约列表 | renewal-tracker |
| `/api/v1/commercial/renewals` | POST | 添加续约条目 | renewal-tracker |
| `/api/v1/commercial/renewals/{id}` | PUT | 更新续约条目 | renewal-tracker |
| `/api/v1/commercial/escalation` | POST | 上报路由 | escalation-flagger |
| `/api/v1/commercial/amendments` | POST | 修订历史分析 | amendment-history |
| `/api/v1/commercial/matters` | GET | 事项列表 | matter-workspace |
| `/api/v1/commercial/matters` | POST | 新建事项 | matter-workspace |
| `/api/v1/commercial/matters/{id}/switch` | POST | 切换事项 | matter-workspace |
| `/api/v1/commercial/matters/{id}/close` | POST | 关闭事项 | matter-workspace |
| `/api/v1/commercial/profile` | GET | 获取实践画像 | — |
| `/api/v1/commercial/profile` | PUT | 更新实践画像 | — |

#### 任务 3.2：WebSocket 端点

新建 `backend/app/api/routes/v1/commercial_ws.py`：

```python
@router.websocket("/api/v1/commercial/chat")
async def commercial_chat_ws(
    websocket: WebSocket,
    # 认证通过 Sec-WebSocket-Protocol header
):
    """
    商事合同对话 WebSocket。
    前端发送: { "message": "...", "skill": "auto|vendor|nda|saas|...", "matter_id": null }
    后端推送: { "type": "token|tool_call|result|error", "data": "..." }
    """
    # 1. 认证
    # 2. 读取用户配置
    # 3. 检测技能（auto 或指定）
    # 4. 创建 Agent
    # 5. 流式执行
    # 6. 保存结果到数据库
```

#### 任务 3.3：冷启动访谈 API 详解

冷启动访谈是多步骤交互，需要特殊的 API 设计：

```python
@router.post("/api/v1/commercial/setup")
async def cold_start_setup(
    request: ColdStartRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    冷启动访谈，支持多步骤。

    请求体:
    {
        "step": 0,                    # 当前步骤 (0=开始, 1=团队, 2=手册, 3=上报, 4=种子文件)
        "answers": { ... },           # 当前步骤的回答
        "seed_files": ["path1.pdf"],  # 上传的种子文件（步骤4）
        "quick_mode": false           # 快速模式（2分钟）vs 完整模式（15分钟）
    }

    响应:
    {
        "step": 1,
        "next_questions": [...],      # 下一步的问题
        "progress": 0.2,              # 进度百分比
        "partial_config": { ... }     # 已收集的部分配置
    }
    """
```

### 6.4 Phase 4：定时任务（3 天）

#### 任务 4.1：任务调度器

新建 `backend/app/tasks/scheduler.py`：

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

def setup_commercial_tasks():
    """注册商事合同定时代理"""

    # renewal-watcher: 每周一上午 9:00
    scheduler.add_job(
        renewal_watcher_job,
        'cron',
        day_of_week='mon',
        hour=9,
        minute=0,
        id='commercial_renewal_watcher',
    )

    # deal-debrief: 每周一上午 10:00
    scheduler.add_job(
        deal_debrief_job,
        'cron',
        day_of_week='mon',
        hour=10,
        minute=0,
        id='commercial_deal_debrief',
    )
```

#### 任务 4.2：renewal-watcher 实现

```python
async def renewal_watcher_job():
    """
    每周一运行。
    1. 读取所有用户的续约登记册
    2. 计算未来 90 天内的续约
    3. 按紧急程度分组
    4. 生成报告
    5. 存入通知表
    """
    users = get_all_commercial_users()
    for user in users:
        register = await read_renewal_register(user.id)
        upcoming = calculate_upcoming(register, days=90)
        report = format_renewal_report(upcoming)
        await create_notification(user.id, "renewal_watcher", report)
```

#### 任务 4.3：deal-debrief 实现

```python
async def deal_debrief_job():
    """
    每周一运行。
    1. 扫描上周的合同审查记录
    2. 对比手册立场
    3. 提取偏差
    4. 写入偏差日志
    """
    users = get_all_commercial_users()
    for user in users:
        reviews = get_reviews_last_7_days(user.id)
        profile = get_profile(user.id)
        for review in reviews:
            deviations = extract_deviations(review, profile)
            if deviations:
                await write_deviation_log(user.id, deviations)
```

#### 任务 4.4：playbook-monitor 实现

```python
async def playbook_monitor_check(user_id: int):
    """
    数据触发（在 deal-debrief 写入偏差后调用）。
    1. 读取偏差日志
    2. 统计各条款偏差次数（12个月滚动窗口）
    3. 如果某条款偏差 >= 5 次，生成更新提案
    """
    deviations = await read_deviation_log(user_id)
    patterns = analyze_patterns(deviations, lookback_months=12)
    for clause_key, count in patterns.items():
        if count >= 5:
            proposal = generate_proposal(clause_key, deviations)
            await save_proposal(user_id, proposal)
            await notify_user(user_id, f"手册监控：{clause_key} 有 {count} 次偏差，已生成更新提案")
```

### 6.5 Phase 5：文件处理（3 天）

#### 任务 5.1：合同文件解析

新建 `backend/app/services/contract_parser.py`：

```python
async def parse_contract(file_path: str) -> str:
    """
    解析合同文件为纯文本。
    支持：PDF, DOCX, TXT, 图片（OCR）
    """
    ext = Path(file_path).suffix.lower()

    if ext == '.pdf':
        return await parse_pdf(file_path)
    elif ext in ('.docx', '.doc'):
        return await parse_docx(file_path)
    elif ext == '.txt':
        return Path(file_path).read_text(encoding='utf-8')
    elif ext in ('.png', '.jpg', '.jpeg'):
        return await ocr_image(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")
```

#### 任务 5.2：合同类型自动检测

```python
async def detect_contract_type(text: str) -> str:
    """
    自动检测合同类型。
    返回: 'nda' | 'saas' | 'vendor'
    """
    # 基于关键词和结构特征判断
    nda_keywords = ['保密协议', '保密义务', '机密信息', 'NDA', 'Non-Disclosure']
    saas_keywords = ['SaaS', '订阅', '云服务', '软件即服务', 'SLA', 'uptime']

    nda_score = sum(1 for kw in nda_keywords if kw in text)
    saas_score = sum(1 for kw in saas_keywords if kw in text)

    if nda_score >= 2:
        return 'nda'
    elif saas_score >= 2:
        return 'saas'
    else:
        return 'vendor'
```

---

## 7. 前端开发任务

### 7.1 页面结构

```
frontend/src/app/[locale]/(dashboard)/commercial/
├── page.tsx                          # 商事合同首页（模块概览）
├── setup/
│   └── page.tsx                      # 冷启动访谈页面
├── review/
│   ├── page.tsx                      # 合同审查（上传 + 结果）
│   └── [id]/
│       └── page.tsx                  # 审查详情
├── renewals/
│   └── page.tsx                      # 续约管理
├── matters/
│   ├── page.tsx                      # 事项列表
│   └── [slug]/
│       └── page.tsx                  # 事项详情
├── tools/
│   ├── escalation/
│   │   └── page.tsx                  # 上报路由
│   ├── summary/
│   │   └── page.tsx                  # 业务摘要
│   └── amendments/
│       └── page.tsx                  # 修订历史
└── settings/
    └── page.tsx                      # 实践画像设置
```

### 7.2 核心页面设计

#### 7.2.1 商事合同首页（/commercial）

**功能：**
- 模块配置状态检测（未配置 → 引导冷启动）
- 快速操作入口（审查合同、查看续约、新建事项）
- 统计概览（本月审查数、即将到期续约、活跃事项）
- 最近审查记录

**组件：**
```
CommercialOverview
├── SetupStatusCard          # 配置状态卡片（未配置时显示引导）
├── QuickActions             # 快速操作按钮组
├── StatsCards               # 统计卡片（审查数/续约/事项）
└── RecentReviewsList        # 最近审查列表
```

#### 7.2.2 冷启动访谈（/commercial/setup）

**功能：**
- 分步引导式访谈（5 步）
- 支持快速模式（2 分钟）和完整模式（15 分钟）
- 种子文件上传（5-10 份已签协议）
- 实时预览生成的配置
- 可中断续接

**组件：**
```
ColdStartWizard
├── StepIndicator            # 步骤指示器
├── Step0WhoUses             # 谁使用（律师/非律师）
├── Step1TeamInfo            # 团队信息
├── Step2Playbook            # 合同手册配置
├── Step3Escalation          # 上报矩阵
├── Step4SeedFiles           # 种子文件上传
├── ConfigPreview            # 配置预览
└── CompletionCard           # 完成卡片
```

**交互流程：**
1. 用户进入 `/commercial` → 检测到未配置 → 显示引导卡片
2. 点击「开始配置」→ 跳转到 `/commercial/setup`
3. 逐步回答问题 + 上传种子文件
4. 最后一步预览配置 → 确认保存
5. 跳转回 `/commercial` → 显示已配置状态

#### 7.2.3 合同审查（/commercial/review）

**功能：**
- 文件上传区（拖拽 + 点击，支持 PDF/DOCX/图片）
- 类型自动检测（NDA/SaaS/供应商）+ 手动选择
- 侧边选择（采购方/销售方）
- 审查进度显示（WebSocket 流式）
- 审查结果展示：
  - 底线摘要
  - 严重程度统计（双轴：法律风险 × 商业摩擦）
  - 逐条偏差列表（可展开）
  - 有利条款
  - 缺失条款
  - 审批路由
  - 修改建议包
- NDA 三色分流结果（绿/黄/红）
- 操作按钮：生成业务摘要、上报路由、导出 PDF

**组件：**
```
ContractReviewPage
├── FileUploadZone           # 文件拖拽上传区
├── ReviewConfigPanel        # 审查配置（类型、侧边、金额）
├── ReviewProgress           # 实时进度（WebSocket）
├── ReviewResult
│   ├── BottomLineSummary    # 底线摘要（2句话）
│   ├── SeverityStats        # 双轴严重程度统计
│   ├── DeviationList        # 偏差列表（可展开详情）
│   │   └── DeviationCard    # 单个偏差卡片
│   ├── FavorableTerms       # 有利条款
│   ├── MissingTerms         # 缺失条款
│   ├── ApprovalRouting      # 审批路由
│   └── RevisionPacket       # 修改建议包
├── NdaClassification        # NDA 三色分流（仅 NDA 类型）
├── ActionButtons            # 操作按钮组
└── ChatPanel                # 侧边对话面板（追问）
```

**审查结果偏差卡片设计：**
```
┌──────────────────────────────────────────────┐
│ 🔴 责任限制条款                    法律风险 🔴 │
│                                    商业摩擦 🟠 │
├──────────────────────────────────────────────┤
│ 手册立场：直接损失上限为合同年度金额的 100%    │
│ 合同原文："赔偿总额不超过已付费用的 50%"       │
│ 差距：低于底线（底线为 100%）                  │
├──────────────────────────────────────────────┤
│ 为什么重要：如果供应商造成重大损失，我们最多    │
│ 只能追回一半已付款项。                         │
├──────────────────────────────────────────────┤
│ 建议修改：                                    │
│ "赔偿总额不超过已付费用的 100%"               │
├──────────────────────────────────────────────┤
│ 对方不让步 → 底线方案：接受 75% + 排除 IP     │
│ 赔偿和数据泄露的上限                          │
│ → 上报给：法务负责人                          │
└──────────────────────────────────────────────┘
```

#### 7.2.4 续约管理（/commercial/renewals）

**功能：**
- 续约日历看板（时间轴视图）
- 紧急程度分组列表（🔴🟠🟡）
- 手动添加续约条目
- 编辑/更新续约信息
- 从审查结果自动导入续约（SaaS 审查交接）
- 标记已续约/已取消

**组件：**
```
RenewalsPage
├── RenewalCalendar          # 日历视图（时间轴）
├── UrgencyGroups            # 紧急程度分组列表
│   ├── RedGroup (0-13天)
│   ├── OrangeGroup (14-44天)
│   └── YellowGroup (45-89天)
├── AddRenewalDialog         # 添加续约对话框
├── RenewalDetailPanel       # 续约详情面板
└── MissedWindowsAlert       # 错过窗口提醒
```

#### 7.2.5 事项管理（/commercial/matters）

**功能：**
- 事项列表（活跃/已关闭）
- 新建事项（引导式录入）
- 事项详情（基本信息 + 关联审查 + 历史记录 + 工作笔记）
- 切换当前活跃事项
- 关闭事项

**组件：**
```
MattersPage
├── MatterList               # 事项列表
├── CreateMatterDialog       # 新建事项对话框
└── MatterDetail
    ├── MatterInfo           # 基本信息
    ├── RelatedReviews       # 关联审查记录
    ├── MatterHistory        # 事件历史
    └── MatterNotes          # 工作笔记
```

#### 7.2.6 辅助工具页面

**上报路由（/commercial/tools/escalation）：**
- 输入问题描述
- 显示审批矩阵匹配结果
- 生成上报消息草稿
- 复制/发送按钮

**业务摘要（/commercial/tools/summary）：**
- 选择已完成的审查
- 选择目标受众（采购/部门负责人/财务/安全/高管）
- 生成 200 字业务语言摘要
- 复制/分享

**修订历史（/commercial/tools/amendments）：**
- 上传基础协议 + 所有修订
- 选择模式：全量变更摘要 / 特定条款追踪
- 展示时间线 + 当前有效状态表

### 7.3 导航更新

更新侧边栏导航，移除旧入口，新增：

```typescript
// 侧边栏菜单结构
const sidebarMenu = [
  {
    title: 'AI 对话',
    icon: MessageSquare,
    href: '/chat',
  },
  {
    title: '商事合同',       // 新增
    icon: FileText,
    href: '/commercial',
    children: [
      { title: '概览', href: '/commercial' },
      { title: '合同审查', href: '/commercial/review' },
      { title: '续约管理', href: '/commercial/renewals' },
      { title: '事项管理', href: '/commercial/matters' },
      { title: '辅助工具', href: '/commercial/tools' },
      { title: '设置', href: '/commercial/settings' },
    ],
  },
  // 后续其他模块...
];
```

### 7.4 通用组件

新建 `frontend/src/components/commercial/`：

| 组件 | 用途 |
|------|------|
| `SeverityBadge.tsx` | 双轴严重程度徽章（法律风险 × 商业摩擦） |
| `ClassificationBadge.tsx` | NDA 三色分流徽章 |
| `DeviationCard.tsx` | 偏差详情卡片 |
| `PlaybookReference.tsx` | 手册立场引用展示 |
| `ContractUploader.tsx` | 合同文件上传组件（拖拽 + 类型检测） |
| `ColdStartWizard.tsx` | 冷启动访谈向导组件 |
| `RenewalCalendar.tsx` | 续约日历组件 |
| `MatterSelector.tsx` | 事项选择器（切换当前事项） |
| `EscalationMessage.tsx` | 上报消息预览/编辑组件 |
| `StakeholderSummary.tsx` | 业务摘要展示组件 |

---

## 8. 技能实现详解

### 8.1 cold-start-interview 实现

**触发条件：**
- 用户访问商事合同模块，`module_configs` 表中无记录或 `setup_status != 'completed'`
- 用户主动请求「配置」「设置」

**实现方式：**
- 不走 Agent 对话，而是**多步表单**（前端引导 + 后端处理）
- 每步收集信息存入 `module_configs.setup_data`（JSON）
- 最后一步生成完整的实践画像，写入 `commercial_profiles`

**步骤设计：**

| 步骤 | 前端 | 后端 |
|------|------|------|
| 0 | 选择使用者角色 + 快速/完整模式 | 创建 module_config 记录 |
| 1 | 表单：公司名称、团队规模、业务类型、月均合同量、侧边 | 存入 setup_data |
| 2 | 表单：合同手册（责任上限、赔偿、数据保护、期限、管辖法律、红线） | 存入 setup_data |
| 3 | 表单：上报矩阵（审批级别、阈值、审批人、方式） | 存入 setup_data |
| 4 | 上传 5-10 份已签协议 | 解析文件 → 提取实际签署立场 → 与声明立场对比 |
| 完成 | 预览配置 → 确认 | 写入 commercial_profiles，更新 module_config.setup_status = 'completed' |

### 8.2 vendor-agreement-review 实现

**触发条件：**
- 用户上传合同文件 + 类型检测为供应商协议
- 用户请求「审查合同」

**实现方式：**
- 走 Agent 对话模式
- Agent 系统提示词 = 实践画像 + 合同法参考 + vendor-review 技能指导 + 安全机制
- 工具：search_law, get_law_article, read_practice_profile, get_playbook, write_renewal_register

**执行流程：**

```
1. 前端上传文件 → 后端解析为纯文本
2. 后端检测合同类型 → 'vendor'
3. 创建 Agent，传入系统提示词
4. Agent 执行：
   a. 定位（协议类型、角色、金额、期限）
   b. 绝对红线检查
   c. 逐条对比（读取 playbook 工具）
   d. 责任限制四维分析
   e. 管辖地检查
   f. 有利条款 + 缺失条款
   g. 审批路由（读取 escalation_matrix）
   h. 组装备忘录
5. 结果存入 contract_reviews 表
6. WebSocket 流式推送给前端
```

### 8.3 nda-review 实现

**触发条件：**
- 类型检测为 NDA
- 用户请求「审查保密协议」

**特殊之处：**
- 输出为三色分流（GREEN/YELLOW/RED），不是完整备忘录
- 设计为非律师自助使用
- 不谈判，只分类

### 8.4 saas-msa-review 实现

**触发条件：**
- 类型检测为 SaaS
- 用户请求「审查 SaaS 协议」

**特殊之处：**
- 先执行完整的供应商协议审查（6 步）
- 再叠加 SaaS 专属审查层（6 个维度）
- AI/ML 权利判定（7 个维度）
- 自动交接续约信息到续约登记册

### 8.5 renewal-tracker 实现

**触发条件：**
- 用户请求「续约」「到期」
- SaaS 审查交接
- 定时代理调用

**实现方式：**
- 不走 Agent，直接查询 `renewal_registrations` 表
- 4 种模式：录入、即将到来、CLM 扫描、错过窗口
- 默认模式：未来 90 天，按紧急程度分组

### 8.6 escalation-flagger 实现

**触发条件：**
- 用户请求「谁批准」「上报」
- 审查过程中发现超出审查者权限的问题

**实现方式：**
- 走 Agent 对话模式
- 读取上报矩阵
- 匹配审批人
- 生成上报消息草稿（不发送）

### 8.7 stakeholder-summary 实现

**触发条件：**
- 用户请求「给业务总结」「非法律版摘要」

**实现方式：**
- 走 Agent 对话模式
- 输入：已完成的审查备忘录
- 输出：200 字业务语言摘要
- 受众校准表内置

### 8.8 amendment-history 实现

**触发条件：**
- 用户请求「改了什么」「修订历史」
- 用户上传多个版本

**实现方式：**
- 走 Agent 对话模式
- 2 种模式：全量变更摘要 / 特定条款追踪
- 输入：基础协议 + 所有修订文件

### 8.9 matter-workspace 实现

**触发条件：**
- 用户请求「新建事项」「切换事项」

**实现方式：**
- 不走 Agent，直接 CRUD 操作 `commercial_matters` 表
- 子命令：new / list / switch / close / none
- 其他技能通过 `read_matter_context` 工具获取当前事项上下文

---

## 9. 定时代理实现

### 9.1 renewal-watcher

**调度：** 每周一 09:00
**逻辑：**
1. 遍历所有配置了商事合同模块的用户
2. 查询各用户的续约登记册
3. 计算未来 90 天内的续约
4. 按紧急程度分组
5. 生成 Markdown 报告
6. 存入通知表，前端展示通知

**输出格式：**
```markdown
📅 **续约预警 — [日期] 周**

🔴 **13天内需取消**
• [对方名称] — 取消截止 **[日期]**（[年度金额]）— 负责人：[业务负责人]

🟠 **14-44天内需取消**
• [对方名称] — 取消截止 [日期]（[金额]）

🟡 **45-89天内需取消**
• [N] 份协议 — [查看详情]
```

### 9.2 deal-debrief

**调度：** 每周一 10:00
**逻辑：**
1. 查询上周的合同审查记录
2. 对比手册立场
3. 提取偏差
4. 写入 `contract_deviations` 表
5. 触发 playbook-monitor 检查

### 9.3 playbook-monitor

**调度：** 数据触发（deal-debrief 写入后调用）
**逻辑：**
1. 统计各条款偏差次数（12 个月滚动窗口）
2. 偏差 >= 5 次 → 生成更新提案
3. 写入 `playbook_proposals` 表
4. 通知用户

---

## 10. 开发排期

### 总工期：约 5-6 周

```
Week 1:  Phase 1 — 基础架构
         ├── Day 1-2: 数据库迁移 + 移除旧代码
         ├── Day 3-4: Repository + Schema
         └── Day 5:   文件处理服务

Week 2:  Phase 2 — 技能引擎（上）
         ├── Day 1-2: 技能注册系统 + 提示词提取
         ├── Day 3:   工具实现（配置、续约、事项）
         └── Day 4-5: Agent 初始化 + 技能路由

Week 3:  Phase 2 — 技能引擎（下）+ Phase 3 — API
         ├── Day 1-2: 完成所有技能的 Agent 执行
         ├── Day 3-4: REST API 端点
         └── Day 5:   WebSocket 端点

Week 4:  Phase 4 — 定时任务 + Phase 5 — 前端（上）
         ├── Day 1:   APScheduler 集成 + 3 个定时代理
         ├── Day 2-3: 冷启动访谈页面 + 合同审查页面
         └── Day 4-5: 续约管理页面 + 事项管理页面

Week 5:  Phase 5 — 前端（下）+ 联调
         ├── Day 1-2: 辅助工具页面 + 通用组件
         ├── Day 3-4: 全链路联调
         └── Day 5:   Bug 修复 + 优化

Week 6:  测试 + 部署
         ├── Day 1-2: 集成测试
         ├── Day 3:   性能测试
         └── Day 4-5: 部署 + 验收
```

### 关键里程碑

| 里程碑 | 目标日期 | 交付物 |
|--------|---------|--------|
| M1: 旧功能移除 | Week 1 Day 2 | 清洁的代码库，无 LPA/Cases 代码 |
| M2: 数据模型就绪 | Week 1 Day 4 | 7 张新表 + Alembic 迁移 |
| M3: 冷启动可运行 | Week 2 Day 3 | 用户可完成配置流程 |
| M4: 合同审查可运行 | Week 3 Day 2 | 上传合同 → 得到审查报告 |
| M5: 全部技能可用 | Week 3 Day 5 | 9 个技能全部通过手动测试 |
| M6: 前端完成 | Week 5 Day 2 | 所有页面可用 |
| M7: 定时代理上线 | Week 4 Day 1 | 后台任务正常运行 |
| M8: 验收通过 | Week 6 Day 5 | 全部功能验收 |

---

## 11. 附录：关键文件清单

### 11.1 需要读取的 claude-for-legal-zh 源文件

| 文件 | 用途 |
|------|------|
| `commercial-legal/CLAUDE.md` | 实践画像模板 |
| `commercial-legal/references/contract-law-core.md` | 合同法参考（496行） |
| `commercial-legal/skills/cold-start-interview/SKILL.md` | 冷启动技能 |
| `commercial-legal/skills/vendor-agreement-review/SKILL.md` | 供应商审查技能 |
| `commercial-legal/skills/nda-review/SKILL.md` | NDA 分流技能 |
| `commercial-legal/skills/saas-msa-review/SKILL.md` | SaaS 审查技能 |
| `commercial-legal/skills/renewal-tracker/SKILL.md` | 续约追踪技能 |
| `commercial-legal/skills/escalation-flagger/SKILL.md` | 上报路由技能 |
| `commercial-legal/skills/stakeholder-summary/SKILL.md` | 业务摘要技能 |
| `commercial-legal/skills/amendment-history/SKILL.md` | 修订历史技能 |
| `commercial-legal/skills/matter-workspace/SKILL.md` | 事项工作区技能 |
| `commercial-legal/agents/renewal-watcher.md` | 续约监控代理 |
| `commercial-legal/agents/deal-debrief.md` | 偏差收集代理 |
| `commercial-legal/agents/playbook-monitor.md` | 手册监控代理 |

### 11.2 需要新建的后端文件

```
backend/app/
├── agents/commercial/
│   ├── __init__.py
│   ├── agent.py                # Agent 工厂
│   ├── skills.py               # 技能注册
│   ├── tools.py                # 工具实现
│   ├── router.py               # 技能路由
│   └── prompts/
│       ├── __init__.py
│       ├── security.py         # 共享安全机制提示词
│       ├── cold_start.py
│       ├── vendor_review.py
│       ├── nda_review.py
│       ├── saas_review.py
│       ├── renewal_tracker.py
│       ├── escalation.py
│       ├── stakeholder.py
│       ├── amendment.py
│       └── matter.py
├── api/routes/v1/
│   ├── commercial.py           # REST API
│   └── commercial_ws.py        # WebSocket
├── db/models/
│   ├── commercial_profile.py
│   ├── renewal_registration.py
│   ├── commercial_matter.py
│   ├── contract_review.py
│   ├── contract_deviation.py
│   ├── playbook_proposal.py
│   └── module_config.py
├── repositories/
│   ├── commercial_profile_repo.py
│   ├── renewal_registration_repo.py
│   ├── commercial_matter_repo.py
│   ├── contract_review_repo.py
│   ├── contract_deviation_repo.py
│   ├── playbook_proposal_repo.py
│   └── module_config_repo.py
├── schemas/
│   └── commercial.py
├── services/
│   ├── contract_parser.py      # 文件解析
│   └── contract_type_detector.py # 类型检测
└── tasks/
    ├── __init__.py
    ├── scheduler.py            # APScheduler 配置
    └── commercial/
        ├── renewal_watcher.py
        ├── deal_debrief.py
        └── playbook_monitor.py
```

### 11.3 需要新建的前端文件

```
frontend/src/
├── app/[locale]/(dashboard)/commercial/
│   ├── page.tsx
│   ├── setup/page.tsx
│   ├── review/page.tsx
│   ├── review/[id]/page.tsx
│   ├── renewals/page.tsx
│   ├── matters/page.tsx
│   ├── matters/[slug]/page.tsx
│   ├── tools/escalation/page.tsx
│   ├── tools/summary/page.tsx
│   ├── tools/amendments/page.tsx
│   └── settings/page.tsx
├── components/commercial/
│   ├── SeverityBadge.tsx
│   ├── ClassificationBadge.tsx
│   ├── DeviationCard.tsx
│   ├── PlaybookReference.tsx
│   ├── ContractUploader.tsx
│   ├── ColdStartWizard.tsx
│   ├── RenewalCalendar.tsx
│   ├── MatterSelector.tsx
│   ├── EscalationMessage.tsx
│   └── StakeholderSummary.tsx
├── lib/api/
│   └── commercial.ts
└── stores/
    └── commercial-store.ts
```

---

*文档生成时间：2026-05-28*
*基于 claude-for-legal-zh 商事合同模块 + LexMind v0.6.0.1 架构*
