# 争议解决模块（Litigation-Legal）开发计划

**版本：** 1.0
**日期：** 2026-06-12
**目标：** 将 claude-for-legal-zh 的**争议解决（诉讼）模块**完整融入 LexMind，作为第 6 个法律模块，**严格复用 ip（知识产权）/ privacy（隐私数据）/ employment（劳动用工）/ corporate（公司并购）已验证的真实架构模式**。

---

## Context（为什么做这件事）

LexMind 已落地 5 个法律模块（commercial → corporate → employment → privacy → ip），均遵循同一套"四层移植 + 传输层三分"的真实架构（ip 模块已合并落地）。本次新增**争议解决模块**（第 6 个），把 claude-for-legal-zh 的 `litigation-legal` 插件的能力，通过 LexMind 的产品形态（后端 API + Web UI）交付给中国律师与法务人员。

**最关键的事实澄清（务必先读）：**

- 真正的移植源是 **`~/.claude/plugins/marketplaces/claude-for-legal-zh/litigation-legal/`**（中文本地化版，作者"陈石 律师"）。
- 它覆盖的是**中国法**：**《民事诉讼法》《最高人民法院关于适用〈民事诉讼法〉的解释》《民事诉讼证据规定》**、执行程序及配套司法解释、**《民法典》诉讼时效（§188 / §195）**、**《律师法》§38**（律师保密义务）。**不是** 美国 FRCP / FRE / attorney work product 制度。
  - 证据三性审查 / 非法证据排除 = **民诉法§66-67 + 民诉法解释§104-106**
  - 法院调查令 / 协查 = **民诉法§67 + 民诉法解释§94-96** + 各省高院律师调查令实施办法（地方差异大）
  - 证据保全 = **民诉法§81、§84 + 民诉法解释§94-99**
  - 诉讼时效中断 = **民法典§188、§195**；申请执行时效 = **2 年**
  - 审限 = 一审普通程序 6 个月（可延长）/ 简易程序 3 个月 / 小额诉讼 2 个月；上诉期 判决 15 日 / 裁定 10 日；举证期限 不少于 15 日；管辖权异议 答辩期内（15 日）提出
- ⚠️ 不要使用英文上游缓存（含 FRCP / privilege / deposition 的美式制度）。一切以 `claude-for-legal-zh` marketplace 为准。
- 因为是中国法，**可直接复用 LexMind 现有中文法条 RAG**（`search_law` / `get_law_article`），与 employment / privacy / ip 一致。

**litigation 模块相对 ip 的两处结构性新增（决定本期 6 表而非 5 表）：**

1. **案件（matter）是核心实体**，且带**事件流时间线**（源插件的 `history.md` 逐案事件追加 + `_log.yaml` 逐案状态）→ 独立 `litigation_matter_events` 表（ip / privacy 都没有的事件子表）。
2. **律师函（demand）有 intake / draft / received 双向生命周期**（信函起草、发送门禁、来函分流）→ 独立 `litigation_demands` 表（类比 ip 的 `ip_enforcement`）。

**与 ip 的关键差异点：**

- 工作成果抬头只有 **2 种**（律师 / 非律师），**无**专利代理师特权的 4 抬头；但有 litigation 独有的**中国法保密说明**（"律师工作成果"是美国 FRCP 26(b)(3) 概念，中国法律体系无对应的独立保护制度——与外部律师沟通享更强保密，纯内部分析备忘录保密性相对较弱；律师法§38、民诉法§67）。
- 多了 **"五组内容分离"** 诉讼文书编辑纪律（证据列举 / 质证意见 / 证据认定 / 查明事实 / 争议焦点分析，后一组不能比前一组走得更远）。

**最终效果**：争议解决模块的后端 Agent / 提示词 / 工具 / 工作流**完全遵循** `claude-for-legal-zh` 的 ZH `SKILL.md` 定义，LexMind 只提供用户友好的前端 UI 和把"配置文件 CLAUDE.md"换成"数据库画像表"的产品化封装。

---

## 目录

1. [总体目标与范围](#1-总体目标与范围)
2. [模块全景（技能按传输层三分）](#2-模块全景技能按传输层三分)
3. [复用既有架构（镜像 ip / privacy）](#3-复用既有架构镜像-ip--privacy)
4. [数据模型设计](#4-数据模型设计)
5. [后端开发任务](#5-后端开发任务)
6. [前端开发任务](#6-前端开发任务)
7. [技能实现详解](#7-技能实现详解)
8. [定时代理实现](#8-定时代理实现)
9. [法条检索与知识库前置条件](#9-法条检索与知识库前置条件)
10. [开发排期](#10-开发排期)
11. [附录：关键文件清单](#11-附录关键文件清单)
12. [设计决策小结](#12-设计决策小结供审阅)

---

## 1. 总体目标与范围

### 1.1 目标

将 `claude-for-legal-zh` 争议解决模块的 **17 个核心技能 + customize + 冷启动基础设施** 移植到 LexMind：

- 用户访问「争议解决」模块时，若未配置则引导冷启动访谈
- 配置完成后，用户可通过前端界面使用全部技能
- 后端 Agent / 提示词 / 工具 **完全遵循** ZH `SKILL.md`（中国法实质内容 + 共享护栏 + 多模式技能理念）
- **架构上逐项镜像 ip 模块**（最新、最近的同构样板；ip 又镜像 privacy → employment → corporate）
- 1 个定时代理（docket-watcher 周度案件进度监控，纯算术，无 LLM）

### 1.2 范围

**包含（全量 17 个核心技能 + 必要基础设施）：**

| 技能 | 中文 | 落地形态 |
|------|------|---------|
| cold-start-interview | 冷启动访谈 | 冷启动**服务状态机** + 前端向导（**非 Agent**） |
| matter-intake | 案件登记 | REST CRUD（结构化录入 + 冲突门禁） |
| matter-update | 案件进展记录 | REST CRUD（事件流追加） |
| matter-close | 案件结案归档 | REST CRUD（状态更新，保留不删） |
| matter-briefing | 单案深度简报 | WS Agent |
| portfolio-status | 案件组合概览 | REST（聚合算术，**非 Agent**） |
| demand-intake | 律师函委托登记 | REST 建档 |
| demand-draft | 律师函起草 | REST 建档 + WS Agent 起草 |
| demand-received | 来函分流 | REST 建档 + WS Agent 分析 |
| subpoena-triage | 调查令/协查分流 | REST 建档 + WS Agent 分析 |
| legal-hold | 证据保全通知 | REST 状态 + WS Agent 起草 |
| chronology | 大事记/时间线构建 | WS Agent |
| claim-chart | 要件分析表 | WS Agent |
| oc-status | 外部律师进度询问函 | WS Agent |
| brief-section-drafter ★ | 书状段落起草 | WS Agent |
| deposition-prep ★ | 庭前质证准备 | WS Agent |
| privilege-log-review ★ | 证据三性审查 | WS Agent |
| customize | 修改画像某一项 | 前端**设置页** + `PUT /litigation/profile`（非 Agent） |

> ★ = overview.md 未列、但源插件已有完整 SKILL.md 的诉讼核心工具，本期纳入（用户已确认全量 17）。

**明确延后（不在本期）：**

- `matter-workspace`（多客户事项工作区）— 照 ip / privacy / employment 先例，企业法务默认隐藏 matter 隔离概念，本期统一用 **practice-level（实践级）上下文**，`matters` 以 `user_id` 归属。源插件 CLAUDE.md 中此节默认"已启用：✗"（企业法务用户不可见）。后续如需私人执业 / 律所多客户隔离再引入。
- **元典 / 北大法宝 / 裁判文书网 / 飞书 MCP 检索** — 本期用 LexMind 现有 RAG（`search_law`）替代；ZH 提示词里的 `[yuandian检索]` 标签改为 `[本地知识库]`（见 §7.18、§9）。
- **外部 MCP 集成**（企业网盘 / SharePoint / 飞书文档 / 即时通讯 / Gmail 草稿）— 本期不接；冷启动「可用集成」一节统一标记为不可用，按 ZH 的降级路径处理（输出存库、通知内嵌、oc-status 仅产草稿不发）。
- **docket-watcher 的"每日扫描"**（14 天内开庭 / 严重案件）— 本期先做**周度**（照既有 cron 惯例），每日扫描作为后续增强。

### 1.3 与 commercial / corporate / employment / privacy / ip 的关系

| 维度 | commercial | corporate | employment | privacy | ip | **litigation（本期）** |
|------|-----------|-----------|------------|---------|----|----------------------|
| 路由前缀 | `/commercial` | `/corporate` | `/employment` | `/privacy` | `/ip` | `/litigation` |
| module_configs.module_name | `commercial-legal` | `corporate-legal` | `employment-legal` | `privacy-legal` | `ip-legal` | `litigation-legal` |
| 独立 profile 表 | `commercial_profiles` | `corporate_profiles` | `employment_profiles` | `privacy_profiles` | `ip_profiles` | `litigation_profiles`（新建，**非共享**） |
| Agent 工厂 | `agents/commercial/` | `agents/corporate/` | `agents/employment/` | `agents/privacy/` | `agents/ip/` | `agents/litigation/agent.py`（镜像 ip） |
| WS 端点 | `/ws/commercial` | `/ws/corporate` | `/ws/employment` | `/ws/privacy` | `/ws/ip` | `/ws/litigation` |
| 定时任务 | renewal_watcher, deal_debrief, playbook_monitor | dataroom_watcher | leave_tracker | policy_sweep_reminder | ip_renewal_watcher | **docket_watcher** |
| 前端页面 | `/commercial/*` | `/corporate/*` | `/employment/*` | `/privacy/*` | `/ip/*` | `/litigation/*` |

---

## 2. 模块全景（技能按传输层三分）

**核心原则（来自 ip / privacy / employment 真实代码）：** REST 端点**全部是 CRUD / 聚合算术（纯 service 调用）**；所有 Agent 驱动的技能**只走 WebSocket**，前端用显式 `action` 字段选择技能，**后端不做 LLM / 关键词意图路由**（见 `privacy_ws.py` / `ip_ws.py`："skill chosen explicitly by the client — no LLM intent routing"）。判断标准是：**技能是否需要调用 LLM 生成 / 推理内容？** 是→WS Agent；否（纯 CRUD / 算术）→REST；无 LLM 的周期任务→cron。

### 2.1 技能 → 传输层映射矩阵

| # | 技能 | 传输层 | 入口 | 落库表 |
|---|------|--------|------|--------|
| 1 | cold-start-interview | **REST**（service 状态机）+ 前端向导 | `POST /litigation/setup` | module_configs → litigation_profiles |
| 2 | customize | **REST** | `PUT /litigation/profile` | litigation_profiles |
| 3 | matter-intake | **REST** CRUD | `POST /litigation/matters` | litigation_matters |
| 4 | matter-update | **REST** CRUD | `POST /litigation/matters/{id}/events` | litigation_matter_events |
| 5 | matter-close | **REST** CRUD | `POST /litigation/matters/{id}/close` | litigation_matters（status=closed） |
| 6 | portfolio-status | **REST** 聚合算术 | `GET /litigation/matters/portfolio` | 读 litigation_matters |
| 7 | matter-briefing | **WS** `action=matter_briefing` | `/ws/litigation` | litigation_analyses（matter_briefing） |
| 8 | demand-intake | **REST** 建档 | `POST /litigation/demands` | litigation_demands |
| 9 | demand-draft | **WS** `action=demand_draft` | `/ws/litigation` | litigation_demands（回写草稿） |
| 10 | demand-received | **REST** 建档 + **WS** `action=demand_received` | `POST /litigation/demands` → `/ws` | litigation_demands（mode=receive） |
| 11 | subpoena-triage | **REST** 建档 + **WS** `action=subpoena_triage` | `POST /litigation/analyses` → `/ws` | litigation_analyses（subpoena_triage） |
| 12 | legal-hold | **REST** 状态 + **WS** `action=legal_hold` 起草 | `/ws/litigation` | litigation_analyses（legal_hold） |
| 13 | chronology | **WS** `action=chronology` | `/ws/litigation` | litigation_analyses（chronology） |
| 14 | claim-chart | **WS** `action=claim_chart` | `/ws/litigation` | litigation_analyses（claim_chart） |
| 15 | oc-status | **WS** `action=oc_status` | `/ws/litigation` | litigation_analyses（oc_status） |
| 16 | brief-section-drafter ★ | **WS** `action=brief_section` | `/ws/litigation` | litigation_analyses（brief_section） |
| 17 | deposition-prep ★ | **WS** `action=deposition_prep` | `/ws/litigation` | litigation_analyses（deposition_prep） |
| 18 | privilege-log-review ★ | **WS** `action=privilege_log` | `/ws/litigation` | litigation_analyses（privilege_log） |
| 19 | docket-watcher（进度监控） | **cron**（纯算术） | scheduler job | litigation_notifications |

WS `action` 合计 **11 个**：`matter_briefing / demand_draft / demand_received / subpoena_triage / legal_hold / chronology / claim_chart / oc_status / brief_section / deposition_prep / privilege_log`。
`litigation_analyses` 的 `analysis_type` 合计 **9 种**（demand_draft / demand_received 写 `litigation_demands`，不写 analyses）：`matter_briefing / chronology / claim_chart / subpoena_triage / legal_hold / oc_status / brief_section / deposition_prep / privilege_log`。

### 2.2 技能依赖关系

```
cold-start-interview ──写入──> litigation_profiles（实务画像 / CLAUDE.md 等价物，按执业角色分支）

所有 WS Agent 技能 ──读取──> litigation_profiles（前置条件；未配置则 /status 引导冷启动）
所有 WS Agent 技能 ──若未配置 LLM──> 报错 llm_not_configured（绝不兜底）

【案件中枢】
matter-intake(REST) ──冲突门禁(三路径)──> 建 litigation_matters + 播种首条 event
matter-update(REST) ──事件类型 + 重要性触发──> 追加 litigation_matter_events（含 deadline 事件）
matter-briefing(WS) ──冲突门禁(代号必须存在) + 陈旧度检查──> 综合 matter + events 生成简报
matter-close(REST) ──非律师门禁──> status=closed + outcome/lessons（保留不删）
portfolio-status(REST) ──聚合算术──> 风险分布 / 期限 / 陈旧 / 7 类异常

【律师函纵队】
demand-intake(REST) ──8 核心 + 5 策略块──> 建 litigation_demands(mode=send, status=intake)
demand-draft(WS) ──发送前 7 项 LOUD GATE──> 回写 letter_draft(带抬头) + outbound_letter(去抬头)
demand-received(REST 建档 + WS) ──实质理由评估 + 跨案检索──> 四选项树(遵从/谈判/反制/忽略)

【程序触发文件】
subpoena-triage(REST 建档 + WS) ──步骤0 前置规则研究──> 5 分类 + 异议框架；监察/刑事→上报
legal-hold(REST 状态 + WS) ──issue/refresh/release──> 起草保全通知 + 写 next_refresh（喂 docket-watcher）

【分析产出】
chronology(WS) ──保密门 + 逐文件提取 + 按理论标重要性──> 大事记（进攻性 vs 防守性）
claim-chart(WS) ──"草案非认定"盾 + 逐要件对照 + 缺口优先──> 要件分析表
brief-section(WS) ──五组内容分离 + 理论一致性 + 逐字引用──> 书状段落草案
deposition-prep(WS) ──按证人立场分支 + 不预测答案──> 庭前提纲 + 证据列表
privilege-log(WS) ──三性审查 + 三态保守(宁多勿少)──> 证据可采性意见
oc-status(WS) ──按事务所风格──> 外部律师状态请求函草稿（仅草稿不发）

docket-watcher(cron) ──纯算术：扫活跃 matters 的 deadline 事件 + legal_hold next_refresh，按审限规则重算，分桶预警──> 写 litigation_notifications（不调 LLM）
```

### 2.3 多模式技能保真（本模块的灵魂之一）

诉讼天然是双方 / 多向的，多个技能保留**模式分支**，必须保真移植：

- **demand-received（来函分流）— 收悉对方律师函**
  - 解析来函 → 实质理由评估（权利有效？事实基础？是否过宽？时效？）→ 己方敞口 → **四选项树**（A 实质回复 / B 暂搁观察 / C 和解谈判 / D 不回复 + 证据保全）。注意诉讼时效中断（民法典§195）。
- **subpoena-triage（调查令 / 协查）— 五分类分支**
  - 法院调查令（民诉法§67、解释§94-96）/ 律师调查令（各省高院实施办法，地方差异大）/ 行政协查 / 证人出庭通知 / **监察或刑事侦查（→ 立即上报，不自行处理）**。每类：范围 / 负担 / 保密分析 + 异议框架 + 合规方案 + 期限。
- **legal-hold（证据保全）— 三态生命周期**
  - `issue`（首次签发，范围 / 保管人 / 系统）/ `refresh`（6 个月定期刷新，确认范围变更）/ `release`（解除，留存指令）。每次写 `result_json` 的 `hold_status` + `next_refresh`（喂 docket-watcher）。
- **当事人角色分支（原告 / 被告 / 兼顾）** 贯穿 demand / chronology / claim-chart / deposition-prep / matter-intake：
  - 原告视角：风险校准围绕标的额 / 投入 / 时效；律师函是主张文件；证据收集是进攻性的；claim-chart 证明构成要件。
  - 被告视角：风险校准围绕败诉敞口 / 准备金 / 和解权限 / 保险；律师函是接收分流的；证据收集是防守性的；claim-chart 否定构成要件。

每个多模式技能：**自动识别模式；不明确时问一次**。落库 `litigation_demands.mode` / `litigation_analyses.classification`。

### 2.4 风险量表双映射（litigation 独有，对应 ip 的工作成果抬头矩阵）

诉讼技能使用两套量表，**一一映射**（来自源 CLAUDE.md「严重性词汇映射」）：

| 严重性×可能性矩阵 | `_log.yaml` `risk:` | 标准（跨插件） | 含义 |
|---|---|---|---|
| 监控 | 低 | 🟢 低 | 无需行动，跟踪即可 |
| 常规 | 中 | 🟡 中 | 按正常节奏处理 |
| 优先 | 高 | 🟠 高 | 本周需关注 |
| 严重 | 严重 | 🔴 阻断 | 放下一切优先处理 |

> **上游技能对事项的评级在下游作为底线携带。** 阻断级发现不能被无声降级，除非下游技能明确声明降级理由。前端 `SeverityBadge` 与提示词 `security.py` 都要实现此映射。`litigation_matters.risk` 与 `litigation_analyses.severity` 落此量表。

### 2.5 工作成果抬头与中国法保密说明（2 分支，litigation 独有保真点）

**工作成果标头**（附于本模块生成的每份内部分析 / 简报 / 分流 / 审查之前，按 `user_role` 2 分支）：

| 角色 | 抬头 |
|------|------|
| 律师 / 法律专业人士 | `保密 · 受律师-客户特权保护 —— 律师工作成果 —— 依律师指示编制` |
| 非律师 | `研究笔记 —— 非法律意见 —— 在采取行动前请由执业律师审查` |

**中国法保密说明（必须保真移植，区别于美式 work product）：** "律师工作成果"是美国法 FRCP 26(b)(3) 概念，中国法律体系无对应的独立保护制度——

- 《律师法》§38：律师应保守执业中知悉的国家秘密、商业秘密，对委托人不愿泄露的信息予以保密 `[法条原文]`
- 《民事诉讼法》§67：法院有权调查取证，有关单位和个人不得拒绝——中国法下律师保密特权**并非绝对**
- 与**外部律师**沟通享更强保密保护；纯内部分析备忘录在诉讼中保密性相对较弱

> ⚠️ **对外交付物（律师函 / 证据保全通知 / 诉讼文书 / 对家函件）一律移除抬头**。`WorkProductHeader` 组件与 `security.py` 都要实现 (role) 2 分支 + 目的地检查（抬头是标签非控制手段，发送前检查去向）。

### 2.6 定时代理

| 代理 | 调度 | 功能 | 是否调 LLM |
|------|------|------|-----------|
| docket-watcher | 每周一 10:23（错峰；09:07/09:23/09:37/09:47/10:07 已被占用，每日 08:17 已占用） | 读活跃 `litigation_matters` 的 deadline 事件 + `legal_hold` 的 next_refresh，按审限规则**重算**候选期限（不信任已存日期），分桶预警；逾期 / 态势变化即时上报 | **否**（纯算术，照 ip_renewal_watcher / dataroom_watcher） |

> 说明：源 `docket-watcher.md` 强调"**不直接排入日程**——推算期限是线索，不是日程条目；须经执业律师对照法院实际规则核验"。审限计算是确定性算术（一审 6 月 / 简易 3 月 / 上诉 15 日等），因此 cron 不调 LLM。即便无到期事项也发简短"无事报告"——"静默通过看起来与损坏的定时任务一模一样"。

---

## 3. 复用既有架构（镜像 ip / privacy）

### 3.1 直接复用的公共引擎（不新建）

| 组件 | 路径 | 复用方式 |
|------|------|---------|
| 模型工厂 | `agents/model_factory.py` → `create_pydantic_model()` | 直接调用 |
| Agent 流式引擎 | `services/agent_stream.py` → `stream_agent_run()` | 直接调用 |
| WS 连接管理 | `services/agent.py` → `AgentConnectionManager` | 直接复用 |
| WS 鉴权 | `api/deps.py` → `get_current_user_ws` | 直接复用 |
| 调度器 | `scheduler.py`（APScheduler，已挂在 lifespan） | **只新增一个 job**，不改 lifespan |
| module_configs 表 | `db/models/module_config.py` | 直接复用，`module_name="litigation-legal"` |
| 法律检索工具 | `agents/tools/law_tools.py` → `search_law / get_law_article` | 按需挂到需法条的技能 |
| 活跃用户迭代 | `tasks/_common.py` → `iter_active_user_ids(db)` | cron 直接复用 |
| 领域异常 | `core/exceptions.py`（NotFoundError / AuthorizationError 等） | 直接复用 |
| JSON 序列化助手 | `services/_emp_serialize.py` → `dump_for_db()` | 直接复用 |
| 冷启动状态机蓝本 | `services/ip_cold_start_service.py`（状态机蓝本） | 复制为 litigation 版 |

### 3.2 复制 ip / privacy 模式新建的组件（**复制而非共享**）

profile / cold-start / WS / route 在各模块间是**逐字并行的多份代码**（如 `ip_profile_service.py` 与 `privacy_profile_service.py` 结构一致），不存在共享 company-profile。litigation 同样新建自己的一套：

| 组件 | 镜像来源 | litigation 新建 |
|------|---------|----------------|
| Agent 工厂 | `agents/ip/agent.py` | `agents/litigation/agent.py` |
| Agent Deps | `agents/ip/deps.py` | `agents/litigation/deps.py` |
| 提示词 | `agents/ip/prompts/` | `agents/litigation/prompts/` |
| 工具 | `agents/ip/tools/` | `agents/litigation/tools/` |
| WS 端点 | `api/routes/v1/ip_ws.py` | `api/routes/v1/litigation_ws.py` |
| REST 端点 | `api/routes/v1/ip.py` | `api/routes/v1/litigation.py` |
| profile service | `services/ip_profile_service.py` | `services/litigation_profile_service.py` |
| cold-start service | `services/ip_cold_start_service.py` | `services/litigation_cold_start_service.py` |
| 子服务 | `services/ip_*_service.py` | `services/litigation_*_service.py` |
| 统一分析表 | `db/models/ip_review.py` | `db/models/litigation_analysis.py` |
| 信函生命周期表 | `db/models/ip_enforcement.py` | `db/models/litigation_demand.py` |
| 主实体表 | `db/models/commercial_matter.py` | `db/models/litigation_matter.py` |
| 通知模型 | `db/models/ip_notification.py` | `db/models/litigation_notification.py` |
| 定时任务 | `tasks/ip_renewal_watcher.py` + `ip_deadline_rules.py` | `tasks/litigation_docket_watcher.py` + `litigation_deadline_rules.py` |
| 前端 API 客户端 | `lib/ip.ts` | `lib/litigation.ts` |
| 前端聊天 Hook | `hooks/use-ip-chat.ts` | `hooks/use-litigation-chat.ts` |
| 前端类型 | `types/ip.ts` | `types/litigation.ts` |
| 前端代理路由 | `app/api/ip/[[...path]]/route.ts` | `app/api/litigation/[[...path]]/route.ts` |

---

## 4. 数据模型设计

### 4.1 ORM 约定（强制）

所有模型用 SQLAlchemy `Mapped` 风格 + 继承 `Base, TimestampMixin`（见真实 `db/models/ip_review.py` / `commercial_matter.py`），**不手写 created_at/updated_at**；`String(36)` 主键 + `default=lambda: str(uuid.uuid4())`；FK `ondelete="CASCADE"`。下文用字段表描述结构，**不用裸 `CREATE TABLE`**。复杂结构一律 JSON 文本列（`Text` 列，repo 序列化用 `dump_for_db`，schema 用 `field_validator(mode="before")` + `parse_json_field` 反序列化）。

### 4.2 表清单（6 张新表 + 复用 module_configs）

> 设计取舍：matter-briefing / chronology / claim_chart / subpoena / legal_hold / oc_status / brief_section / deposition_prep / privilege_log 这 9 类**内部分析产出**结构相近且需跨技能引用（严重性底线 + prior-context 检索），统一进 **`litigation_analyses`**（`analysis_type` 判别 + `result_json`），照 ip `ip_reviews`。**律师函生命周期独特**（信函草稿、模式、发送门禁、来函四选项树、回复期限），单独建 **`litigation_demands`**（类比 ip_enforcement）。**案件 + 事件流**是 litigation 核心，建 **`litigation_matters`**（主表，镜像 commercial_matter）+ **`litigation_matter_events`**（事件子表，litigation 独有）。

#### 4.2.1 `litigation_profiles`（诉讼实务画像，1:1 用户）

镜像 ZH `CLAUDE.md` 各节，JSON 列承载：

- 公司画像：`company_context` JSON（实体 / 行业 / 上市状态 / 监管状态 / 核心管辖地 / 人员规模 / 法务团队规模，多来自共享 company-profile）、`key_contacts` JSON（GC / CFO / HR / PR / 信息安全 / 审计委员会，及"何时纳入"阈值）
- 使用者：`user_role`（`lawyer` / `non_lawyer_with_counsel` / `non_lawyer_without`）、`lawyer_contact`
- 执业角色：`practice_role`（`企业法务` / `律所律师` / `独立执业` / `其他`）— 决定下游话术框架（准备金/合伙人审查/案件量）
- 当事人角色：`party_role`（`原告方` / `被告方` / `兼顾-默认原告` / `兼顾-默认被告` / `依案件而定`）— 决定进攻 vs 防守框架
- 集成：`integrations` JSON（文件存储 / 即时通讯 / 定时任务 / 合同管理系统，本期多为 ✗）
- 风险校准：`risk_calibration` JSON（风险偏好 + 严重性×可能性 3×3 矩阵 + 严重性/可能性分级阈值 + 重大性阈值（准备金/披露/管理层报告/GC 上报）+ 和解权限阶梯 + 保险覆盖 + 保险通知程序）
- 争议画像：`dispute_profile` JSON（业务背景 + 争议模式表 + 常见对手 + 外部律师库 + 常见管辖法院/仲裁机构 + 文件存储 + 利益冲突排查方法）
- 文书风格：`doc_style` JSON（管理层备忘录 / 准备金备忘录 / 外部律师指令 / 保密惯例 / 证据保全模板 / 上报渠道 / 律师函实务）
- 输出与表面：`output_config` JSON（工作成果抬头规则 2 分支 / 安静模式 / 审查备注格式 / 下一步决策树）
- 状态：`setup_status`（not_started/in_progress/completed）、`setup_progress` JSON、`setup_depth`（quick/full）
- `profile_content`（Markdown，编译后的画像，注入系统提示词）
- `UNIQUE(user_id)`

#### 4.2.2 `litigation_matters`（案件主表，N）

镜像 `commercial_matter.py`，但字段更丰富（matter 是 litigation 核心）：

- `user_id`(FK, index)
- 标识：`case_name`、`case_number`、`court`、`cause_of_action`（案由，依《民事案件案由规定》）、`case_type`、`jurisdiction`
- 当事人：`our_side`（`plaintiff` / `defendant` / `third_party`）、`counterparty`
- 状态：`status`（`active` / `settled` / `dismissed` / `judgment_won` / `judgment_lost` / `withdrawn` / `closed` / `archived`）、`stage`（庭前 / 证据交换 / 庭审 / 上诉 / 执行）
- 风险：`risk`（低/中/高/严重）、`materiality`（已计提准备金 / 已对外披露 / 监控中 / 无）、`exposure_range`
- 关键日期：`filing_date`、`next_deadline`（当前最紧迫单一期限，由 events 重算回填）
- JSON：`outside_counsel`（外所/主办/费率/委托协议）、`internal_owners`（业务负责人/HR/公关/财务）、`conflicts`（冲突排查状态：method/cleared_by/cleared_date/override）
- `initial_theory`（text，初始案件理论）、`notes`、`source`（manual / demand_escalation / cold_start）
- 结案字段（可空）：`closed_date`、`outcome`、`final_cost`、`lessons`
- `index(user_id, case_number)`、`index(user_id, status)`

> **冲突门禁**：matter-intake 创建时必须经过利益冲突排查（三路径：现在运行 / 标注待定 / 书面绕过），结果写 `conflicts`。matter-briefing/update/close 的"代号必须存在"门禁由 service 校验。

#### 4.2.3 `litigation_matter_events`（案件事件流/时间线，N:1 matter，litigation 独有）

源自 `history.md` 逐案事件追加 + `_log.yaml` 状态变更。matter-update 写入；matter-briefing / portfolio-status / docket-watcher 读取：

- `matter_id`(FK, index)、`user_id`(FK，冗余便于归属过滤)
- `event_date`、`event_type`（`procedure` / `evidence` / `substantive` / `strategy` / `risk_reassessment` / `party` / `administrative` / **`deadline`** / `closing`）
- `summary`（text，发生了什么）
- `field_changes`（JSON，记录此事件触发的 status/risk/stage/materiality 等字段变更：`{字段: [旧值, 新值]}`）
- `due_date`（DATE，可空——`event_type=deadline` 的候选期限，供 docket-watcher 扫描）
- `deadline_status`（可空：pending / approaching / overdue / met / waived）
- `associated_files`（JSON，关联文件路径）
- `index(matter_id, event_date)`。**纯追加，不修改既往记录**；修正通过新条目实现。**待办/候选期限统一作为 `event_type=deadline` 的事件行**（精简为 1 表承载事件 + 期限）。

#### 4.2.4 `litigation_demands`（律师函生命周期，N）

镜像 `ip_enforcement.py`：

- `user_id`(FK, index)、`matter_id`(FK，可空——独立函件不关联具体案件)
- `demand_type`：`payment`（付款催告）/ `breach_cure`（违约整改）/ `stop_infringement`（停止侵权）/ `evidence_preservation`（证据保全函）/ `settlement`（和解）/ `other`
- `mode`：`send`（发送）/ `receive`（接收）
- `counterparty`（对方当事人；**最小化**，避免 PII 滥置）
- `intake_snapshot` JSON（委托登记：函件类型 / 当事人 / 事实 / 法律依据 / 期望结果 / 截止 / 先前沟通 / 分发 / 筹码 / 不利耐受 / 语气 / 保密过滤 / 自认弃权风险）
- `right_or_claim` JSON（涉案主张：权利类型 / 依据 / 状态）
- `letter_draft`（Markdown，**内部草稿带抬头**）、`outbound_letter`（Markdown，**对外版本去抬头**）
- `pretransmit_checklist` JSON（发送前 7 项门禁：保密过滤 / 自认风险 / 权利保留 / 和解姿态 / 事实准确性 / 比例适当 / 授权人签署）
- `response_deadline` DATE（可空；对方回复期限 / 我方合规期限）
- `triage_result` JSON（receive 模式的四选项树结论：遵从/谈判/反制/忽略 + 实质理由评估）
- `recommended_action`（可空：receive 模式结论）
- `status`（intake / drafting / gated / sent / received / responded / escalated / closed）
- `escalation_flag` BOOL、`escalation_reason`
- `sent_date` DATE、`sent_via`（邮件/快递/当面）
- `log` JSON（审计：建档/起草/过门禁/标记已发送日期、审批人）

> **系统只产草稿、绝不实际发送**：`status=sent` 仅表示用户在前端确认"我已自行发出"，系统不调用任何外发通道（符合安全规则：对外发函由用户本人执行）。

#### 4.2.5 `litigation_analyses`（内部分析产出统一表，N）

镜像 `ip_review.py`，按 `analysis_type` 判别 **9 类**：`matter_briefing` / `chronology` / `claim_chart` / `subpoena_triage` / `legal_hold` / `oc_status` / `brief_section` / `deposition_prep` / `privilege_log`：

- `user_id`(FK, index)、`matter_id`(FK，可空——subpoena 可能未关联案件)
- `analysis_type`、`subject`（案件名 / 证人 / 调查令来源 / 书状章节 / 证据清单——用于 prior-context 检索与严重性底线）
- `counterparty`（可空）
- `classification`（可空，skill-specific：subpoena 用 5 分类；privilege 用三态 `ADMISSIBLE`/`MARKED`/`INADMISSIBLE`；claim-chart 用模式 `infringement`/`invalidity`/`civil_elements`；demand-received 在 demands 表）
- `severity`（可空：blocking/high/medium/low ↔ 严重/优先/常规/监控）
- `result_summary`（text，底线一两句）、`result_memo`（Markdown 全文，含工作成果抬头）、`result_json`（结构化：events / claim_mapping / objection_frameworks / evidence_entries / outline / **legal_hold 的 hold_status + next_refresh + custodians**）
- `status`（draft/final）
- 由 WS Agent 经 `save_analysis` 工具写入；REST 仅读历史。`index(user_id, matter_id)`、`index(analysis_type)`。

> **legal-hold 进本表**（`analysis_type=legal_hold`），`result_json` 存 `hold_status`（issued/refreshed/released）/ `issued_date` / `scope` / `custodians` / **`next_refresh`** / `released_date`。docket-watcher 扫 `analysis_type=legal_hold` 的 `next_refresh`。

#### 4.2.6 `litigation_notifications`（通知，N）

照 `ip_notification.py`：`notification_type`（`docket_alert` / `deadline_alert` / `manual`）、`title`、`content`（Markdown）、`priority`、`is_read`、`action_url`。

### 4.3 实体关系图

```
users (1) ── (1) litigation_profiles
users (1) ── (N) litigation_matters (1) ── (N) litigation_matter_events   [event_type 含 deadline]
users (1) ── (N) litigation_demands       [demand_type · mode: send/receive]
users (1) ── (N) litigation_analyses      [analysis_type: 9 类]
users (1) ── (N) litigation_notifications
users (1) ── (1) module_configs [module_name="litigation-legal"]
```

---

## 5. 后端开发任务

### 5.1 Phase 1：数据层

#### 任务 1.1：Alembic 迁移（**幂等守护强制**）

照 ip 拆 **2 个迁移文件**，链在当前 head 之后（先 `uv run alembic heads` 确认，当前最新为 ip 的迁移）：

1. `2026-06-xx_add_litigation_profile_table.py`
2. `2026-06-xx_add_litigation_core_tables.py`（matters / matter_events / demands / analyses / notifications）

每个 `upgrade()` 用 inspector 守护（**create_all + Alembic 双轨**，否则 `test_migrations` 红），`downgrade()` 名称无关、逆 FK 顺序 drop（先 matter_events 后 matters）：

```python
def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "litigation_profiles" in inspector.get_table_names():   # 锚点表守护
        return
    op.create_table("litigation_profiles", ..., *_ts_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE",
                                name="fk_litigation_profiles_user_id"),
        sa.UniqueConstraint("user_id", name="uq_litigation_profiles_user_id"))
    op.create_index("ix_litigation_profiles_user_id", "litigation_profiles", ["user_id"])

def downgrade() -> None:
    op.drop_table("litigation_profiles")
```

`_ts_columns()` 助手照 ip / privacy 迁移复制（created_at server_default + updated_at nullable）。

#### 任务 1.2：数据模型（6 文件）

`db/models/litigation_profile.py`、`litigation_matter.py`、`litigation_matter_event.py`、`litigation_demand.py`、`litigation_analysis.py`、`litigation_notification.py`。在 `db/models/__init__.py` 导入并加入 `__all__`（`main.py` 启动时 `from app.db import models` 触发 create_all 注册）。

#### 任务 1.3：Repository 层（无状态函数，`db.flush()`+`db.refresh()`，**绝不 commit**）

`litigation_profile_repo.py`、`litigation_matter_repo.py`、`litigation_matter_event_repo.py`、`litigation_demand_repo.py`、`litigation_analysis_repo.py`、`litigation_notification_repo.py`。关键字仅参数（`db` 之后 `*`）。列表函数返回 `(items, total)`；`litigation_matter_repo` 提供 `list_by_user`（全量供 cron / portfolio）；`litigation_matter_event_repo` 提供 `list_by_matter(matter_id)`（时间线）与 `list_deadlines(user_id)`（供 docket-watcher）；`litigation_analysis_repo` 提供 `list_by_subject` 与 `list_legal_holds(user_id)`。JSON 列在 service 内用 `dump_for_db` 序列化。

#### 任务 1.4：Schema 层 `schemas/litigation/`

`__init__.py`、`_json.py`（复用 `parse_json_field`）、`profile.py`、`cold_start.py`、`matter.py`、`matter_event.py`、`demand.py`、`analysis.py`、`notification.py`。遵循 `*Create/*Update/*Read/*List` + `ConfigDict(from_attributes=True)`；JSON-text 列用 `@field_validator(mode="before")` 解码。`Literal` 类型：`UserRole` / `PracticeRole` / `PartyRole` / `MatterStatus` / `MatterStage` / `EventType` / `DemandType` / `DemandMode` / `AnalysisType` / `Severity` / `ModuleStatus`。

### 5.2 Phase 2：技能引擎

#### 任务 2.1：Agent 工厂（镜像 `ip/agent.py`）

`agents/litigation/agent.py`：

```python
LitigationSkillName = Literal[
    "matter_briefing", "demand_draft", "demand_received", "subpoena_triage",
    "legal_hold", "chronology", "claim_chart", "oc_status",
    "brief_section", "deposition_prep", "privilege_log",
]
SKILL_ANALYSIS_TYPE: dict[LitigationSkillName, str] = {...}
# demand_draft / demand_received 写 litigation_demands，不入 SKILL_ANALYSIS_TYPE
_PROMPT_BUILDERS: dict[LitigationSkillName, Callable[..., str]] = {...}
_SKILL_TOOLS:    dict[LitigationSkillName, tuple[Callable, ...]] = {...}
# 需要法条检索的技能挂 search_law / get_law_article：
_LAW_TOOL_SKILLS: frozenset[LitigationSkillName] = frozenset(
    {"claim_chart", "subpoena_triage", "legal_hold", "demand_draft", "demand_received",
     "brief_section", "privilege_log"}
    # chronology / deposition_prep / matter_briefing / oc_status 主要基于卷宗与画像，可不挂
)

def create_litigation_agent(skill, *, practice_profile_markdown=None,
                            model_name=None, provider=None, api_key=None,
                            base_url=None, temperature=None) -> Agent[LitigationDeps, str]:
    ...  # 同 ip：查 builder、create_pydantic_model、挂 _SKILL_TOOLS[skill]、按需挂 law tools、tool_retries=3
```

`agents/litigation/deps.py`：

```python
@dataclass
class LitigationDeps:
    user_id: str
    db: Session
    analysis_type: str | None = None   # 分析技能预建行后回填
    analysis_id: str | None = None
    demand_id: str | None = None       # demand-draft/received 起草目标
    matter_id: str | None = None       # 案件上下文
    output_dir: str | None = None
```

#### 任务 2.2：提示词提取 `agents/litigation/prompts/`

从 `~/.claude/plugins/marketplaces/claude-for-legal-zh/litigation-legal/skills/*/SKILL.md` **逐段提取，保留全部实质内容**（中国法条引用、各分类、多模式分支、风险方法论、免责盾、五组内容分离、逐字引用纪律等）：

| 文件 | 来源 SKILL.md |
|------|-------------|
| `security.py` | 共享护栏 + 六维度风险评价 + 双轴 + 来源溯源标签 + **五组内容分离** + **2 抬头 + 中国法保密说明** + 风险量表双映射 + 时效触发 + 逐字引用纪律（来自 CLAUDE.md） |
| `matter_briefing.py` | matter-briefing（冲突门禁 + 陈旧度 + 风险重评估提示） |
| `demand_draft.py` | demand-draft（按 demand_type 骨架 + 发送前 7 项 LOUD GATE + 去抬头） |
| `demand_received.py` | demand-received（实质理由评估 + 跨案检索 + 四选项树） |
| `subpoena_triage.py` | subpoena-triage（步骤0 规则研究 + 5 分类 + 异议框架 + 监察/刑事上报） |
| `legal_hold.py` | legal-hold（issue/refresh/release + 证据保全§81/§84 + next_refresh） |
| `chronology.py` | chronology（保密门 + 逐文件提取 + 按理论标重要性 + 不解决矛盾） |
| `claim_chart.py` | claim-chart（"草案非认定"盾 + 逐要件对照 + 缺口优先 + 单元格转义） |
| `oc_status.py` | oc-status（按事务所风格 + 仅产草稿 + 发送门禁） |
| `brief_section.py` | brief-section-drafter（五组分离 + 理论一致性 + 逐字引用 + 弱论点坦诚） |
| `deposition_prep.py` | deposition-prep（按证人立场分支 + 不预测答案 + 不决定提问） |
| `privilege_log.py` | privilege-log-review（三性审查 + 三态保守 + 非法证据排除§104-106） |

> cold-start 提示词**不在此**——它是 service 状态机（任务 2.4）。matter-intake/update/close/portfolio-status **非 Agent**——纯 CRUD/算术（§7.2-7.5）。customize **非 Agent**——设置页（§7.18）。

#### 任务 2.3：工具 `agents/litigation/tools/`

签名一律 `async def tool(ctx: RunContext[LitigationDeps])`，内部做归属校验（照 ip `tools/*` 的 `_load_owned_*` 模式）。

| 文件 | 工具 |
|------|------|
| `_validators.py` | 域值校验（check_analysis_type / check_classification / check_severity 等） |
| `profile_tools.py` | `read_litigation_profile`（读画像；未配置则提示去设置） |
| `matter_tools.py` | `read_matter`（读案件 + 事件流，供 briefing/demand/chronology 取上下文）、`read_prior_analyses`（按 subject/matter 查 prior 分析，支撑严重性底线） |
| `demand_tools.py` | `read_demand`、`save_letter`（回写 letter_draft / outbound_letter / pretransmit_checklist / log / status） |
| `analysis_tools.py` | `save_analysis`（写 litigation_analyses，含 type/severity/classification/result_json）、`read_portfolio`（供 docket/briefing 查活跃案件） |
| `law_tools.py`（封装复用） | `research_litigation_rules(topic)`：先读画像 `dispute_profile`，再 RAG `search_law`（民诉法/证据规定/执行/民法典时效），标注来源标签（见 §7.18、§9） |

#### 任务 2.4：cold-start service（**非 Agent，按执业角色分支**）

`services/litigation_cold_start_service.py` 复制 `ip_cold_start_service.py` 状态机，`MODULE_NAME="litigation-legal"`，**6 步统一状态机（0–5）**，部分步骤的问题集**按 `practice_role` 动态切换**（前端 ColdStartWizard 按角色渲染不同表单；后端状态机管步骤推进 + materialize）：

```
0 使用者角色 + 执业角色(企业法务/律所/独立执业) + 当事人立场 + 集成检查        [公共]
1 [企业法务] 公司概况 + 关键内部联系人   /   [律所·独立] 案件量 + 客户期望
2 风险校准(风险偏好 / 严重性×可能性矩阵 / 重大性阈值 / 和解权限阶梯 / 保险)
3 争议画像(争议模式 / 常见对手 / 外部律师库 / 常见管辖法院 / 文件存储 / 利益冲突排查)
4 文书风格(管理层备忘录 / 准备金备忘录 / 外部律师指令 / 保密惯例 / 证据保全 / 上报 / 律师函实务)
5 输出与表面 + 生成画像(materialize)
QUICK_PLAN=(0,1,5)   FULL_PLAN=(0,1,2,3,4,5)
```

终步 `_materialize_profile` 编译并写 `litigation_profiles.profile_content` + 各 JSON 字段；跳过项写 `[占位符]`/`[立场未测试]`（绝不静默缺口）。

### 5.3 Phase 3：API 端点

#### 任务 3.1：REST（`api/routes/v1/litigation.py`，全部 CRUD/聚合，照 ip.py 签名）

处理器签名 `(... , user: CurrentUser, svc: LitigationXxxSvc) -> Any`，声明 `response_model` + 必要 `status_code`，分页 `skip/limit`：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/litigation/status` | GET | 模块配置状态（驱动前端"去设置 vs 主界面"） |
| `/litigation/setup` | POST | 冷启动步骤提交 |
| `/litigation/setup/status` | GET | 冷启动进度 |
| `/litigation/profile` | GET / PUT | 实务画像（PUT 即 customize） |
| `/litigation/matters` | GET / POST | 案件列表 / 登记（POST 含冲突门禁 + 播种首条 event） |
| `/litigation/matters/portfolio` | GET | 案件组合概览（portfolio-status：风险分布/期限/陈旧/7 类异常，聚合算术） |
| `/litigation/matters/{id}` | GET / PUT | 案件详情（含事件流） / 更新 |
| `/litigation/matters/{id}/events` | GET / POST | 事件流列表 / 追加（matter-update，含 deadline） |
| `/litigation/matters/{id}/close` | POST | 结案（matter-close，非律师门禁，status=closed 保留不删） |
| `/litigation/demands` | GET / POST | 律师函列表 / 建档（POST 落 mode + 对方 + intake_snapshot + 算 response_deadline） |
| `/litigation/demands/{id}` | GET / PUT | 律师函详情 / 更新（发送门禁结果、标记已发送、升级标记） |
| `/litigation/analyses` | GET / POST | 分析产出列表（可按 analysis_type / matter_id 过滤） / 建档（subpoena/legal_hold 先建档再 WS 起草） |
| `/litigation/analyses/{id}` | GET | 产出详情 |
| `/litigation/notifications` | GET | 通知列表 |
| `/litigation/notifications/{id}/read` | POST | 标记已读 |

#### 任务 3.2：WS（`api/routes/v1/litigation_ws.py`，镜像 ip_ws.py）

- `_SKILL_BY_ACTION` 显式映射 11 个 action → `create_litigation_agent(skill)`
- `_require_llm_configured`：未配置 LLM → 推 `error / llm_not_configured`（**绝不兜底**）
- 归属预校验（matter_id / demand_id / analysis_id 属于该用户）
- 9 个 analysis 技能仿 ip **预建 litigation_analyses 行**并推 `analysis_started`；`demand_draft/demand_received` 需先解析 demand_id（REST 已建档）
- 复用 `stream_agent_run`，事件名一致：`text_delta` / `tool_call` / `tool_result` / `final_result` / `complete` / `error`（+ `analysis_started`）

#### 任务 3.3：DI / 注册 / 挂载

- `api/deps.py`：加 `get_litigation_*_service` + `Annotated` 别名（`LitigationProfileSvc` / `LitigationColdStartSvc` / `LitigationMatterSvc` / `LitigationDemandSvc` / `LitigationAnalysisSvc` / `LitigationNotificationSvc`）
- `api/routes/v1/__init__.py`：在 ip 之后加
  ```python
  from app.api.routes.v1 import litigation, litigation_ws
  v1_router.include_router(litigation.router, prefix="/litigation", tags=["litigation"])
  v1_router.include_router(litigation_ws.router, tags=["litigation-ws"])
  ```
- `main.py` lifespan **无需改**（scheduler 已挂）

### 5.4 Phase 4：定时代理

`tasks/litigation_docket_watcher.py`，照 `ip_renewal_watcher.py` 写 `run(db) -> int`：遍历 `iter_active_user_ids`、读活跃 `litigation_matters` 的 deadline 事件 + `legal_hold` 的 next_refresh、用 `tasks/litigation_deadline_rules.py` 按审限规则重算下一期限、分桶、命中预警窗口写 `litigation_notifications`。**不调 LLM。** `scheduler.py` 新增 job（周一 10:23）。详见 §8。

### 5.5 Phase 5：服务层

`litigation_profile_service.py`、`litigation_cold_start_service.py`（任务 2.4 已起）、`litigation_matter_service.py`（含冲突门禁、事件流追加、portfolio 聚合、结案非律师门禁）、`litigation_demand_service.py`（含建档时算 response_deadline、发送门禁状态机、升级触发判定）、`litigation_analysis_service.py`、`litigation_notification_service.py`。可按 ip 把小服务合并。服务用 `dump_for_db` 编码 JSON 列；读方法做归属校验（`raise NotFoundError`）。

---

## 6. 前端开发任务

### 6.1 页面结构 `frontend/src/app/[locale]/(dashboard)/litigation/`

```
litigation/
├── page.tsx                      # 概览（未配置 → 引导冷启动）
├── setup/page.tsx                # 冷启动向导（ColdStartWizard，按执业角色分支）
├── matters/
│   ├── page.tsx                  # 案件组合（portfolio-status：风险分布/期限/陈旧/7 类异常）
│   ├── new/page.tsx              # 案件登记（matter-intake + 冲突门禁三路径）
│   └── [id]/page.tsx             # 案件详情（事件时间线 + matter-update + matter-briefing WS + matter-close）
├── demands/
│   ├── page.tsx                  # 律师函列表（发送/接收分 tab，按状态/期限分组）
│   └── [id]/page.tsx             # 律师函详情（intake / draft WS / received WS + 发送门禁 + 双栏信函）
├── analyses/
│   ├── page.tsx                  # 分析产出列表（9 类分 tab）
│   └── [id]/page.tsx             # 产出详情
├── chronology/page.tsx           # 大事记构建（WS 流式 + 进攻/防守框架）
├── claim-chart/page.tsx          # 要件分析表（WS + 缺口优先 + 草案非认定盾）
├── subpoena/page.tsx             # 调查令分流（5 分类 + WS + 异议框架）
├── legal-hold/page.tsx           # 证据保全（issue/refresh/release + WS 起草 + next_refresh）
├── oc-status/page.tsx            # 外部律师状态请求（WS 起草 + 发送门禁）
├── brief-section/page.tsx        # 书状段落起草（WS + 五组分离提示）★
├── deposition/page.tsx           # 庭前质证准备（证人立场 + WS）★
├── privilege-log/page.tsx        # 证据三性审查（上传清单 + WS + 三态）★
└── settings/page.tsx             # 实务画像设置（customize）
```

### 6.2 关键页面

- **概览**：SetupStatusCard / QuickActions（登记案件/律师函/调查令/要件分析）/ StatsCards / **DeadlineSummary**（近 30 天期限）/ RecentMattersList / NotificationArea。
- **冷启动**：`ColdStartWizard`（镜像 ip 向导），6 步，**按 practice_role 渲染不同表单**（企业法务 vs 律所/独立），调 `litigationApi.submitSetup`，服务端 materialize 后跳概览。**纯表单，非 WS。**
- **案件组合（portfolio-status）**：按风险分布 / 期限（14/30/60 天）/ 阶段分布分组 + **7 类异常标注**（逾期节点 / 陈旧 / 冲突未解 / 冲突绕过 / 高风险无覆盖 / 计提陈旧 / 证保缺口）。案件超 10 提议仪表板。
- **案件详情**：**MatterTimeline**（事件流时间线，事件类型徽章）+ matter-update 追加事件表单 + **matter-briefing WS**（深度简报，含风险重评估提示）+ matter-close（非律师门禁确认）。
- **律师函详情**：先选 **类型**（付款催告/违约整改/停止侵权/证据保全/和解）+ **模式**（发送/接收）→ 建档(REST) → 起草/分流(WS) → 展示**内部草稿（带工作成果抬头）** 与 **对外版本（去抬头）** 双栏 + **发送门禁核对清单（7 项，必须全勾才能标记"已发送"）** + 来函四选项树 + 审计日志。
- **claim-chart**：**顶部强制"草案非认定"盾** → 录入诉讼请求/权利要求 + 目标 → WS 流式 → 要件逐项对照表（强度/状态 + 逐字引用）+ **缺口优先清单**（保守宁多勿少）。
- **privilege-log**：上传证据清单 → WS 流式 → 三态意见表（✅可采/⚠️需律师/❌建议排除，**绝不删除清单**）+ 模式观察。
- **subpoena**：先选 5 分类 → WS 流式 → 范围/负担/保密分析 + 异议框架 + 合规方案；监察/刑事显示"已上报"提示。
- **chronology / brief-section / deposition / legal-hold / oc-status**：录入/上传 → WS 流式 → 结构化结果 + 详情存 analyses。

### 6.3 通用组件 `frontend/src/components/litigation/`

`RiskMatrix`（严重性×可能性 3×3）、`SeverityBadge`（🟢🟡🟠🔴 ↔ 监控/常规/优先/严重）、`PartyRoleSelector`（原告/被告/兼顾）、`ConflictGateBlock`（冲突排查三路径）、`WorkProductHeader`（按 role 2 分支 + 中国法保密说明）、`ReviewerNote`（审查备注区块）、`MatterTimeline`（事件流时间线）、`DeadlineBadge`、`DemandModeSelector`（发送/接收）、`DemandGate`（发送门禁 7 项核对清单）、`LetterDualView`（内部草稿/对外版本双栏）、`ClaimChartTable`（要件逐项对照 + 缺口）、`EvidenceReviewTable`（三性审查三态）、`SubpoenaCategoryBadge`（5 分类）、`FiveGroupSeparationNote`（五组内容分离提示）、`NextStepDecisionTree`（下一步决策树）、`PortfolioAnomalyList`（7 类异常）、`ColdStartWizard`（按角色分支）。

### 6.4 导航注册

- `components/layout/app-sidebar.tsx`：`navigation` 数组加 `{ name: t("litigation"), href: ROUTES.LITIGATION, icon: Scale }`（Lucide `Scale` / `Gavel`）
- `lib/constants.ts`：加 `LITIGATION: "/litigation"` 等 ROUTES（LITIGATION_SETUP / LITIGATION_MATTERS / LITIGATION_DEMANDS / LITIGATION_ANALYSES / LITIGATION_CHRONOLOGY / LITIGATION_CLAIM_CHART / LITIGATION_SUBPOENA / LITIGATION_LEGAL_HOLD / LITIGATION_SETTINGS）
- i18n 文案（`messages/zh.json` + `en.json`）加 `litigation` 顶层 key（zh 为主）

### 6.5 类型 `types/litigation.ts`

镜像 `types/ip.ts`：枚举（UserRole / PracticeRole / PartyRole / MatterStatus / MatterStage / EventType / DemandType / DemandMode / AnalysisType / Severity / ModuleStatus）、实体接口（LitigationMatter / LitigationMatterEvent / LitigationDemand / LitigationAnalysis / LitigationProfile）、`LitigationWsMessage`（`{action, matter_id?/demand_id?/analysis_id?, ...}`）、`LitigationWsEvent` 联合类型。

### 6.6 API 客户端 `lib/litigation.ts` + 代理 `app/api/litigation/[[...path]]/route.ts`

`litigationApi` 对象包 `apiClient`（GET/POST/PUT/upload）；catch-all 代理转发到 `/api/v1/litigation/*`，从 cookie 取 `access_token` 注入 Bearer（照 ip 代理，支持 multipart 以便卷宗/来函/证据清单上传）。

### 6.7 聊天 Hook `hooks/use-litigation-chat.ts`

镜像 `use-ip-chat.ts`：WS URL `${getWsUrl()}/api/v1/ws/litigation`，subprotocols `["access_token.${token}", "litigation"]`；发送 `{ action, matter_id?/demand_id?/analysis_id?, prompt/payload }`；处理事件 `text_delta` / `tool_call` / `tool_result` / `final_result` / `complete` / `error`（+ `analysis_started`）。

---

## 7. 技能实现详解

### 7.1 技能分发（显式 action，无意图路由）

前端按用户选择的功能直接发对应 `action`（点「要件分析」→ `action=claim_chart`）。后端 `_SKILL_BY_ACTION` 校验后建 Agent。**不做关键词意图识别**——与 ip/privacy/employment 一致，避免中文意图歧义与隐性兜底。

### 7.2 matter-intake（案件登记，REST）

统一登记 10 项：①标识（案件名/案号/法院/案由/管辖）②**冲突门禁**（利益冲突排查三路径：现在运行 / 标注待定 / 书面绕过——必须通过）③来源 ④风险分流（按画像矩阵）⑤重大性（准备金/披露触发）⑥外部律师 ⑦内部负责人 ⑧证据保全初判 ⑨期限 ⑩初始理论。生成 slug → 建 `litigation_matters` + 播种首条 `litigation_matter_events`（event_type=administrative）→ 展示完整内容确认。**护栏**：冲突排查三路径清晰、案号唯一检查、占位符诚实标注、无自行冲突检索（仅记录）、无自动保全发出。当事人角色（原告/被告）分支提问。

### 7.3 matter-update（案件进展，REST）

冲突门禁（代号必须存在）→ 提示事件类型（7 类）+ 日期（默认今天）+ 摘要 → 逐项检查日志字段变更（status/stage/risk/materiality）→ **重要性触发器**（实质/策略/风险/监管事件时必询）→ **接受和解门禁**（非律师需律师审查）→ 追加 `litigation_matter_events`（含 field_changes；若 deadline 事件则写 due_date）→ 回填 `litigation_matters.next_deadline`。**无编辑既往历史**（新条目纠正）。

### 7.4 matter-close（结案归档，REST）

冲突门禁 → 确认代号与当前状态 → 捕获结果（类型：和解/撤诉/判决我方胜/判决我方败/撤回/合并/其他 + 日期 + 敞口 + 成本 + 教训）→ **非律师门禁**（需律师审查）→ `status=closed` + 写 closed_date/outcome/final_cost/lessons + 追加 closing 事件。**既有行不删**（status 变 closed）；教训需诚实（不编造）。

### 7.5 portfolio-status（案件组合概览，REST 聚合算术）

解析活跃 `litigation_matters`（status != closed）→ 按风险分布 / 按期限（14/30/60 天）/ 按重大性 / 按阶段分组 → **7 类异常逐项检查**（逾期节点 / 陈旧>30天 / 冲突未解 / 冲突绕过 / 高风险无覆盖 / 计提陈旧 / 证保缺口）→ 案件超 10 提议仪表板。**不做决定（浮现问题）、不假装精度（敞口是粗略）、不替代案件管理系统（仅汇总）。**

### 7.6 matter-briefing（单案深度简报，WS Agent）

冲突门禁（代号必须存在）→ 读 matter + 事件流 + 画像 → **陈旧度检查**（>30 天标注）→ 生成简报：一段话概要 + 近期变化 + 下一节点 + 敞口 + 内部负责人 + **风险重评估提示** + 待解决问题 + （如指定目的）通话前备忘。**风险评级仅是记录判断（不预测）、不推荐策略（浮现问题）。** 落 `litigation_analyses(type=matter_briefing)`。

### 7.7 demand-intake（律师函委托登记，REST 建档）

加载风险校准 + 律师函实务 → 询问 **8 核心项**（函件类型/当事人/事实/法律依据/期望/截止/先前沟通/分发）+ 按重要性选询 **5 策略块**（筹码/不利耐受/语气/保密过滤/自认弃权风险）→ 生成 slug → 建 `litigation_demands(mode=send, status=intake)` 写 intake_snapshot → 提示"准备好时起草"。**必填 vs 可选分明，逐项确认。**

### 7.8 demand-draft（律师函起草，WS Agent）

加载 intake → 运行**起草前 7 项门禁**（保密过滤/自认风险/权利保留/和解姿态/事实准确性/比例适当/授权人签署）→ 按 demand_type 选骨架（付款催告/违约整改/停止侵权等，引民法典§195 诉讼时效中断）→ 对话迭代起草至用户批准 → 回写 `letter_draft`(带抬头) + `outbound_letter`(**去抬头**) + pretransmit_checklist → 输出发送后检查清单。**外发版不含抬头、逐字引用逐字、门禁不可跳（或标注已跳）、不发送（仅草稿）。**

### 7.9 demand-received（来函分流，REST 建档 + WS）

审读来函提取关键字段 → **案件组合交叉检索**（直接匹配 + 类型匹配）→ **实质理由评估**（事实/法律基础/对方胜算/我方抗辩/索赔合理性）→ **四选项树**（A 实质回复 / B 暂搁观察 / C 和解谈判 / D 不回复 + 证据保全）→ 期限分流（对方/我方内部/法定，诉讼时效§195）→ 撰写分流意见 → 转交（创建案件/起草回复/关联既有案）。**不验证被引用法律（标注 `[需审查]`）、不发送回复（仅分流）、不做最终判断。** 落 `litigation_demands(mode=receive)`。

### 7.10 subpoena-triage（调查令/协查分流，REST 建档 + WS）

**步骤0：前置研究适用规则**（民诉法§67、解释§94-96、各省律师调查令实施办法等；**不沉默补充**，标注 `[联网检索—需复核]`）→ **5 分类**（法院调查令/律师调查令/行政协查/证人出庭/**监察或刑事侦查→上报**）→ 提取关键字段 → 案件组合交叉检索 → 范围/负担/保密分析 → 异议框架（法律依据/具体适用/强度）→ 合规方案（预计提供范围/检索人员/审查方案）→ 期限（答复/异议/协商/提供）→ 撰写分流意见。**不沉默补充、不最终决定异议（框架供律师用）、刑事案件上报。** 落 `litigation_analyses(type=subpoena_triage)`。

### 7.11 legal-hold（证据保全，REST 状态 + WS 起草）

**三态生命周期**：`issue`（首次：范围+保管人+日期+系统 → 起草保全通知，民诉法§81/§84）/ `refresh`（6 个月：确认范围变更 → 下一版本）/ `release`（解除：确认日期+留存指令 → 解除通知）。每次更新 `result_json` 的 hold_status + **next_refresh**（喂 docket-watcher）。**草案收尾标注"发出保全启动义务"、不强制执行（律师审查+发出）、保管人离职时标记。** 落 `litigation_analyses(type=legal_hold)`。

### 7.12 chronology（大事记/时间线，WS Agent）

**保密门**（用户声明来源已清理或需标记）→ 识别文件来源 → 逐文件提取带日期事件 → 去重合并 → **按案件理论标重要性**（🔴/🟡/⚪，进攻性 vs 防守性框架）→ 输出大事记表（带来源标注）→ 版本号递增。**来源标注不删、不解决矛盾（两说法都列并标记）、不发明来源中没有的事件、完整性不保证。** 落 `litigation_analyses(type=chronology)`。

### 7.13 claim-chart（要件分析表，WS Agent）

**"草案非认定"盾置顶** → 确认模式（民事构成要件 / 专利侵权-无效-审查）+ 上下文（立场/管辖/阶段）→ 加载要件模板 + 确认控制性法律依据（民诉法§67 谁主张谁举证）→ 映射每要件到目标（强度/状态）→ **逐字引用** → **缺口检测【优先输出】**（保守宁多勿少）→ 表格 + CSV → 更新事件流。**顶部声明"草案非认定"、缺口倾向保守、逐字引用、单元格前缀转义。** 落 `litigation_analyses(type=claim_chart)`。

### 7.14 oc-status（外部律师进度询问，WS Agent）

过滤活跃案件（status != closed 且外聘律师非空，默认 >10 天未更新 + 21 天内期限）→ 每案读 matter + 事件流 → 各案邮件草稿骨架（开场 + 进展 + 节点 + 待决 + 预算 + 具体要求）→ 按事务所沟通风格调整语气 → 输出 Markdown 草稿。**仅生成草稿（律师审查+发送）、发送门禁提示、不生成没有的内容。** 落 `litigation_analyses(type=oc_status)`。

### 7.15 brief-section-drafter（书状段落起草，WS Agent）★

选章节类型（起诉状/答辩状/代理词/上诉状/再审申请；书面 vs 口头）→ 加载案件理论 + 风格指南 → **理论一致性检查**（章节与理论是否一致）→ **五组内容分离纪律**（证据列举/质证意见/证据认定/查明事实/争议焦点分析，后一组不超前一组）→ 按内部风格起草 → **引用一切**（事实→卷宗，法律→法条，民诉法§13 诚信原则）→ 标记 `[需核实]` + 弱论点坦诚标注。**逐字引用必须逐字、精确引用必须支撑整个命题、外发版不含抬头。** 落 `litigation_analyses(type=brief_section)`。

### 7.16 deposition-prep（庭前质证准备，WS Agent）★

证人身份确认 → **按立场选提问风格**（对方/交叉提问 vs 己方/直接提问；单位当事人特殊规则）→ 提取其文件 → 构建要点（背景 → 有利事实 → 不利事实 → 质证材料 → 核心事实序列）→ 撰写提纲 + 证据列表。**逐字引用必须逐字、缺确切引文用占位 `[核实确切引文]`、绝不填补空白、不预测证人答案、不决定庭审提问。** 落 `litigation_analyses(type=deposition_prep)`。

### 7.17 privilege-log-review（证据三性审查，WS Agent）★

格式检查（必填字段）→ 逐项审查（原件 vs 副本/来源/形式规范/与待证事实关联）→ **真实性、合法性、关联性三性** → **非法证据排除规则**（民诉法解释§104-106）→ **三态标记**（✅可采 / ✅+⚠️保留并标记需律师 / ❌建议排除，**仍保留**）→ 模式标记（重复问题、过度提交）。**三态规则不自裁（⚠️=人工决定）、❌不删除清单（仅建议）、保守倾向（宁标记过度）。** 落 `litigation_analyses(type=privilege_log)`。

### 7.18 cold-start-interview & customize

- **cold-start-interview**：service 状态机 + 前端向导（§5.2 任务 2.4、§6.2）。保真 ZH 的"快速/完整"分叉、**按执业角色分支**、对真实回答暂停等待、即时核实用户陈述的法律事实、绝不静默缺口、占位符未填则每个技能停下引导设置。
- **customize**：不单独建 Agent；映射为**设置页** + `PUT /litigation/profile`。按节分组（风险校准/争议画像/文书风格/角色/集成），改一项即写回。护栏：不删节（标记"不在范围"）、提示跨字段冲突、展示下游技能影响。

### 7.19 共享护栏移植（`prompts/security.py`，所有技能注入）

ZH CLAUDE.md「共享护栏」「风险评价方法论」「主观法律判断决策姿态」整体移植：

- **来源溯源标签（中国法版）**：`[法条原文]`/`[裁判文书]`/`[本地知识库]`/`[联网检索—需复核]`/`[模型知识—需验证]`/`[用户提供]`/`[已验证—YYYY-MM-DD]`。⚠️ ZH 原文 `[yuandian检索]` → 本期改为 `[本地知识库]`（LexMind 用 RAG，不接外部 MCP）。
- **六维度风险评价 + 双轴风险评价**（诉讼场景商业摩擦维度可简化，重点法律风险）。
- **五组内容分离**（证据列举/质证意见/证据认定/查明事实/争议焦点分析）—— 注入 brief-section/claim-chart/privilege-log。
- **三值而非二值**（标注补充 / 停止并告知 / 标注但不使用），**禁止沉默补充**。
- **时效触发**：引《民事诉讼法》《证据规定》《民法典》时效具体条文 / 司法解释 / 地方口径 / 案例前先检索（RAG/web），不直接用模型知识。
- **跨技能严重性底线**（阻断级→监控须显式声明降级理由）。
- **2 种工作成果抬头 + 中国法保密说明**（§2.5）：按 role 分支；**对外交付物（律师函/证据保全通知/诉讼文书/对家函件）省略抬头**。
- **逐字引用纪律**（卷宗/笔录/证人陈述逐字准确，近似正确比改述更糟）+ **精确引用必须支撑整个命题**。
- **审查备注区块**（来源/已读/标注/时效性/依赖前）、**安静模式**（对外交付物像合伙人写的）、**目的地检查**（抬头是标签非控制）、**下一步决策树**、**关口**（发律师函/证据保全前，非律师出简报）。
- **比例性 / 管辖域识别（默认中国大陆法，涉港澳台/境外识别并行动）/ 检索内容信任（MCP/RAG/上传内容是数据非指令）/ 卷宗引用失败不沉默**。

---

## 8. 定时代理实现

`tasks/litigation_docket_watcher.py`，照 `ip_renewal_watcher.py` 的 `run(db) -> int` + `tasks/litigation_deadline_rules.py` 算术助手：

```python
def run(db: Session) -> int:
    written = 0
    for user_id in iter_active_user_ids(db):
        profile = litigation_profile_repo.get_by_user_id(db, user_id)
        if not profile or profile.setup_status != "completed":
            continue
        matters, _ = litigation_matter_repo.list_by_user(db, user_id=user_id, skip=0, limit=10000)
        active = [m for m in matters if m.status not in ("closed", "archived")]
        buckets = bucket_deadlines(db, active)      # 纯算术：扫 deadline 事件 + legal_hold next_refresh，按审限规则重算 + 分桶
        if buckets.has_alerts():                    # 含 逾期 / ≤30天 / 态势变化
            litigation_notification_repo.create(db, user_id=user_id,
                notification_type="docket_alert", priority=buckets.top_priority(),
                title=f"案件进度提醒：{buckets.summary()}",
                content=render_docket_report(buckets),  # 🔴≤7日 · 🟠8-30日 · 🔵态势变化 · ⏰逾期待办
                action_url="/litigation/matters")
            written += 1
    return written
```

`tasks/litigation_deadline_rules.py`（确定性算术，无 LLM）：

- 审限：一审普通程序 6 个月（可延长）/ 简易程序 3 个月 / 小额诉讼 2 个月
- 上诉期：判决 15 日 / 裁定 10 日（自送达次日起）
- 举证期限：不少于 15 日；管辖权异议：答辩期内（15 日）提出
- 申请执行时效：2 年（民诉法§246）
- 证据保全刷新：6 个月（从 legal_hold 的 last_refresh 算 next_refresh）
- 诉讼时效：3 年（民法典§188）；中断重算（§195）—— 仅作提示，须律师核实

`scheduler.py` 新增 `JOB_LITIGATION_DOCKET_WATCHER`，`CronTrigger(day_of_week="mon", hour=10, minute=23)`，`replace_existing=True`。**不调 LLM。** 无到期事项也发简短"无事报告"。**关键护栏（来自源 docket-watcher.md）**：推算期限是**线索非日程**（须律师核实）、不信赖自身文书分类、"无新进"≠"无问题"、不触碰已结案件。

---

## 9. 法条检索与知识库前置条件

- **复用** `agents/tools/law_tools.py` 的 `search_law` / `get_law_article`（Qdrant + BGE-zh）。新增 `research_litigation_rules(topic)` 薄封装：先读画像 `dispute_profile`（常见管辖法院/地域），再 RAG 检索，按 §7.19 标注来源。
- **⚠️ 前置条件（开发前确认）**：RAG 语料须包含 **《民事诉讼法》《最高人民法院关于适用〈民事诉讼法〉的解释》《民事诉讼证据规定》《民法典》（诉讼时效 §188/§195）** 及关键执行规定、司法解释（举证时限、非法证据排除§104-106、证据保全§94-99、调查令§94-96）。若缺，按 `docs/development/guides/add-rag-source.md` 先行入库，否则 `research_litigation_rules` 命中率不足、技能将频繁"禁止沉默补充"停下。**地方性司法口径（各省律师调查令实施办法）差异大**，subpoena-triage 须显式标注 `[联网检索—需复核]`。
- **移植 references**：把 `claude-for-legal-zh/litigation-legal/references/` 下的核心规则文件作为模块参考数据（照 employment 的 `references/labor-core-rules.md` 与 ip 的 `references/ip-core-rules.md` 处理）——放 `backend/app/agents/litigation/references/litigation-core-rules.md` 供提示词/工具引用。

---

## 10. 开发排期

### 总工期：约 5–6 周（比 ip 略多——6 张表 vs 5、11 WS action vs 8、cold-start 角色分支、matter 事件流、+3 额外技能）

```
Week 1  数据层 + 技能引擎起步
  D1 迁移(2文件,幂等守护) + 模型(6)    D2 Repository + Schema
  D3 服务层(profile + cold-start 角色分支状态机)    D4 Agent工厂+Deps + 提示词(security 含五组分离+2抬头, matter_briefing, claim_chart)
  D5 提示词(demand_draft 7门禁, demand_received 四选项, subpoena 5分类)

Week 2  技能引擎完成 + API
  D1 提示词(legal_hold 三态, chronology, oc_status, brief_section 五组, deposition, privilege_log 三态)
  D2 工具(profile/matter/demand/analysis/law)    D3 REST(~18端点, matters/events/portfolio/close, demands, analyses) + DI/注册/挂载
  D4 WS(11 action, 预建行)    D5 deadline_rules + docket cron + API 集成测试

Week 3-4  前端
  W3D1 冷启动向导(角色分支) + 案件组合(7异常)/案件详情(时间线+briefing)
  W3D2 案件登记(冲突门禁) + matter-update/close    W3D3 律师函列表/详情(双模 + 7门禁 + 双栏)
  W3D4 claim-chart(缺口+草案盾) + chronology    W3D5 subpoena(5分类) + legal-hold(三态)
  W4D1 brief-section(五组) + deposition + privilege-log(三态)    W4D2 oc-status + analyses 列表/详情 + 设置页
  W4D3 导航/代理/Hook/类型    W4D4-5 通用组件(RiskMatrix/WorkProductHeader/DemandGate/LetterDualView/ClaimChartTable/EvidenceReviewTable)

Week 5  联调 + 测试
  D1-2 全链路联调(17 技能手测 + 冷启动角色分支)    D3 集成测试(tests/litigation/: repo/service/scheduler/migrations)
  D4-5 Bug 修复

Week 6  缓冲 + 部署
```

### 里程碑

| 里程碑 | 目标 | 交付物 |
|--------|------|--------|
| M1 数据层就绪 | W1 D2 | 6 表 + Repo + Schema（迁移幂等过 test_migrations） |
| M2 冷启动可运行 | W1 D3 | cold-start 角色分支状态机贯通 |
| M3 案件中枢可运行 | W2 D3 | matter-intake/update/close/portfolio/briefing 手测通过（冲突门禁 + 事件流 + 非律师门禁） |
| M4 律师函可运行 | W2 D4 | demand 双模式 + 7 项发送门禁 + 对外去抬头 手测通过 |
| M5 全部 Agent 技能可用 | W2 D5 | 11 个 WS action 手测通过 |
| M6 API + cron 完成 | W2 D5 | REST + WS + portfolio 算术 + docket cron |
| M7 前端完成 | W4 D5 | 所有页面可用 |
| M8 验收通过 | W5 D5 | 全功能 + tests/litigation 绿 |

---

## 11. 附录：关键文件清单

### 11.1 需读取的源文件（claude-for-legal-zh，**以 -zh 为准**）

`~/.claude/plugins/marketplaces/claude-for-legal-zh/litigation-legal/`：`CLAUDE.md`（画像模板 + 共享护栏 + 风险方法论 + **五组内容分离** + **2 抬头 + 中国法保密说明** + 严重性词汇映射）、`references/`（核心规则）、`agents/docket-watcher.md`、`skills/{cold-start-interview,customize,matter-intake,matter-update,matter-close,matter-briefing,portfolio-status,demand-intake,demand-draft,demand-received,subpoena-triage,legal-hold,chronology,oc-status,claim-chart,brief-section-drafter,deposition-prep,privilege-log-review}/SKILL.md`。

### 11.2 需新建的后端文件

```
backend/app/
├── agents/litigation/
│   ├── __init__.py  agent.py  deps.py
│   ├── tools/  (_validators, profile_tools, matter_tools, demand_tools, analysis_tools, law_tools)
│   ├── prompts/ (security, matter_briefing, demand_draft, demand_received, subpoena_triage,
│   │             legal_hold, chronology, claim_chart, oc_status, brief_section, deposition_prep, privilege_log)
│   └── references/ (litigation-core-rules.md  ← 移植)
├── api/routes/v1/  litigation.py  litigation_ws.py
├── db/models/  litigation_profile.py  litigation_matter.py  litigation_matter_event.py
│              litigation_demand.py  litigation_analysis.py  litigation_notification.py
├── repositories/  litigation_profile_repo.py  litigation_matter_repo.py  litigation_matter_event_repo.py
│                  litigation_demand_repo.py  litigation_analysis_repo.py  litigation_notification_repo.py
├── schemas/litigation/  __init__.py _json.py profile.py cold_start.py matter.py matter_event.py
│                        demand.py analysis.py notification.py
├── services/  litigation_profile_service.py  litigation_cold_start_service.py  litigation_matter_service.py
│              litigation_demand_service.py  litigation_analysis_service.py  litigation_notification_service.py
├── tasks/  litigation_docket_watcher.py  litigation_deadline_rules.py
└── alembic/versions/  (2 个迁移文件，幂等守护)
更新：db/models/__init__.py  api/deps.py  api/routes/v1/__init__.py  scheduler.py
```

### 11.3 需新建的前端文件

```
frontend/src/
├── app/[locale]/(dashboard)/litigation/  (page + setup + matters[/new,/id] + demands[/id] + analyses[/id]
│                                          + chronology + claim-chart + subpoena + legal-hold + oc-status
│                                          + brief-section + deposition + privilege-log + settings)
├── app/api/litigation/[[...path]]/route.ts
├── components/litigation/  (RiskMatrix, SeverityBadge, PartyRoleSelector, ConflictGateBlock, WorkProductHeader,
│                            ReviewerNote, MatterTimeline, DeadlineBadge, DemandModeSelector, DemandGate,
│                            LetterDualView, ClaimChartTable, EvidenceReviewTable, SubpoenaCategoryBadge,
│                            FiveGroupSeparationNote, NextStepDecisionTree, PortfolioAnomalyList, ColdStartWizard)
├── hooks/use-litigation-chat.ts
├── lib/litigation.ts
└── types/litigation.ts
更新：components/layout/app-sidebar.tsx  lib/constants.ts  messages/{zh,en}.json
```

### 11.4 Required Verification（每阶段完成前）

后端：`uv run ruff check . --fix && uv run ruff format . && uv run ty check && uv run pytest`（含 `tests/litigation/` 与 `test_migrations`）。
前端：`bun run lint && bun test`。
端到端手测：① 冷启动向导（企业法务 vs 律所角色分支）贯通写画像；② 未配置 LLM 时 WS 报 `llm_not_configured`（不兜底）；③ 11 个 WS action 各跑一次（重点：demand 双模式 + 7 项发送门禁 + 对外去抬头、subpoena 5 分类 + 监察/刑事上报、legal-hold 三态 + next_refresh、claim-chart 缺口优先 + 草案盾、privilege-log 三态保守、brief-section 五组分离、matter-briefing 冲突门禁 + 陈旧度）；④ matter-intake（冲突门禁三路径）→ update（事件流 + deadline）→ portfolio（7 异常聚合）→ close（非律师门禁）；⑤ docket cron 手动触发产出案件进度通知；⑥ 设置页改一项画像写回生效；⑦ 非律师角色下 matter-close/update 接受和解触发律师审查门禁。

---

## 12. 设计决策小结（供审阅）

1. **法域 = 中国法**（民诉法/民诉法解释/证据规定/执行 + 民法典时效§188/195 + 律师法§38）：源为 `claude-for-legal-zh` 中文本地化版，**非**美国 FRCP/FRE/work product 制度。复用现有中文 RAG。
2. **范围 = 全量 17 技能 + customize(设置页) + 冷启动基础设施**；`matter-workspace` 延后（照 ip/privacy/employment 先例用实践级上下文，matters 以 user_id 归属）。额外纳入 overview 未列的 brief-section-drafter / deposition-prep / privilege-log-review（用户已确认）。
3. **架构 = 逐项镜像 ip**（最新同构样板）：传输层三分（11 WS 显式 action / REST CRUD+聚合 / docket cron 纯算术）、独立 profile 表（复制非共享）、迁移幂等守护、绝不兜底。
4. **数据模型 = 6 张表**（profile / matters 主表 / matter_events 事件流 / demands 信函生命周期 / analyses 统一 9 类 / notifications）——比 ip 多 matter_events（litigation 的案件有时间线，这是核心价值）。
5. **litigation 独有保真重点**：①**2 种工作成果抬头 + 中国法保密说明**（律师法§38、民诉法§67——美式 work product 中国无对应制度）②**五组内容分离**诉讼文书编辑纪律 ③风险量表双映射（监控/常规/优先/严重）④冲突门禁（利益冲突排查三路径 + 代号必须存在）⑤当事人角色分支（原告进攻 vs 被告防守）⑥律师函发送门禁 7 项 LOUD GATE + 对外去抬头（系统只产草稿不发送）⑦逐字引用纪律（卷宗逐字准确）⑧claim-chart 缺口优先 + 草案非认定盾 ⑨subpoena 步骤0 规则研究 + 监察/刑事上报 ⑩privilege-log 三态保守（宁标记过度）⑪docket-watcher 不直接排期（线索非日程，须律师核实）⑫非律师门禁（接受和解须律师审查）。

*文档生成时间：2026-06-12（v1.0）*
*基于 claude-for-legal-zh 争议解决模块 + LexMind 现行架构*
*架构逐项镜像 ip（知识产权）模块的真实实现*

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | issues_open | 7 issues, 1 critical gap |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **UNRESOLVED:** 0 (all issues have user decisions)
- **CRITICAL GAPS:** 1 (null guard crash in matter_tools.py:72)
- **ACTIONS APPROVED:** 6 (wire research_litigation_rules, fix N+1 portfolio, extract DRY helper, fix event count, fix null guards, write backend tests)
- **TODOS ADDED:** 2 (案件创建幂等防护, docket-watcher 每日扫描)
- **VERDICT:** Eng Review issues_open — 6 fixes + tests pending implementation. Run `/review` after fixes applied.
