# 知识产权模块（IP-Legal）开发计划

**版本：** 1.0
**日期：** 2026-06-10
**目标：** 将 claude-for-legal-zh 的**知识产权模块**完整融入 LexMind，作为第 5 个法律模块，**严格复用 privacy（隐私数据）/ employment（劳动用工）/ corporate（公司并购）已验证的真实架构模式**。

---

## Context（为什么做这件事）

LexMind 已落地 4 个法律模块（commercial → corporate → employment → privacy），均遵循同一套"四层移植 + 传输层三分"的真实架构。本次新增**知识产权模块**（第 5 个），把 claude-for-legal-zh 的 `ip-legal` 插件的能力，通过 LexMind 的产品形态（后端 API + Web UI）交付给中国律师与法务人员。

**最关键的事实澄清（务必先读）：**

- 真正的移植源是 **`~/.claude/plugins/marketplaces/claude-for-legal-zh/ip-legal/`**（中文本地化版，作者"陈石 律师"）。
- 它覆盖的是**中国法**：**《商标法》《专利法》《著作权法》《反不正当竞争法》**及配套司法解释、《信息网络传播权保护条例》《电子商务法》《专利代理条例》；**不是** 美国 Lanham Act / DMCA / 35 U.S.C.。
  - 商标可注册性与混淆 = **商标法第 8–14、30–33、57 条** + 商标审查指南
  - 专利侵权"全面覆盖" = **专利法第 64 条** + 侵犯专利权纠纷案件解释（字面/等同/禁止反悔）
  - 网络传播权通知-删除 = **《信息网络传播权保护条例》第 14–16 条 + 《电子商务法》第 42–43 条**
  - 专利代理师保密义务 = **《专利代理条例》第 17 条**（仅延及 CNIPA 前专利代理业务）
- ⚠️ 不要使用英文上游缓存 `~/.claude/plugins/cache/claude-for-legal/ip-legal/`（那是美/欧版，含 DMCA、35 U.S.C. § 271 等）。一切以 `claude-for-legal-zh` marketplace 为准。
- 因为是中国法，**可直接复用 LexMind 现有中文法条 RAG**（`search_law` / `get_law_article`），与 employment / privacy 一致。

**IP 模块相对 privacy 的两处结构性新增（决定本期 5 表而非 4 表）：**

1. **对外维权信函**（侵权警告函、网络传播权通知/反通知）有信函起草、发送门禁与生命周期 → 独立 `ip_enforcement` 表（类比 privacy_dsar 的两函生命周期）。
2. **知识产权组合登记册**（商标/专利/著作权/域名注册 + 续展期限）→ 独立 `ip_portfolio` 表（类比 commercial 的 renewal_registrations），并喂养 `ip-renewal-watcher` 定时代理。

**最终效果**：知识产权模块的后端 Agent / 提示词 / 工具 / 工作流**完全遵循** `claude-for-legal-zh` 的 ZH `SKILL.md` 定义，LexMind 只提供用户友好的前端 UI 和把"配置文件 CLAUDE.md"换成"数据库画像表"的产品化封装。

---

## 目录

1. [总体目标与范围](#1-总体目标与范围)
2. [模块全景（技能按传输层三分）](#2-模块全景技能按传输层三分)
3. [复用既有架构（镜像 privacy / employment）](#3-复用既有架构镜像-privacy--employment)
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

将 `claude-for-legal-zh` 知识产权模块的 **10 个核心技能 + customize + 冷启动基础设施** 移植到 LexMind：

- 用户访问「知识产权」模块时，若未配置则引导冷启动访谈
- 配置完成后，用户可通过前端界面使用全部技能
- 后端 Agent / 提示词 / 工具 **完全遵循** ZH `SKILL.md`（中国法实质内容 + 共享护栏 + 多模式技能理念）
- **架构上逐项镜像 privacy 模块**（最新、最近的同构样板；privacy 又镜像 employment → corporate）
- 1 个定时代理（ip-renewal-watcher 周度续展期限预警，纯算术，无 LLM）

### 1.2 范围

**包含（用户列出的 10 个核心技能 + 必要基础设施）：**

| 技能 | 中文 | 落地形态 |
|------|------|---------|
| cold-start-interview | 冷启动访谈 | 冷启动**服务状态机** + 前端向导（**非 Agent**） |
| clearance | 商标可注册性检索初筛 | WS Agent |
| fto-triage | 专利自由实施初步分析 | WS Agent |
| invention-intake | 发明披露初筛 | WS Agent |
| infringement-triage | 侵权初步分析（商标/著作权/专利/商业秘密四态） | WS Agent |
| ip-clause-review | 合同 IP 条款审查 | WS Agent |
| oss-review | 开源许可证合规检查 | WS Agent |
| cease-desist | 侵权警告函（发送/接收双模式） | REST 建档 + WS Agent 起草 |
| takedown | 网络传播权通知（发送/回应/反通知三模式） | REST 建档 + WS Agent 起草 |
| portfolio | 注册续展跟踪（report/add/update/audit） | REST CRUD + 算术（**非 Agent**） |
| customize | 修改画像某一项 | 前端**设置页** + `PUT /ip/profile`（非 Agent） |

**明确延后（不在本期）：**

- `matter-workspace`（事项工作区）— **不在用户列出的 10 技能内**；且照 privacy/employment 先例，企业法务默认隐藏 matter 概念，本期统一用 **practice-level（实践级）上下文**。源插件 CLAUDE.md 中此节默认"已启用：✗"。后续如需私人执业多客户隔离再引入。
- **元典 / 北大法宝 / CNIPA MCP 检索** — 本期用 LexMind 现有 RAG（`search_law`）替代；ZH 提示词里的 `[元典检索]/[北大法宝]/[CNIPA]` 标签改为 `[本地知识库]/[法条原文]`（见 §7.11）。
- **外部 MCP 集成**（IP 管理系统同步 Anaqua/PatSnap/智慧芽/大为、Drive / SharePoint / 飞书文档 / 即时通讯）— 本期不接；冷启动「可用集成」一节统一标记为不可用，按 ZH 的降级路径处理（输出存库、通知内嵌、portfolio 手动维护）。

### 1.3 与 commercial / corporate / employment / privacy 的关系

| 维度 | commercial | corporate | employment | privacy | **ip（本期）** |
|------|-----------|-----------|------------|---------|----------------|
| 路由前缀 | `/commercial` | `/corporate` | `/employment` | `/privacy` | `/ip` |
| module_configs.module_name | `commercial-legal` | `corporate-legal` | `employment-legal` | `privacy-legal` | `ip-legal` |
| 独立 profile 表 | `commercial_profiles` | `corporate_profiles` | `employment_profiles` | `privacy_profiles` | `ip_profiles`（新建，**非共享**） |
| Agent 工厂 | `agents/commercial/` | `agents/corporate/` | `agents/employment/` | `agents/privacy/` | `agents/ip/agent.py`（镜像 privacy） |
| WS 端点 | `/ws/commercial` | `/ws/corporate` | `/ws/employment` | `/ws/privacy` | `/ws/ip` |
| 定时任务 | renewal_watcher, deal_debrief, playbook_monitor | dataroom_watcher | leave_tracker | policy_sweep_reminder | **ip_renewal_watcher** |
| 前端页面 | `/commercial/*` | `/corporate/*` | `/employment/*` | `/privacy/*` | `/ip/*` |

---

## 2. 模块全景（技能按传输层三分）

**核心原则（来自 corporate/employment/privacy 真实代码）：** REST 端点**全部是 CRUD（纯 service 调用）**；所有 Agent 驱动的技能**只走 WebSocket**，前端用显式 `action` 字段选择技能，**后端不做 LLM / 关键词意图路由**（见 `privacy_ws.py` / `employment_ws.py`："skill chosen explicitly by the client — no LLM intent routing"）。

### 2.1 技能 → 传输层映射矩阵

| # | 技能 | 传输层 | 入口 | 落库表 |
|---|------|--------|------|--------|
| 1 | cold-start-interview | **REST**（service 状态机）+ 前端向导 | `POST /ip/setup` | module_configs → ip_profiles |
| 2 | customize | **REST** | `PUT /ip/profile` | ip_profiles |
| 3 | clearance | **WS** `action=clearance` | `/ws/ip` | ip_reviews（type=clearance） |
| 4 | fto-triage | **WS** `action=fto` | `/ws/ip` | ip_reviews（type=fto） |
| 5 | invention-intake | **WS** `action=invention` | `/ws/ip` | ip_reviews（type=invention） |
| 6 | infringement-triage | **WS** `action=infringement` | `/ws/ip` | ip_reviews（type=infringement） |
| 7 | ip-clause-review | **WS** `action=ip_clause` | `/ws/ip` | ip_reviews（type=ip_clause） |
| 8 | oss-review | **WS** `action=oss` | `/ws/ip` | ip_reviews（type=oss） |
| 9 | cease-desist | **REST 建档** + **WS** `action=cease_desist` 起草 | `POST /ip/enforcement` → `/ws/ip` | ip_enforcement |
| 10 | takedown | **REST 建档** + **WS** `action=takedown` 起草 | `POST /ip/enforcement` → `/ws/ip` | ip_enforcement |
| 11 | portfolio（report/add/update/audit） | **REST** CRUD + 算术 | `GET/POST/PUT /ip/portfolio` | ip_portfolio |
| 12 | ip-renewal-watcher（续展提醒） | **cron**（纯算术） | scheduler job | ip_notifications |

WS `action` 合计 **8 个**：`clearance / fto / invention / infringement / ip_clause / oss / cease_desist / takedown`。

### 2.2 技能依赖关系

```
cold-start-interview ──写入──> ip_profiles（实务画像 / CLAUDE.md 等价物）

所有 WS Agent 技能 ──读取──> ip_profiles（前置条件；未配置则 /status 引导冷启动）
所有 WS Agent 技能 ──若未配置 LLM──> 报错 llm_not_configured（绝不兜底）

infringement-triage(WS) ──四态分析(TM/著作权/专利/商业秘密)──> 分类(忽略/沟通/警告函/起诉)
    └─ 若 🔴清晰侵权 / 🟠很可能侵权 ──桥接──> cease-desist(发送) 或 takedown(著作权)

clearance(WS) ──"初步非意见"盾──> 固有障碍表 + 近似商标 + 混淆因素(商标法§57) ──> 🟢/🟡/🔴（绝不下"可注册"结论）
fto-triage(WS) ──"初步非意见"盾──> 权利要求逐元素对照(专利法§64) + 故意侵权警告(§71) ──> 写 review(type=fto)
    └─ 遇外观设计 ──立即路由──> 设计专业律师（§23 不同测试，停止逐元素分析）
invention-intake(WS) ──六维筛查(新颖/创造/可授权主题/公开时间§24/可检测/战略价值)──> 三态(推进/调查/驳回)

ip-clause-review(WS) ──转让缺陷盾 + 逐条审计──> 写 review(type=ip_clause)
oss-review(WS) ──按部署模式(SaaS/分发/内部/嵌入)逐包分类许可证──> 🔴可否发布 + 义务清单

cease-desist：REST POST 建 ip_enforcement 档(mode + 对方 + 涉案权利 + 尽调) ──> WS action=cease_desist 起草信函 ──发送门禁──> 回写
takedown：REST POST 建 ip_enforcement 档 ──> WS action=takedown 起草通知/反通知 ──发送门禁 + 15工作日时钟──> 回写

portfolio：REST add/update 维护 ip_portfolio；report/audit 按管辖地规则算术重算期限
ip_renewal_watcher(cron) ──纯算术：读 ip_portfolio，按管辖地规则重算下一期限，分桶预警──> 写 ip_notifications（不调 LLM）
```

### 2.3 多模式技能保真（本模块的灵魂）

IP 维权天然是双方/多向的，多个技能保留**模式分支**，必须保真移植：

- **cease-desist（侵权警告函）— 双模式**
  - **发送（send）**：识别权利 → 识别侵权 → 识别关系 → 识别请求 → 按维权姿态校准 → **对方尽调（§⑤.5：实体、资源、IP 组合、诉讼史、是否聘律、反诉风险）** → 按中国实务起草 → **发送前 LOUD GATE**。
  - **接收（receive）**：解析来函 → 评估对方主张（权利有效？事实基础？是否过度？时效？）→ 评估己方敞口 → **四选项树**（遵从/谈判/反制（确认不侵权之诉/无效宣告/不侵权抗辩）/忽略）。注意 **确认不侵权之诉风险** 与过宽警告函触发的反法§17 惩罚性赔偿反制。
- **takedown（网络传播权通知）— 三模式**
  - **发送（send）**：识别作品（登记状态）→ 识别侵权内容（URL/平台/证据）→ **合理使用四因素门（著作权法§24，穷尽列举，比美国窄）** → 按《条例》§14 + 电商法§42 起草通知。
  - **回应（respond）**：解析收到的通知 → 评估（是否有许可/合理使用/通知有瑕疵/平台是否依§15/§17 履行）→ 四选项树。
  - **反通知（counter）**：确认删除由通知触发 → 善意相信删除有误 → 按《条例》§16 + 电商法§43 起草反通知（注意**15 个工作日**起诉等待期）。
- **infringement-triage（侵权初步分析）— 四态（按 IP 类型分支）**
  - 商标（混淆可能性，商标法§57）/ 著作权（接触+实质相似 + 合理使用§24 + 通知删除）/ 专利（发明实用新型逐元素§64；**外观设计立即路由设计律师**）/ 商业秘密（三要件：秘密性/价值性/保密措施，反法§9 + 反向工程抗辩）。每态输出因素表，**绝不下结论**（留待主审律师）。
- **ip-clause-review（合同 IP 条款）— 两步**
  - 转让缺陷盾（是否应从对方受让 IP？现在式转让语言是否到位？**著作人身权放弃**著作权法§10）+ 逐条风险审计。

每个多模式技能：**自动识别模式；不明确时问一次**。落库 `ip_enforcement.mode` / `ip_reviews.classification`。

### 2.4 维权姿态与 4 种工作成果抬头（IP 独有，privacy 没有）

**维权姿态**（激进/适度/保守）从画像读取，决定 cease-desist 默认提供的第一选项（激进→直接警告函草稿；保守→温和沟通）。发函审批矩阵（函件类型→审批人→升级触发）与自动升级触发（对方是客户/对方更强/涉专利/可能上媒体）从画像注入。

**4 种工作成果抬头**（《专利代理条例》第 17 条特权范围所限，按 role × 事项类型分支）：

| 角色 / 事项 | 抬头 |
|------|------|
| 律师 / 法律专业人士 | `保密——律师工作成果——按照律师指示准备` |
| 专利代理师 · CNIPA 前专利事项 | `保密——专利代理师—委托人特权——《专利代理条例》第17条——CNIPA 代理业务` |
| 专利代理师 · **非**专利事项（商标/著作权/开源/商业秘密/合同） | `研究笔记——非特权——专利代理师特权不延及非专利代理业务——在行动前应由执业律师审阅` |
| 非律师（有/无律师对接） | `研究笔记——非法律意见——在行动前应由执业律师审阅` |

> ⚠️ **错误的"特权"标注制造可被发现的认可**。为专利代理师用户在非专利事项上运行的技能必须标注 `非特权`。security 提示词与前端 `WorkProductHeader` 组件都要实现此 (role × matter_type) 分支。**对外交付物（警告函/网络传播权通知/对外摘要）一律移除抬头**。

### 2.5 定时代理

| 代理 | 调度 | 功能 | 是否调 LLM |
|------|------|------|-----------|
| ip_renewal_watcher | 每周一 09:47（错峰；09:07/09:23/09:37/10:07/08:17 已被占用） | 读 `ip_portfolio`，按管辖地规则**重算**每项资产下一期限（不信任已存日期），分桶预警；宽展/已失效即时上报 | **否**（纯算术，照 dataroom_watcher / commercial renewal_watcher） |

> 说明：源 `ip-renewal-watcher.md` 的期限计算是确定性算术（商标法§40 十年+6月宽展、专利年费等），因此 cron 不调 LLM，符合既有惯例（leave-tracker / dataroom-watcher / policy_sweep_reminder）。即便无到期事项也发简短"无事报告"——"静默通过看起来与损坏的定时任务一模一样"。

---

## 3. 复用既有架构（镜像 privacy / employment）

### 3.1 直接复用的公共引擎（不新建）

| 组件 | 路径 | 复用方式 |
|------|------|---------|
| 模型工厂 | `agents/model_factory.py` → `create_pydantic_model()` | 直接调用 |
| Agent 流式引擎 | `services/agent_stream.py` → `stream_agent_run()` | 直接调用 |
| WS 连接管理 | `services/agent.py` → `AgentConnectionManager` | 直接复用 |
| WS 鉴权 | `api/deps.py` → `get_current_user_ws` | 直接复用 |
| 调度器 | `scheduler.py`（APScheduler，已挂在 lifespan） | **只新增一个 job**，不改 lifespan |
| module_configs 表 | `db/models/module_config.py` | 直接复用，`module_name="ip-legal"` |
| 法律检索工具 | `agents/tools/law_tools.py` → `search_law / get_law_article` | 按需挂到需法条的技能 |
| 活跃用户迭代 | `tasks/*` → `iter_active_user_ids(db)` | cron 直接复用 |
| 领域异常 | `core/exceptions.py`（NotFoundError 等） | 直接复用 |
| JSON 序列化助手 | `services/_emp_serialize.py` → `dump_for_db()` | 直接复用 |
| 冷启动状态机基类 | `services/privacy_cold_start_service.py`（状态机蓝本） | 复制为 ip 版 |

### 3.2 复制 privacy/employment 模式新建的组件（**复制而非共享**）

profile / cold-start / WS / route 在各模块间是**逐字并行的多份代码**（如 `privacy_profile_service.py` 与 `employment_profile_service.py` 结构一致），不存在共享 company-profile。ip 同样新建自己的一套：

| 组件 | 镜像来源 | ip 新建 |
|------|---------|----------------|
| Agent 工厂 | `agents/privacy/agent.py` | `agents/ip/agent.py` |
| Agent Deps | `agents/privacy/deps.py` | `agents/ip/deps.py` |
| 提示词 | `agents/privacy/prompts/` | `agents/ip/prompts/` |
| 工具 | `agents/privacy/tools/` | `agents/ip/tools/` |
| WS 端点 | `api/routes/v1/privacy_ws.py` | `api/routes/v1/ip_ws.py` |
| REST 端点 | `api/routes/v1/privacy.py` | `api/routes/v1/ip.py` |
| profile service | `services/privacy_profile_service.py` | `services/ip_profile_service.py` |
| cold-start service | `services/privacy_cold_start_service.py` | `services/ip_cold_start_service.py` |
| 子服务 | `services/privacy_*_service.py` | `services/ip_*_service.py` |
| 通知模型 | `db/models/privacy_notification.py` | `db/models/ip_notification.py` |
| 定时任务 | `tasks/privacy_policy_sweep_reminder.py` | `tasks/ip_renewal_watcher.py` |
| 前端 API 客户端 | `lib/privacy.ts` | `lib/ip.ts` |
| 前端聊天 Hook | `hooks/use-privacy-chat.ts` | `hooks/use-ip-chat.ts` |
| 前端类型 | `types/privacy.ts` | `types/ip.ts` |
| 前端代理路由 | `app/api/privacy/[[...path]]/route.ts` | `app/api/ip/[[...path]]/route.ts` |

---

## 4. 数据模型设计

### 4.1 ORM 约定（强制）

所有模型用 SQLAlchemy `Mapped` 风格 + 继承 `Base, TimestampMixin`（见 `db/models/privacy_profile.py`），**不手写 created_at/updated_at**；`String(36)` 主键 + `default=lambda: str(uuid.uuid4())`；FK `ondelete="CASCADE"`。下文用字段表描述结构，**不用裸 `CREATE TABLE`**。复杂结构一律 JSON 文本列（repo 序列化、schema 用 `field_validator(mode="before")` 反序列化）。

### 4.2 表清单（5 张新表 + 复用 module_configs）

> 设计取舍：clearance/fto/invention/infringement/ip_clause/oss 这 6 类**内部分析产出**结构相近且需跨技能引用（严重性底线 + prior-context 检索），故统一进 **`ip_reviews`**（`review_type` 判别 + `result_json`），照 privacy `privacy_reviews`。**维权信函生命周期独特**（信函草稿、模式、对方尽调、发送门禁、反通知 15 工作日时钟），单独建 **`ip_enforcement`**（类比 privacy_dsar）。**注册组合**有期限算术与 cron 消费，单独建 **`ip_portfolio`**（类比 commercial renewal_registrations）。

#### 4.2.1 `ip_profiles`（知识产权实务画像，1:1 用户）

镜像 ZH `CLAUDE.md` 各节，JSON 列承载：

- 公司画像：`company_context` JSON（实体名称 / 行业 / 阶段 / 主要管辖域 / 痛点 / 执业场景，多来自共享 company-profile）
- 使用者：`user_role`（`lawyer` / `patent_agent` / `non_lawyer_with_counsel` / `non_lawyer_without`）、`lawyer_contact`、`supervising_lawyer`（仅专利代理师）
- 集成：`integrations` JSON（ip_mgmt_system / legal_research / patent_research / doc_storage / im，本期多为 ✗）
- IP 实务画像：`ip_scope` JSON（商标 / 著作权 / 专利 / 商业秘密 / 开源——实际从事哪些）、`registration_jurisdictions` JSON（CNIPA / 港澳 / 马德里 / PCT-EPO）、`ip_management_system`、`domain_ownership` JSON（各业务领域归属人/团队/外所）、`outside_counsel` JSON（外部律所名单表）
- 维权姿态：`enforcement_posture` JSON（`default_stance` 激进/适度/保守 + 何时发警告函/温和沟通/起诉 + `approval_matrix` 发函审批表 + `auto_escalation` 自动升级触发）
- 品牌保护：`brand_protection` JSON（监测标识 / 监测管辖域 / 监测服务 / 监测频率）
- 组合元信息：`portfolio_meta` JSON（last_audit_date / **renewal_alert_channel**）
- 输出与表面：`output_config` JSON（工作成果抬头规则 4 分支 / naming / 安静模式）
- 状态：`setup_status`（not_started/in_progress/completed）、`setup_progress` JSON、`setup_depth`（quick/full）
- `profile_content`（Markdown，编译后的画像，注入系统提示词）
- `UNIQUE(user_id)`

#### 4.2.2 `ip_reviews`（内部分析产出统一表，N）

- `user_id`(FK, index)
- `review_type`：`clearance` / `fto` / `invention` / `infringement` / `ip_clause` / `oss`
- `subject`（商标名 / 产品 / 发明名 / 对方当事人 / 合同名 / 依赖树——用于 prior-context 检索与严重性底线）
- `counterparty`（可空，infringement/ip_clause 上下文匹配）
- `ip_category`（可空：`trademark`/`copyright`/`patent`/`trade_secret`/`design`——infringement 的四态判别）
- `classification`（可空：clearance/oss 用 `GREEN`/`YELLOW`/`RED`；invention 用 `PURSUE`/`INVESTIGATE`/`REJECT`；infringement 用 `IGNORE`/`COMMUNICATE`/`CEASE_DESIST`/`LITIGATE`）
- `severity`（可空：🔴/🟠/🟡/🟢——跨技能严重性底线）
- `result_summary`（text，底线一两句）、`result_memo`（Markdown 全文，含工作成果抬头）、`result_json`（结构化：factors / claim_mapping / obligations / redlines / open_questions）
- `status`（draft/final）
- 由 WS Agent 经 `save_review` 工具写入；REST 仅读历史。`index(user_id, subject)`。

#### 4.2.3 `ip_enforcement`（维权信函生命周期，N）

- `user_id`(FK, index)
- `matter_type`：`cease_desist` / `takedown`
- `mode`：`send` / `receive` / `respond` / `counter`（takedown 用 send/respond/counter；cease_desist 用 send/receive）
- `counterparty`（对方当事人；**最小化**，避免 PII 滥置）
- `right_at_issue` JSON（涉案权利：类型 + 注册号 + 登记状态）
- `infringement_facts`（text，被诉行为/URL/平台/证据描述）
- `due_diligence` JSON（cease-desist 发送前对方尽调：实体/资源/IP 组合/诉讼史/是否聘律/反诉风险）
- `response_deadline` DATE（可空；takedown 反通知触发的 15 工作日时钟、对方来函的回复期限）
- `letter_draft`（Markdown，**内部草稿带抬头**）、`outbound_letter`（Markdown，**对外版本去抬头**）
- `send_gate` JSON（发送门禁核对结果：权利有效 / 主张成立 / 比例适当 / 授权人签署 / 尽调已呈现）
- `recommended_action`（可空：receive/respond 模式的四选项树结论）
- `status`（intake/drafting/gated/sent/responded/escalated/closed）
- `escalation_flag` BOOL、`escalation_reason`
- `log` JSON（审计：建档/起草/过门禁/标记已发送日期、审批人）

> **系统只产草稿、绝不实际发送**：`status=sent` 仅表示用户在前端确认"我已自行发出"，系统不调用任何外发通道（符合安全规则：对外发函由用户本人执行）。

#### 4.2.4 `ip_portfolio`（知识产权组合登记册，N）

- `user_id`(FK, index)
- `asset_type`：`trademark` / `patent_invention` / `patent_utility` / `patent_design` / `copyright` / `domain` / `other`
- `jurisdiction`（CN / Madrid / HK / US / ...）
- `title`（商标名 / 专利名称 / 作品名）
- `owner_entity`（权利人法律实体）
- `status`：`pending` / `registered` / `granted` / `lapsed` / `abandoned`
- `application_number`、`registration_number`
- 关键日期：`filing_date`、`registration_date`、`grant_date`、`priority_date`
- `next_deadlines` JSON（list：{deadline_type, due_date, grace_end, basis_rule, action, status}）
- `business_owner`、`agent_managed` BOOL（是否外协代理代管续展）
- `notes`、`source`（manual / cold_start / ip_system_sync）
- `index(user_id, asset_type)`。续展期限**不存为权威**——由 cron / report 按 `deadline_rules` 实时重算。

#### 4.2.5 `ip_notifications`（通知，N）

照 `privacy_notification.py`：`notification_type`（`renewal_alert` / `manual`）、`title`、`content`（Markdown）、`priority`、`is_read`、`action_url`。

### 4.3 实体关系图

```
users (1) ── (1) ip_profiles
users (1) ── (N) ip_reviews        [review_type: clearance/fto/invention/infringement/ip_clause/oss]
users (1) ── (N) ip_enforcement    [matter_type: cease_desist/takedown · mode: send/receive/respond/counter]
users (1) ── (N) ip_portfolio      [asset_type: trademark/patent_*/copyright/domain]
users (1) ── (N) ip_notifications
users (1) ── (1) module_configs [module_name="ip-legal"]
```

---

## 5. 后端开发任务

### 5.1 Phase 1：数据层

#### 任务 1.1：Alembic 迁移（**幂等守护强制**）

照 privacy 拆 **2 个迁移文件**，链在当前 head 之后（先 `uv run alembic heads` 确认，当前最新为 privacy 的 `2026-06-07_add_privacy_core_tables`）：

1. `2026-06-xx_add_ip_profile_table.py`
2. `2026-06-xx_add_ip_core_tables.py`（reviews / enforcement / portfolio / notifications）

每个 `upgrade()` 用 inspector 守护（**create_all + Alembic 双轨**，否则 `test_migrations` 红），`downgrade()` 名称无关、逆 FK 顺序 drop：

```python
def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "ip_profiles" in inspector.get_table_names():   # 锚点表守护
        return
    op.create_table("ip_profiles", ..., *_ts_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE",
                                name="fk_ip_profiles_user_id"),
        sa.UniqueConstraint("user_id", name="uq_ip_profiles_user_id"))
    op.create_index("ix_ip_profiles_user_id", "ip_profiles", ["user_id"])

def downgrade() -> None:
    op.drop_table("ip_profiles")
```

`_ts_columns()` 助手照 privacy 迁移复制（created_at server_default + updated_at nullable）。

#### 任务 1.2：数据模型（5 文件）
`db/models/ip_profile.py`、`ip_review.py`、`ip_enforcement.py`、`ip_portfolio.py`、`ip_notification.py`。在 `db/models/__init__.py` 导入并加入 `__all__`（`main.py` 启动时 `from app.db import models` 触发 create_all 注册）。

#### 任务 1.3：Repository 层（无状态函数，`db.flush()`+`db.refresh()`，**绝不 commit**）
`ip_profile_repo.py`、`ip_review_repo.py`、`ip_enforcement_repo.py`、`ip_portfolio_repo.py`、`ip_notification_repo.py`。关键字仅参数（`db` 之后 `*`）。列表函数返回 `(items, total)`；`ip_review_repo` 提供 `list_by_subject(user_id, subject)` 供 prior-context 检索；`ip_portfolio_repo` 提供 `list_by_user`（全量供 cron 重算）。JSON 列在 service 内用 `dump_for_db` 序列化。

#### 任务 1.4：Schema 层 `schemas/ip/`
`__init__.py`、`_json.py`（复用 `parse_json_field`）、`profile.py`、`cold_start.py`、`review.py`、`enforcement.py`、`portfolio.py`、`notification.py`。遵循 `*Create/*Update/*Read/*List` + `ConfigDict(from_attributes=True)`；JSON-text 列用 `@field_validator(mode="before")` 解码。`Literal` 类型：`UserRole` / `ReviewType` / `IpCategory` / `EnforcementMode` / `AssetType` / `ModuleStatus`。

### 5.2 Phase 2：技能引擎

#### 任务 2.1：Agent 工厂（镜像 `privacy/agent.py`）
`agents/ip/agent.py`：

```python
IpSkillName = Literal[
    "clearance", "fto", "invention", "infringement", "ip_clause", "oss",
    "cease_desist", "takedown",
]
SKILL_REVIEW_TYPE: dict[IpSkillName, str] = {...}  # clearance->clearance, ... cease_desist/takedown 不入 reviews
_PROMPT_BUILDERS: dict[IpSkillName, Callable[..., str]] = {...}
_SKILL_TOOLS:    dict[IpSkillName, tuple[Callable, ...]] = {...}
# 需要法条检索的技能挂 search_law / get_law_article：
_LAW_TOOL_SKILLS: frozenset[IpSkillName] = frozenset(
    {"clearance", "fto", "invention", "infringement", "ip_clause", "cease_desist", "takedown"}
    # oss 主要比对许可证文本，可不挂；portfolio 非 Agent
)

def create_ip_agent(skill, *, practice_profile_markdown=None,
                    model_name=None, provider=None, api_key=None,
                    base_url=None, temperature=None) -> Agent[IpDeps, str]:
    ...  # 同 privacy：查 builder、create_pydantic_model、挂 _SKILL_TOOLS[skill]、按需挂 law tools、tool_retries=3
```

`agents/ip/deps.py`：

```python
@dataclass
class IpDeps:
    user_id: str
    db: Session
    review_type: str | None = None     # 分析技能预建行后回填
    review_id: str | None = None
    enforcement_id: str | None = None  # cease-desist/takedown 起草目标
    output_dir: str | None = None
```

#### 任务 2.2：提示词提取 `agents/ip/prompts/`
从 `~/.claude/plugins/marketplaces/claude-for-legal-zh/ip-legal/skills/*/SKILL.md` **逐段提取，保留全部实质内容**（中国法条引用、各分类、多模式分支、风险方法论、免责盾、故意侵权警告等）：

| 文件 | 来源 SKILL.md |
|------|-------------|
| `security.py` | 共享护栏 + 风险评价方法论 + **4 种工作成果抬头**（来自 CLAUDE.md） |
| `clearance.py` | clearance（"初步非意见"盾 + 固有障碍 + 混淆因素商标法§57） |
| `fto_triage.py` | fto-triage（权利要求逐元素§64 + 故意侵权§71 + 外观设计路由） |
| `invention_intake.py` | invention-intake（六维筛查 + 三态 + 公开宽限§24） |
| `infringement_triage.py` | infringement-triage（四态：TM/著作权/专利/商业秘密） |
| `ip_clause_review.py` | ip-clause-review（转让缺陷盾 + 逐条审计 + 人身权§10） |
| `oss_review.py` | oss-review（部署模式 + copyleft 分级 + 义务清单） |
| `cease_desist.py` | cease-desist（双模式 + 对方尽调 + 发送门禁） |
| `takedown.py` | takedown（三模式 + 合理使用门 + 15 工作日时钟） |

> cold-start 提示词**不在此**——它是 service 状态机（任务 2.4）。portfolio **非 Agent**——纯算术（§8）。

#### 任务 2.3：工具 `agents/ip/tools/`
签名一律 `async def tool(ctx: RunContext[IpDeps])`，内部做归属校验（照 privacy `tools/*` 的 `_load_owned_*` 模式）。

| 文件 | 工具 |
|------|------|
| `_validators.py` | 域值校验（check_review_type / check_classification 等） |
| `profile_tools.py` | `read_ip_profile`（读画像；未配置则提示去设置） |
| `review_tools.py` | `save_review`（写 ip_reviews，含 type/severity/classification/ip_category）、`read_prior_reviews`（按 subject/counterparty 查 prior 分析，支撑严重性底线） |
| `enforcement_tools.py` | `read_enforcement`、`save_letter`（回写 letter_draft/outbound_letter/send_gate/log/status） |
| `portfolio_tools.py` | `read_portfolio`（供 infringement/clearance 查己方权利） |
| `law_tools.py`（封装复用） | `research_ip_rules(topic, regime)`：先读画像 `ip_scope`/`registration_jurisdictions`，再 RAG `search_law`（商标法/专利法/著作权法/反法），标注来源标签（见 §7.11、§9） |

#### 任务 2.4：cold-start service（**非 Agent**）
`services/ip_cold_start_service.py` 复制 `privacy_cold_start_service.py` 状态机，6 步（对照 ZH cold-start-interview 的 Part 0–6 合并）：

```
0 角色(含专利代理师) + 执业环境 + 集成        1 公司业务背景 + 注册管辖域 + IP 业务领域组合
2 维权姿态(激进/适度/保守 + 发函审批矩阵 + 自动升级)   3 内部规范(开源政策 + 发明申请战略 + 品牌监测标识)
4 种子文件(组合登记导出 / 信函模板 / 开源政策 / 审批手册)     5 输出与表面 + 生成画像
QUICK_PLAN=(0,1,5)   FULL_PLAN=(0,1,2,3,4,5)
```
`MODULE_NAME="ip-legal"`，终步 `_materialize_profile` 编译并写 `ip_profiles.profile_content` + 各 JSON 字段；跳过项写 `[占位符]`/`[立场未测试]`（绝不静默缺口）。若有种子组合导出，可一并初始化 `ip_portfolio`。

### 5.3 Phase 3：API 端点

#### 任务 3.1：REST（`api/routes/v1/ip.py`，全部 CRUD，照 privacy.py 签名）
处理器签名 `(... , user: CurrentUser, svc: IpXxxSvc) -> Any`，声明 `response_model` + 必要 `status_code`，分页 `skip/limit`：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/ip/status` | GET | 模块配置状态（驱动前端"去设置 vs 主界面"） |
| `/ip/setup` | POST | 冷启动步骤提交 |
| `/ip/setup/status` | GET | 冷启动进度 |
| `/ip/profile` | GET / PUT | 实践画像（PUT 即 customize） |
| `/ip/reviews` | GET | 分析产出列表（可按 review_type 过滤） |
| `/ip/reviews/{id}` | GET | 产出详情 |
| `/ip/enforcement` | GET / POST | 维权信函列表 / 建档（POST 落 mode + 对方 + 涉案权利 + 算 deadline） |
| `/ip/enforcement/{id}` | GET / PUT | 信函详情 / 更新（发送门禁结果、标记已发送、升级标记） |
| `/ip/portfolio` | GET / POST | 组合列表（report：算术分桶） / 新增资产 |
| `/ip/portfolio/{id}` | PUT | 更新资产（缴费/同步状态） |
| `/ip/portfolio/audit` | GET | 组合体检（撤三风险§49、pending>2yr、所有权一致性、24 月期限预测） |
| `/ip/notifications` | GET | 通知列表 |
| `/ip/notifications/{id}/read` | POST | 标记已读 |

#### 任务 3.2：WS（`api/routes/v1/ip_ws.py`，镜像 privacy_ws.py）
- `_SKILL_BY_ACTION` 显式映射 8 个 action → `create_ip_agent(skill)`
- `_require_llm_configured`：未配置 LLM → 推 `error / llm_not_configured`（**绝不兜底**）
- 归属预校验（review_id / enforcement_id 属于该用户）
- `clearance/fto/invention/infringement/ip_clause/oss` 仿 privacy **预建 ip_reviews 行**并推 `review_started`；`cease_desist/takedown` 需先解析 enforcement_id（REST 已建档）
- 复用 `stream_agent_run`，事件名一致（见 §6.7）

#### 任务 3.3：DI / 注册 / 挂载
- `api/deps.py`：加 `get_ip_*_service` + `Annotated` 别名（`IpProfileSvc` / `IpColdStartSvc` / `IpReviewSvc` / `IpEnforcementSvc` / `IpPortfolioSvc` / `IpNotificationSvc`）
- `api/routes/v1/__init__.py`：在 privacy 之后加
  ```python
  from app.api.routes.v1 import ip, ip_ws
  v1_router.include_router(ip.router, prefix="/ip", tags=["ip"])
  v1_router.include_router(ip_ws.router, tags=["ip-ws"])
  ```
- `main.py` lifespan **无需改**（scheduler 已挂）

### 5.4 Phase 4：定时代理
`tasks/ip_renewal_watcher.py`，照 `privacy_policy_sweep_reminder.py` 写 `run(db) -> int`：遍历 `iter_active_user_ids`、读 `ip_portfolio`、用 `tasks/ip_deadline_rules.py` 按管辖地重算下一期限、分桶、命中预警窗口写 `ip_notifications`。**不调 LLM。** `scheduler.py` 新增 job（周一 09:47）。详见 §8。

### 5.5 Phase 5：服务层
`ip_profile_service.py`、`ip_cold_start_service.py`（任务 2.4 已起）、`ip_review_service.py`、`ip_enforcement_service.py`（含建档时算 response_deadline、发送门禁状态机、升级触发判定）、`ip_portfolio_service.py`（report/audit 调用 deadline_rules）、`ip_notification_service.py`。可按 privacy 把小服务合并。服务用 `dump_for_db` 编码 JSON 列；读方法做归属校验（`raise NotFoundError`）。

---

## 6. 前端开发任务

### 6.1 页面结构 `frontend/src/app/[locale]/(dashboard)/ip/`

```
ip/
├── page.tsx                      # 概览（未配置 → 引导冷启动）
├── setup/page.tsx                # 冷启动向导（ColdStartWizard）
├── clearance/page.tsx            # 商标可注册性初筛（WS 流式 + 免责盾 + 因素表）
├── fto/page.tsx                  # 专利 FTO 初筛（WS + 权利要求对照 + 故意侵权警告）
├── invention/page.tsx            # 发明披露初筛（WS + 三态）
├── infringement/page.tsx         # 侵权初步分析（IP 类型选择 + WS + 四态）
├── ip-clause/page.tsx            # 合同 IP 条款审查（上传/粘贴 + WS）
├── oss-review/page.tsx           # 开源许可证合规（部署模式 + 依赖列表 + WS）
├── enforcement/
│   ├── page.tsx                  # 维权信函列表（cease-desist/takedown 分 tab，按状态/期限分组）
│   └── [id]/page.tsx             # 信函详情（模式/对方尽调/草稿/发送门禁/对外版本）
├── reviews/
│   ├── page.tsx                  # 分析产出列表（6 类分 tab）
│   └── [id]/page.tsx             # 产出详情
├── portfolio/page.tsx            # 组合登记册（report 分桶 + add/update + audit）
└── settings/page.tsx             # 实践画像设置（customize）
```

### 6.2 关键页面
- **概览**：SetupStatusCard / QuickActions（清查/FTO/侵权/警告函）/ StatsCards / **RenewalDeadlineSummary**（近 90 天续展）/ RecentReviewsList / NotificationArea。
- **冷启动**：`ColdStartWizard`（镜像 `privacy` 向导），6 步，调 `ipApi.submitSetup`，服务端 materialize 后跳概览。**纯表单，非 WS。**
- **clearance / fto**：**顶部强制免责盾**（"初步检索，非法律意见，绝不下'可注册/可实施'结论"）→ 描述 → WS 流式 → 因素表（固有障碍/混淆因素 或 权利要求逐元素）+ 🟢🟡🔴 信号。fto 遇外观设计显示"已路由设计律师"提示并停止逐元素。
- **infringement**：先选 **IP 类型**（商标/著作权/专利/商业秘密）→ WS 流式 → 对应四态因素表 + 分类徽章（忽略/沟通/警告函/起诉）+ 若 🔴/🟠 显示"桥接到警告函/网络传播权通知"按钮。
- **enforcement（维权信函）**：先选 **类型**（侵权警告函 / 网络传播权通知）+ **模式**（发送/接收/回应/反通知）→ 建档(REST) → 起草(WS) → 展示**内部草稿（带工作成果抬头）** 与 **对外版本（去抬头）** 双栏 + **发送门禁核对清单**（必须全部勾选才能标记"已发送"）+ 对方尽调块 + 审计日志。
- **portfolio**：report 视图按 `next_deadlines` 紧急度分桶（🔴宽展/已失效 · ⏰≤30 · 🟠30-60 · 🟡60-90 · 🌐代理代管 · ❓不明）；add/update 表单；audit 体检报告。
- **oss-review / ip-clause / invention**：录入/上传 → WS 流式 → 结构化结果 + 详情存 reviews。

### 6.3 通用组件 `frontend/src/components/ip/`
`ClassificationBadge`（🟢🟡🔴 + 三态/四态）、`SeverityBadge`、`PreliminaryDisclaimer`（clearance/fto 免责盾）、`WillfulnessWarning`（fto/infringement）、`IpCategorySelector`（商标/著作权/专利/商业秘密）、`EnforcementModeSelector`（发送/接收/回应/反通知）、`EnforcementGate`（发送门禁核对清单）、`LetterDualView`（内部草稿/对外版本双栏）、`DueDiligenceBlock`、`ClaimMappingTable`（权利要求逐元素）、`RiskMatrix`（六维度/双轴）、`PortfolioDeadlineBadge`、`ReviewTypeTabs`、`NotificationArea`、`ColdStartWizard`、`ReviewerNote`（审阅备注区块）、`WorkProductHeader`（按 role × matter_type 4 分支）。

### 6.4 导航注册
- `components/layout/app-sidebar.tsx`：`navigation` 数组加 `{ name: t("ip"), href: ROUTES.IP, icon: Lightbulb }`（Lucide；或 `ScrollText`/`BadgeCheck`）
- `lib/constants.ts`：加 `IP: "/ip"` 等 ROUTES（IP_SETUP / IP_CLEARANCE / IP_FTO / IP_INFRINGEMENT / IP_ENFORCEMENT / IP_PORTFOLIO / IP_REVIEWS / IP_SETTINGS）
- i18n 文案（`messages/zh.json` + `en.json`）加 `ip` 顶层 key（zh 为主）

### 6.5 类型 `types/ip.ts`
镜像 `types/privacy.ts`：枚举（ReviewType / IpCategory / Classification / EnforcementMatterType / EnforcementMode / AssetType / UserRole / ModuleStatus）、实体接口（IpReview / IpEnforcement / IpPortfolio / IpProfile）、`IpWsMessage`（`{action, review_id?/enforcement_id?, ...}`）、`IpWsEvent` 联合类型。

### 6.6 API 客户端 `lib/ip.ts` + 代理 `app/api/ip/[[...path]]/route.ts`
`ipApi` 对象包 `apiClient`（GET/POST/PUT/upload）；catch-all 代理转发到 `/api/v1/ip/*`，从 cookie 取 `access_token` 注入 Bearer（照 privacy 代理，支持 multipart 以便种子文件/合同/依赖清单上传）。

### 6.7 聊天 Hook `hooks/use-ip-chat.ts`
镜像 `use-privacy-chat.ts`：WS URL `${getWsUrl()}/api/v1/ws/ip`，subprotocols `["access_token.${token}", "ip"]`；发送 `{ action, review_id?/enforcement_id?, prompt/payload }`；处理事件 `text_delta` / `tool_call` / `tool_result` / `final_result` / `complete` / `error`（+ `review_started`）。

---

## 7. 技能实现详解

### 7.1 技能分发（显式 action，无意图路由）
前端按用户选择的功能直接发对应 `action`（点「FTO 初筛」→ `action=fto`）。后端 `_SKILL_BY_ACTION` 校验后建 Agent。**不做关键词意图识别**——与 privacy/employment 一致，避免中文意图歧义与隐性兜底。

### 7.2 clearance（商标可注册性初筛）
**"初步检索，非法律意见"盾置顶（不可协商）**。流程：读画像（角色/管辖域/检索工具）→ 录入（商标名/商品服务/类别/管辖域/视觉风格）→ **固有障碍筛查**（通用名/描述性/欺骗性/地名/姓氏/不良影响/缺显著性/功能性，商标法§11，逐项 yes/no + 理由）→ **近似商标检索**（有检索工具则跑，无则明确"无数据库访问"）→ **混淆因素（商标法§57 + 商标审查指南）**（标识近似：形/音/义/整体印象；商品类似：类似商品表；相关公众注意力；在先商标强度/知名度；意图；实际混淆）→ 结构化因素表（每因素倾向：有利/不利/混合）→ **绝不下"不构成混淆/可注册"结论**。结果落 `ip_reviews(type=clearance, classification, severity)`。最低信心是"需律师"，非"可用"。

### 7.3 fto-triage（专利自由实施初筛）
**"非 FTO 意见"盾置顶**。流程：读画像 → 录入（产品/工艺/技术细节/管辖域/已知专利/上市时间）→ 有库则检索潜在阻碍专利 → 对 2–5 件最可能阻碍专利**按专利法§64「全面覆盖」做权利要求逐元素对照表**（每独立权项逐元素，标字面侵权/不侵权；再评等同侵权可能：手段/功能/效果三基本相同 + 禁止反悔限制）→ 列可能无效抗辩（专利法§22-23/§25，仅标签非意见）→ **故意侵权警告**（阅读本备忘录=知悉；未经律师建议继续=专利法§71 故意侵权，最高 5 倍赔偿；内部保密）。**外观设计立即路由设计律师**（§23"一般消费者观察"测试，不做逐元素，停止）。落 `ip_reviews(type=fto)`。

### 7.4 invention-intake（发明披露初筛）
读画像（专利代理师/管辖域/申请战略）→ **六维筛查**：①新颖性信号 ②创造性信号 ③可授权主题（专利法§2/§25 排除抽象/商业方法/诊断方法/动植物品种等）④**公开状态与时间**（已发表/销售/展示/代码库？中国宽限期 6 个月§24，远窄于美国 1 年——若境外申请需要，标 `时效紧急——宽限期 [日期] 届满`）⑤可检测性（可逆向？产品中可观察？或后端算法宜作商业秘密）⑥战略价值 vs 公司 IP 政策 → **三态**：推进（PURSUE，全面检索+律师审查）/ 调查（INVESTIGATE，回退发明人补充）/ 驳回（REJECT，注明原因）。**绝不说"可专利"**，说"通过初步筛查，值得检索+律师审查"。落 `ip_reviews(type=invention, classification)`。

### 7.5 infringement-triage（侵权初步分析，四态）
按 IP 类型分支，每态输出因素表 + **绝不下结论**：
- **商标**：混淆可能性（商标法§57，同 clearance 因素）+ 可选驰名淡化§13 + 虚假宣传反法§6。
- **著作权**：权属（职务作品§18？）+ 登记状态（中国非起诉前提，但登记=初步证据）+ 接触+实质相似 + 合理使用§24（穷尽列举）+ 通知-删除（《条例》§14-17 + 电商法§42-43 + 避风港）。
- **专利**：**外观设计先早分流→设计律师**；发明/实用新型走权利要求逐元素§64（同 fto 结构）+ 等同 + 无效抗辩 + 赔偿态势§71。
- **商业秘密**：三要件（秘密性/价值性/保密措施反法§9）+ 侵权行为（不正当手段/违反保密义务/教唆帮助）+ **前员工事实模式** + 反向工程抗辩。
**共同关口**：若 🔴/🟠 → 桥接 `cease-desist`（发送）或 `takedown`（著作权）；但不自动起草，由审批人决定是否发送在战略上合理。落 `ip_reviews(type=infringement, ip_category, classification)`。

### 7.6 ip-clause-review（合同 IP 条款审查）
两步：①**固有缺陷盾**（若本应从对方受让工作成果 IP：现在式转让语言"特此转让"而非将来式"同意转让"？范围？**著作人身权放弃**著作权法§10，中国不可转让但可承诺不行使？进一步协助条款？🔴 缺失则"此缺口数年后会在并购尽调中暴露，签前修复"+ 替换语言）②**逐条审计**（转让/归属/改进/背景前景 IP/许可授予/范围/保证/赔偿/人身权放弃/开源声明/商标使用/保密）：逐条 plain English 概述 + 市场惯例 + 你的姿态 + 严重性🔴🟠🟡🟢 + 为何重要 + 替换语言（最小编辑优先）+ 歧义标 `[需审查]` 双解释。**一致性检查**（许可授予 vs 范围、保证 vs 许可 IP、赔偿 vs 授予权利、终止回收）。**管辖标记**（人身权不可放弃、隐含许可风险、AI 生成内容可版权性——北京互联网法院案例，演进中）。落 `ip_reviews(type=ip_clause)`。

### 7.7 oss-review（开源许可证合规）
范围（依赖清单/单包/拟开源的自有代码）→ **部署模式决定触发何种义务**（SaaS：AGPL 网络使用 + 可见界面署名；二进制分发：GPL 各级/LGPL 库级/MPL 文件级；仅内部：多数 copyleft 不触发，AGPL 仍触发；嵌入固件：GPL 最难）→ **逐包分类**（读**实际 LICENSE 文件**非元数据：宽松 MIT/BSD/Apache-2.0；弱 copyleft LGPL/MPL/EPL；强 copyleft GPL/AGPL/OSL/EUPL；公有领域 CC0/Unlicense——中国未定；**非 OSI** SSPL/BUSL/Commons Clause/Elastic——明示非开源；**未知则停，绝不默认宽松**）→ 冲突检查（传递 copyleft / 许可证变更史如 Redis/Mongo/Elastic / 双许可路径）→ 义务映射（按部署模式逐包列具体义务，每项打勾）→ **可否发布分级**（强 copyleft 进二进制=🔴；AGPL 暴露 API 的 SaaS=🔴；商业产品用非 OSI=🔴；宽松+署名到位=🟢）→ 若自有代码发布：发布检查清单（LICENSE/NOTICE/第三方文本/依赖兼容）。落 `ip_reviews(type=oss, classification)`。

### 7.8 cease-desist（侵权警告函，双模式）
- **发送**：①识别权利（商标注册/著作权登记/专利）②识别侵权（谁/什么/何处/自何时/证据）③识别关系（竞争者/经销商/前员工/陌生人）④识别请求（停止/披露/销毁/赔偿/转让）⑤按维权姿态校准（激进/适度/保守）⑤.5 **对方尽调**（实体/资源/IP 组合/诉讼史/是否聘律/反诉风险）⑥按中国实务起草（发件/收件/事由/权利描述/侵权事实/法律依据§57/§63 等/请求/时限/后果/证据保全/保留权利/签署）⑦**发送前 LOUD GATE**（权利有效？主张成立？请求比例适当？授权人签署？对方尽调已呈现？）。
- **接收**：①解析来函（发件/收件/主张权利/被诉行为/依据/要求/威胁/语气）②评估对方主张（权利有效？事实基础？是否过宽？时效？）③评估己方敞口（是否侵权？能否易停？对方可信？）④**四选项树**（A 遵从 / B 谈判 / C 反制：确认不侵权之诉/无效宣告/不侵权抗辩 / D 忽略）。
风险：确认不侵权之诉反诉、过宽警告函触发反法§17 惩罚性赔偿/不正当竞争反制。落 `ip_enforcement(matter_type=cease_desist, mode)`；对外信函去抬头。非律师发送前出 1 页简报。

### 7.9 takedown（网络传播权通知，三模式）
- **发送**：①识别作品（登记状态）②识别侵权内容（URL/平台/证据）③**合理使用四因素门（著作权法§24，穷尽列举；"可能合理使用"则停并升级律师）**④确认善意与授权 ⑤按《条例》§14 + 电商法§42 起草通知（权利人联系/作品描述/侵权 URL/损害证明）⑥**LOUD GATE**（通知是真实法律陈述；错误通知担责《条例》§24/电商法§42 反赔）。
- **回应**：解析收到通知 → 评估（许可/合理使用/通知瑕疵/平台是否依§15/§17 与电商法程序履行）→ 四选项树。
- **反通知**：确认删除由通知触发（非平台政策）→ 善意相信删除有误 → 按《条例》§16 + 电商法§43 起草反通知（用户联系/作品 URL/不侵权声明/善意）→ **注意 15 个工作日**起诉等待期后平台须恢复。
落 `ip_enforcement(matter_type=takedown, mode, response_deadline=15工作日)`；对外去抬头。

### 7.10 portfolio（注册续展跟踪，非 Agent）
REST CRUD + 算术，四模式：`--report`（默认 90 天窗口，分桶）/ `--add`（录入资产）/ `--update`（缴费/同步状态）/ `--audit`（体检：宽展项、pending>2 年、**商标使用状态 撤三风险商标法§49**、所有权一致性、24 月期限预测）。每次 report/audit **按 `deadline_rules` 从关键日期重算下一期限**（不信任已存日期，规则可能变）。状态：upcoming(>90d)/due_soon(30-90d)/overdue(宽展内)/grace(宽展，加费)/lapsed(过宽展，丧失)/filed(本周期已缴)。**每份输出末尾固定**："计算的到期日仅供参考。提交或缴费前对照 CNIPA 商标查询/专利公告/WIPO 核实。记录但错误的到期日比未记录更糟。"

### 7.11 cold-start-interview（冷启动）
service 状态机 + 前端向导（§5.2 任务 2.4、§6.2）。保真 ZH 的"快速/完整"分叉、对真实回答暂停等待、即时核实用户陈述的法律事实、绝不静默缺口、占位符未填则每个技能停下引导设置。

### 7.12 customize（修改画像）
不单独建 Agent；映射为**设置页** + `PUT /ip/profile`。按节分组（IP 业务领域/维权姿态/发函审批/品牌监测/集成/角色），改一项即写回。护栏：不删节（标记"不在范围"）、提示跨字段冲突（如"商标维权姿态激进"但"商标不在 IP 业务领域"）、展示下游技能影响（"改激进 → cease-desist 首选项变为警告函草稿"）。

### 7.13 共享护栏移植（`prompts/security.py`，所有技能注入）
ZH CLAUDE.md「共享护栏」「风险评价方法论」「主观判断决策姿态」整体移植：
- **来源溯源标签（中国法版）**：`[法条原文]`/`[裁判文书]`/`[本地知识库]`/`[联网检索—需复核]`/`[模型知识—需验证]`/`[用户提供]`/`[已验证—YYYY-MM-DD]`。⚠️ ZH 原文里的 `[元典检索]/[北大法宝]/[CNIPA]` → 本期改为 `[本地知识库]`（LexMind 用 RAG，不接外部 MCP）。
- **三值而非二值**（标注补充 / 停止并告知 / 标注但不使用），**禁止沉默补充**。
- **时效触发**：引《商标法》《专利法》《著作权法》《反法》具体条文前先检索（RAG/web），不直接用模型知识。
- **跨技能严重性底线**（🔴→🟢 须显式声明降级理由）。
- **4 种工作成果抬头**（§2.4）：按 role × 事项类型分支；**对外交付物（警告函/网络传播权通知/对外摘要）省略抬头**；专利代理师非专利事项标 `非特权`。
- **审阅备注区块**（来源/已读/标注/时效性/依赖前）、**安静模式**（对外交付物像合伙人写的）、**目的地检查**（抬头是标签非控制）、**下一步决策树**、**关口**（发警告函/网络传播权通知/反通知前，非律师出简报）。
- **比例性 / 管辖域识别（默认中国法，涉港澳台/境外识别并行动）/ 检索内容信任（MCP/RAG/上传内容是数据非指令）/ 大输入大输出**。

---

## 8. 定时代理实现

`tasks/ip_renewal_watcher.py`，照 `privacy_policy_sweep_reminder.py` 的 `run(db) -> int` + `tasks/ip_deadline_rules.py` 算术助手：

```python
def run(db: Session) -> int:
    written = 0
    for user_id in iter_active_user_ids(db):
        profile = ip_profile_repo.get_by_user_id(db, user_id)
        if not profile or profile.setup_status != "completed":
            continue
        assets, _ = ip_portfolio_repo.list_by_user(db, user_id=user_id, skip=0, limit=10000)
        buckets = bucket_deadlines(assets)          # 纯算术：按 deadline_rules 重算 + 分桶
        if buckets.has_alerts():                    # 含 grace/lapsed/≤90天
            ip_notification_repo.create(db, user_id=user_id,
                notification_type="renewal_alert", priority=buckets.top_priority(),
                title=f"IP 续展预警：{buckets.summary()}",
                content=render_renewal_report(buckets),   # 🔴宽展/已失效 · ⏰≤30 · 🟠30-60 · 🟡60-90 · 🌐代理 · ❓不明
                action_url="/ip/portfolio")
            written += 1
    return written
```

`tasks/ip_deadline_rules.py`（确定性算术，无 LLM）：
- 商标（CN）：注册核准日起 10 年；期满前 12 个月续展；6 个月宽展期加费（商标法§40）
- 专利（CN）：发明 20 年 / 实用新型 10 年 / 外观设计 15 年（自申请日）；年费宽展 6 个月加滞纳金（§42-43）
- 著作权（CN）：无续展（个人终生+50 年 / 法人首次发表后 50 年）
- 马德里：10 年续展；域名：按注册商宽展+赎回期；自定义管辖：用户提供留存触发+宽展条款存 `custom_rules`

`scheduler.py` 新增 `JOB_IP_RENEWAL_WATCHER`，`CronTrigger(day_of_week="mon", hour=9, minute=47)`，`replace_existing=True`。**不调 LLM。** 无到期事项也发简短"无事报告"（"静默通过看起来与损坏的定时任务一模一样"）。

---

## 9. 法条检索与知识库前置条件

- **复用** `agents/tools/law_tools.py` 的 `search_law` / `get_law_article`（Qdrant + BGE-zh）。新增 `research_ip_rules(topic, regime)` 薄封装：先读画像 `ip_scope`/`registration_jurisdictions`，再 RAG 检索，按 §7.13 标注来源。
- **⚠️ 前置条件（开发前确认）**：RAG 语料须包含 **《商标法》《专利法》《著作权法》《反不正当竞争法》** 及关键司法解释（审理商标民事纠纷案件解释、侵犯专利权纠纷案件解释 I–III、审理著作权民事纠纷案件解释、反不正当竞争司法解释）+ **《信息网络传播权保护条例》《电子商务法》《专利代理条例》**。若缺，按 `docs/development/guides/add-rag-source.md` 先行入库，否则 `research_ip_rules` 命中率不足、技能将频繁"禁止沉默补充"停下。
- **移植 references**：把 `claude-for-legal-zh/ip-legal/references/ip-core-rules.md`（4 法 58 条基线 + 司法解释要点，截至 2026-05-14）作为模块参考数据（照 employment 的 `references/labor-core-rules.md` 与 privacy 的 `references/pipil-core-provisions.md` 处理）——放 `backend/app/agents/ip/references/ip-core-rules.md` 供提示词/工具引用。

---

## 10. 开发排期

### 总工期：约 4–5 周（比 privacy 略多——5 张表 vs 4、8 action vs 7、+ portfolio 续展算术 + 4 抬头分支）

```
Week 1  数据层 + 技能引擎起步
  D1 迁移(2文件,幂等守护) + 模型(5)    D2 Repository + Schema
  D3 服务层(profile + cold-start 状态机)    D4 Agent工厂+Deps + 提示词(security 含4抬头, clearance, fto)
  D5 提示词(invention, infringement 四态)

Week 2  技能引擎完成 + API
  D1 提示词(ip_clause, oss, cease_desist 双模, takedown 三模)    D2 工具(profile/review/enforcement/portfolio/law)
  D3 REST(~16端点, portfolio report/audit 算术) + DI/注册/挂载    D4 WS(8 action, 预建行)    D5 deadline_rules + cron + API 集成测试

Week 3  前端
  D1 冷启动向导 + clearance/fto 页(免责盾 + 权利要求表)    D2 invention/infringement(四态) + ip-clause/oss 页
  D3 enforcement 列表/详情(双模 + 发送门禁 + 双栏信函)    D4 portfolio(分桶 + audit) + reviews 列表/详情 + 设置页
  D5 导航/代理/Hook/类型 + 通用组件(免责盾/故意侵权/RiskMatrix/WorkProductHeader 4分支)

Week 4  联调 + 测试 + 部署
  D1-2 全链路联调(10 技能手测 + 冷启动)    D3 集成测试(tests/ip/: repo/service/scheduler/migrations)
  D4-5 Bug 修复 + 部署
```

### 里程碑
| 里程碑 | 目标 | 交付物 |
|--------|------|--------|
| M1 数据层就绪 | W1 D2 | 5 表 + Repo + Schema（迁移幂等过 test_migrations） |
| M2 冷启动可运行 | W1 D3 | cold-start 状态机贯通 |
| M3 维权信函可运行 | W2 D1 | cease-desist/takedown WS 技能手测通过（多模式 + 发送门禁 + 去抬头） |
| M4 全部 Agent 技能可用 | W2 D4 | 8 个 WS action 手测通过 |
| M5 API + cron 完成 | W2 D5 | REST + WS + portfolio 算术 + 续展 cron |
| M6 前端完成 | W3 D5 | 所有页面可用 |
| M7 验收通过 | W4 D5 | 全功能 + tests/ip 绿 |

---

## 11. 附录：关键文件清单

### 11.1 需读取的源文件（claude-for-legal-zh，**以 -zh 为准**）
`~/.claude/plugins/marketplaces/claude-for-legal-zh/ip-legal/`：`CLAUDE.md`（画像模板 + 共享护栏 + 风险方法论 + **4 抬头**）、`references/ip-core-rules.md`、`agents/ip-renewal-watcher.md`、`skills/{cold-start-interview,customize,clearance,fto-triage,invention-intake,infringement-triage,ip-clause-review,oss-review,cease-desist,takedown,portfolio}/SKILL.md`。

### 11.2 需新建的后端文件
```
backend/app/
├── agents/ip/
│   ├── __init__.py  agent.py  deps.py
│   ├── tools/  (_validators, profile_tools, review_tools, enforcement_tools, portfolio_tools, law_tools)
│   ├── prompts/ (security, clearance, fto_triage, invention_intake, infringement_triage,
│   │             ip_clause_review, oss_review, cease_desist, takedown)
│   └── references/ (ip-core-rules.md  ← 移植)
├── api/routes/v1/  ip.py  ip_ws.py
├── db/models/  ip_profile.py  ip_review.py  ip_enforcement.py  ip_portfolio.py  ip_notification.py
├── repositories/  ip_profile_repo.py  ip_review_repo.py  ip_enforcement_repo.py  ip_portfolio_repo.py  ip_notification_repo.py
├── schemas/ip/  __init__.py _json.py profile.py cold_start.py review.py enforcement.py portfolio.py notification.py
├── services/  ip_profile_service.py  ip_cold_start_service.py  ip_review_service.py
│              ip_enforcement_service.py  ip_portfolio_service.py  ip_notification_service.py
├── tasks/  ip_renewal_watcher.py  ip_deadline_rules.py
└── alembic/versions/  (2 个迁移文件，幂等守护)
更新：db/models/__init__.py  api/deps.py  api/routes/v1/__init__.py  scheduler.py
```

### 11.3 需新建的前端文件
```
frontend/src/
├── app/[locale]/(dashboard)/ip/  (page + setup + clearance + fto + invention + infringement + ip-clause
│                                  + oss-review + enforcement[/id] + reviews[/id] + portfolio + settings)
├── app/api/ip/[[...path]]/route.ts
├── components/ip/  (ClassificationBadge, SeverityBadge, PreliminaryDisclaimer, WillfulnessWarning,
│                    IpCategorySelector, EnforcementModeSelector, EnforcementGate, LetterDualView,
│                    DueDiligenceBlock, ClaimMappingTable, RiskMatrix, PortfolioDeadlineBadge,
│                    ReviewTypeTabs, NotificationArea, ColdStartWizard, ReviewerNote, WorkProductHeader)
├── hooks/use-ip-chat.ts
├── lib/ip.ts
└── types/ip.ts
更新：components/layout/app-sidebar.tsx  lib/constants.ts  messages/{zh,en}.json
```

### 11.4 Required Verification（每阶段完成前）
后端：`uv run ruff check . --fix && uv run ruff format . && uv run ty check && uv run pytest`（含 `tests/ip/` 与 `test_migrations`）。
前端：`bun run lint && bun test`。
端到端手测：① 冷启动向导贯通写画像；② 未配置 LLM 时 WS 报 `llm_not_configured`（不兜底）；③ 8 个 WS action 各跑一次（重点：cease-desist/takedown 多模式 + 发送门禁 + 对外去抬头、fto/infringement 外观设计路由、clearance/fto 免责盾、infringement 四态、严重性底线）；④ portfolio add → report 算术分桶 → audit；⑤ cron 手动触发产出续展预警通知；⑥ 设置页改一项画像写回生效；⑦ 专利代理师角色下非专利事项抬头标 `非特权`。

---

## 设计决策小结（供审阅）

1. **法域 = 中国法**（商标法/专利法/著作权法/反法 + 信息网络传播权保护条例/电商法/专利代理条例）：源为 `claude-for-legal-zh` 中文本地化版，非英文 DMCA/35 U.S.C. 上游。复用现有中文 RAG。
2. **范围 = 用户列的 10 技能 + customize(设置页) + 冷启动基础设施**；`matter-workspace` 延后（不在 10 技能内 + 照 privacy/employment 先例用实践级上下文）。
3. **架构 = 逐项镜像 privacy**（最新同构样板）：传输层三分（WS 显式 action / REST CRUD / cron 纯算术）、独立 profile 表（复制非共享）、迁移幂等守护、绝不兜底。
4. **数据模型 = 5 张表**（profile / reviews 统一 6 类 / enforcement 信函生命周期 / portfolio 注册组合 / notifications）——比 privacy 多 portfolio，因 IP 有续展 cron 消费的登记册。
5. **IP 独有保真重点**：①专利代理师特权 4 种工作成果抬头（《专利代理条例》§17，按 role×事项分支）②外观设计早分流给设计律师（§23 不同测试）③不撰写专利权利要求 ④对外信函去抬头 + 发送前 LOUD GATE（系统只产草稿不发送）⑤clearance/fto "初步非意见"免责盾 ⑥专利法§71 故意侵权警告 ⑦多模式技能（cease-desist 双向 / takedown 三模 / infringement 四态）⑧portfolio 续展期限纯算术 cron。

*文档生成时间：2026-06-10（v1.0）*
*基于 claude-for-legal-zh 知识产权模块 + LexMind 现行架构*
*架构逐项镜像 privacy（隐私数据）模块的真实实现*
