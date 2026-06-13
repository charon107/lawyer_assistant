# Changelog

All notable changes to this project will be documented in this file.

## [0.12.0.0] - 2026-06-13

### Added

- **争议解决模块前端对齐（Litigation 前端）**: 将 litigation 模块前端提升到与 ip / privacy 模块一致的规范，补齐后端早已就绪但前端缺失的能力。
  - **9 个分析类技能页**: 案件简报、大事记、要件分析、调查令分流、证据保全、对方动态、书状片段、询问准备、特权清单——均为可用页面，运行后跳转分析详情。
  - **律师函创建流**: 新增 `demands/new` 页，覆盖 demand_draft / demand_received 两个 WS 动作（先建律师函记录再流式生成），消除「新建」死链。
  - **案件事件创建页**: 新增 `matters/[id]/events/new`，可登记事件类型 / 日期 / 摘要 / 到期日 / 期限状态，消除「添加事件」死链。
  - **共享组件三件套**: 新增 `components/litigation/` —— badges（严重度 / 分析类型 / 案件状态 / 律师函模式与状态 / 风险）、通知区、技能运行器（带可选案件选择器）。
  - **着陆页改造**: 渲染通知区，QUICK_ACTIONS 扩展到全部技能入口，内联 badge 替换为组件。

### Changed

- **litigation 全量国际化**: 模块内 13 个页面从硬编码中文迁移到 next-intl，`messages/zh.json` 与 `messages/en.json` 各新增完整 `litigation` 翻译块（中英双语，全枚举标签覆盖）。

## [0.11.0.0] - 2026-06-12

### Added

- **争议解决模块（Litigation-Legal）**: 第 6 个法律领域模块，覆盖诉讼案件全生命周期管理（《民事诉讼法》《民诉法解释》《民事诉讼证据规定》、执行程序、《民法典》诉讼时效、《律师法》）。
  - **冷启动向导**: 按执业角色分支（企业法务 / 律所律师 / 独立执业）的引导式设置，支持快速与完整模式。
  - **案件中枢**: 案件登记（含利益冲突门禁）、事件流时间线、进展追加、结案归档（非律师操作记录律师审查提示）、案件组合概览（风险分布 / 期限 / 7 类异常）。
  - **11 个 AI 技能（WebSocket 流式）**: 案件深度简报、律师函起草、来函分流、调查令/协查分流、证据保全、大事记构建、要件分析表、外部律师状态请求、书状段落起草、庭前质证准备、证据三性审查。
  - **律师函生命周期**: REST 建档 + WS 起草，内部草稿（带工作成果抬头）与对外版本（去抬头）双栏，发送前门禁；系统只产草稿、绝不实际发送。
  - **案件进度定时代理（docket-watcher）**: 每周一巡检活跃案件，按审限规则纯算术分桶预警（逾期 / 7 日 / 8-30 日 / 31-90 日 / 态势变化），不调 LLM；推算期限标注为线索而非日程。
  - **中国法保真**: 2 种工作成果抬头（律师/非律师）+ 中国法保密说明（律师法§38、民诉法§67，美式 work-product 制度中国无对应）；五组内容分离诉讼文书编辑纪律；风险量表双映射；逐字引用纪律。
  - **设置与分析历史**: 实务画像可视化编辑、分析产出按 9 类筛选查看。
  - **中英文 i18n**: 全部页面支持中英切换。

### Fixed

- **法条检索工具崩溃**: `research_litigation_rules` 误以同步方式调用 async `search_law` 且参数错位，会运行时崩溃（实为未接线死代码）；改为返回画像上下文，检索交由工厂单独挂载的 `search_law`。
- **模型严重性值信任边界**: `save_analysis` 写入模型给的 severity 未校验，非法值（如中文「严重」）会让分析读取端点 pydantic Literal 校验 500；现在写入前归一化到合法集。
- **案件期限分桶**: docket-watcher 字段名误导（`due_7` 实装 8-30 日）已正名；已结清（met）期限不再误报；态势变化桶从近 7 天非期限事件填充。
- **案件组合 N+1 查询**: portfolio 聚合改为一次性取每案最近事件日期。

### Tests

- 新增 `tests/litigation/`（27 测试）: 冷启动状态机、案件/律师函/分析服务、事件 repo、docket 算术、docket-watcher、law-tool 回归、severity 信任边界、agent 工厂一致性。

## [0.10.0.0] - 2026-06-10

### Added

- **知识产权模块（IP-Legal）**: 第5个法律领域模块，覆盖商标、著作权、专利、商业秘密与开源合规（《商标法》《专利法》《著作权法》《反不正当竞争法》）。
  - **冷启动向导**: 6步引导式设置（角色含专利代理师/业务与IP组合/维权姿态/品牌监测/种子文件/生成），支持快速模式（3步）与完整模式（6步）。
  - **8 个 AI 技能（WebSocket 流式）**: 商标可注册性初筛、专利自由实施（FTO）初筛、发明披露初筛、侵权初步分析（商标/著作权/专利/商业秘密四态）、合同 IP 条款审查、开源许可证合规、侵权警告函（发送/接收双模式）、网络传播权通知（发送/回应/反通知三模式）。
  - **维权信函生命周期**: REST 建档 + WS 起草，内部草稿（带工作成果抬头）与对外版本（去抬头）双栏，发送前确认门禁；系统只产草稿、绝不实际发送。
  - **知识产权组合登记册**: 商标/专利/著作权/域名注册管理，按管辖地规则纯算术推算续展期限并按紧急度分桶预警。
  - **续展定时代理**: 每周一巡检组合，宽展/即将到期事项推送通知（不调 LLM）。
  - **专利代理师特权保真**: 4 种工作成果抬头按角色×事项类型分支（《专利代理条例》第17条）；clearance/fto「初步非意见」免责盾；专利法§71 故意侵权警告；外观设计早分流给设计律师。
  - **设置与审查历史**: 实务画像可视化编辑、分析产出按类型筛选查看。
  - **中英文 i18n**: 全部页面支持中英切换。

### Fixed

- **认证守卫整页刷新卡死**: 修复 0.9.0.0 引入的 `hasAuthCookie()` 逻辑——auth cookie 为 httpOnly、JS 永远读不到，导致整页刷新或直达 dashboard URL 永久卡在「正在验证身份…」。现已在会话已认证时清除 loading 态。影响全部模块（dashboard/commercial/corporate/employment/privacy/ip）。
- **续展期限算术修正**: 著作权（无续展）不再误入「状态不明」分桶；专利期限与年费仅以申请日为锚（弃用 grant_date 兜底，避免已失效专利被显示为有效）；马德里续展限定为商标；宽展期月份计算改用当月实际末日（此前最多早 3 天）。

### Maintenance

- 新增知识产权模块数据库迁移（ip_profiles / ip_reviews / ip_enforcement / ip_portfolio / ip_notifications 五表，幂等守护）。
- 新增续展定时代理（周一 09:47，纯算术）+ 后端测试（tests/ip，17 项）。

## [0.9.0.0] - 2026-06-09

### Added

- **个人信息保护合规模块（个保法）**: 第4个法律领域模块，覆盖《个人信息保护法》全生命周期合规。
  - **冷启动向导**: 6步引导式设置（身份/监管足迹/DPA偏好/PIA触发条件/DSAR流程/就绪确认），支持快速模式（4步）和完整模式（6步）。
  - **用例分类**: AI 对话式分析，按处理目的/数据类型/规模/主体自动判定 PROCEED/PIA_REQUIRED/DPIA_MANDATORY/STOP 四类。
  - **DPA 审查**: 支持数据处理者/受托处理者双方向审查，AI 逐条分析个人信息处理协议条款。
  - **PIA 生成**: 自动生成个人信息保护影响评估报告，覆盖合法性基础、必要性、安全措施、数据主体权利。
  - **合规差距分析**: 按监管要求逐项对比现状，输出差距清单与整改建议。
  - **政策监控**: 双模式——主动检索最新法规动态（查询模式）与定时任务推送（扫描模式）。
  - **DSAR（数据主体权利请求）**: 完整闭环管理——登记/分类/身份验证/系统定位/豁免分析/起草确认函与实质回复函。
  - **审查历史**: 按类型筛选查看所有 AI 审查记录，支持详情页查看完整 Markdown 输出。
  - **通知中心**: 策略扫描提醒等通知列表，支持已读标记。
  - **配置管理**: 监管足迹、数据驻留、DPO 信息、自定义合规档案的可视化编辑。

### Changed

- **前端全面 i18n**: 隐私模块所有页面支持中英文切换，表情符号与可翻译文本分离。
- **注册/登录错误处理增强**: 前端代理路由正确解析 FastAPI 422 验证错误数组与自定义应用错误对象，表单错误提示不再显示通用 500 页面。
- **认证守卫优化**: 检测到已存在的 auth cookie 时乐观渲染页面内容，消除页面加载时的全屏 loading 闪烁。
- **API 客户端错误处理**: `ApiError.message` 始终为字符串，避免数组 `detail` 导致的 `[object Object]` 错误显示。

### Maintenance

- 新增隐私模块数据库迁移（privacy_profile / privacy_dsar / privacy_review / privacy_notification 四表）。
- 后端测试覆盖隐私模块完整流程（test_privacy_flow.py, 11 tests）。

## [0.8.0.1] - 2026-06-03

### Changed

- **劳动用工模块提示词法律保真度提升**: 从源 SKILL.md 逐字补全 7 个 Agent 提示词（termination/hiring/worker-classification/policy/wage-hour/handbook/expansion），将对 CLAUDE.md/文件路径的引用映射为本系统工具调用。
  - 解除审查：完整高风险标记表（8 项，含 id）、工时制度分类错误三条件触发、N/2N 经济补偿与赔偿金区分、解除当日检查清单、非律师后续行动门槛。
  - 录用审查：竞业限制《劳动合同法》第23-24条三要件、试用期第19条、要约效力、告知义务第8条、禁止扣证收财第9条。
  - 劳动关系认定：前瞻性硬门槛、劳社部发〔2005〕12号三要素、差距分析 🔴/🟡/✅。
  - 工资工时：加班费计算基数框架（基数认定 + 150%/200%/300% + 公式 + 21.75 + 仲裁时效一年 + 省级叠加）。
  - 制度起草/更新：《劳动合同法》第4条民主程序与公示、省级补充条款、连锁影响 diff。
  - 异地扩张：直接用工/劳务派遣/业务外包结构框架、新地域清单。
  - 全部沿用来源标注纪律（[法条原文]/[需核实]）与"不自作补充"三值选择。

### Maintenance

- **CI Action 版本统一升级**（Node 24 兼容）: actions/checkout v4→v6、docker/setup-buildx-action v3→v4、docker/login-action v3→v4、docker/build-push-action v6→v7；appleboy/ssh-action 维持 v1.2.5（sha 钉住）。

## [0.8.0.0] - 2026-06-03

### Added

- **劳动用工模块（Employment-Legal）**: 全新第3个业务模块，覆盖招聘审查、解除审查、假期管理、内部调查、地域扩张等 16 项技能。
  - 后端数据层：6 个 SQLAlchemy 模型（employment_profile、employment_review、leave_registration、employment_investigation、employment_expansion、employment_notification）+ Alembic 迁移 + 6 个 Repository
  - 后端服务层：冷启动状态机（6 步向导）、画像管理、审查历史、假期登记、调查管理、扩张管理、通知服务
  - 后端技能引擎：9 个 Agent 技能（hiring/termination/classification/policy/wage_hour/handbook/expansion/inv_query/inv_memo/inv_summary）+ PydanticAI tools
  - 后端 API：REST 端点（/api/v1/employment/*）+ WebSocket 端点（/ws/employment）+ 假期追踪定时任务
  - 前端页面：概览、冷启动向导、用工审查、假期管理、调查管理、地域扩张、设置（共 10 个页面）
  - 前端组件：审查类型选择器、高风险标记徽章、假期表单、假期紧急度徽章、通知区域
  - 前端基础设施：API 客户端、WebSocket hook、代理路由、i18n 中英文翻译

## [0.7.1.0] - 2026-06-03

### Added

- **VDR 数据室文件上传**: 交易工作区「数据室」标签页支持直接上传 PDF、Word、文本等文件，AI 可读取文件内容进行尽调提取。
  - 后端新增 `POST /deals/{deal_id}/vdr/upload` 端点，支持 multipart/form-data 文件上传
  - `VdrService.create_with_file` 存储文件并解析内容到 `parsed_content` 字段
  - `read_vdr_documents` 工具增强：优先返回已解析内容，AI 可读取文件实际文本
  - 前端 `apiClient.upload()` 方法支持 FormData 上传
  - Next.js 代理路由自动检测并转发 multipart 请求
  - 数据室标签页「新增」改为「上传文件」，支持 PDF/DOCX/TXT/CSV/MD

## [0.7.0.2] - 2026-06-03

### Fixed

- **公司并购模块宽度修复**: 移除概览、交易列表、交易工作区三处页面多余的 `max-w-5xl` 居中约束，改用 `w-full`，让内容随侧边栏自适应铺满可用宽度。

## [0.7.0.1] - 2026-06-03

### Changed

- **公司并购模块 UI 排版优化**: 概览、交易列表、交易工作区三处页面的间距与文字层级全面调整，修复文字拥挤、排版不整齐问题。
  - 容器宽度 `max-w-4xl` → `max-w-5xl`，水平内边距 `px-4` → `px-6`
  - 标题区、卡片、列表项的垂直间距统一加大（`gap-2` → `gap-3`/`gap-4`，`p-4` → `px-5 py-4`/`p-6`）
  - 表单字段通过 `Field` 组件统一 `mt-1.5` 与 Label 分离
  - Tab 栏按钮加大点击区域，非活跃态加 hover 反馈
  - 空状态占位符 padding 加大，文字层级统一

## [0.7.0.0] - 2026-06-02

### Added

- **商事合同配置差异化（三维度）**: 冷启动向导的「配置方式」选择现在真正影响后续流程与审查，对齐 `claude-for-legal-ZH` 设计。
  - **深度门控**: 快速模式只走 2 步（配置方式 + 团队信息）并产出"默认值"画像；完整模式走全部 5 步。`commercial_profiles` 新增 `setup_depth` 列。
  - **角色护栏（UPL）**: 新增 `used_by` 列；非法务角色下输出切换为"研究框架"，并在有法律后果的动作前提示先经律师审阅。
  - **方向一致性**: 审查技能共享提示词强制只读匹配方向（销售/采购）的合同手册，绝不跨侧适用。
- **确定性放绿护栏**: `write_contract_review` 在快速/默认值配置或缺匹配方向手册时，自动将"绿/可签"结论降级为"黄"，不依赖模型自觉。

### Changed

- 冷启动状态机由固定 5 步改为按深度驱动步数；`read_practice_profile` 在画像顶部呈现角色/方向/深度授权横幅。

## [0.6.0.1] - 2026-05-21

### Fixed

- **Alembic Migration Conflict**: Fixed `sqlite3.OperationalError: table already exists` during deployment. `create_all()` now runs only in dev/local environments; production relies solely on Alembic migrations.
- **Idempotent Migrations**: `law_metadata` and `document_analyses` table migrations now safely skip if tables already exist from prior `create_all` runs.

## [0.6.0.0] - 2026-05-18

### Added

- **Universal Document Review**: Prompts rewritten for generic contract review (租赁、买卖、服务等), LPA-specific prompts preserved in `prompts/lpa/`
- **Document Type Support**: API route accepts `document_type` parameter, 14 document types configured
- **Chapter Splitting for Chinese Contracts**: New regex pattern for "一、"、"二、" numbered sections
- **Contract Summary Tab**: "关键事实" renamed to "合同摘要" with Chinese field labels

### Fixed

- **MiMo Tool Calling**: Fixed empty arguments by improving tool description, system prompt consistency, and adding empty args detection with retry
- **Progress Bar Stuck at 0%**: Fixed async callback that silently swallowed progress updates
- **Duplicate Findings**: WebSocket and fetchFullResult data no longer accumulate duplicates
- **Report Not Loading**: fetchFullResult now stores reportMarkdown from backend
- **JSON Truncation**: Increased max_tokens for complex review and cross-check (8192→16384)
- **Chapter Title Garbled**: Fixed regex to properly identify Chinese contract section headers

## [0.5.0.0] - 2026-05-16

### Added

- **ChatGPT-Style Tool Status**: Compact status indicators during tool execution (e.g., "检索法律知识库...") instead of raw tool call cards
- **Collapsible Tool Details**: Tool call details collapsed by default after completion, expandable via "查看工具调用详情" toggle
- **ToolStatusIndicator Component**: Spinner + label component for streaming tool status display
- **Backend tool_status Event**: User-friendly status labels emitted before raw tool_call events

### Fixed

- **PDF Upload Stuck at Idle**: Review detail page now auto-connects WebSocket when review is still in progress, fixing the stuck-at-0% bug after upload redirect
- **Duplicate Agent Icons**: Prevented multiple agent avatars from appearing during tool-call loops — one icon per assistant turn
- **Duplicate Type Interface**: Removed duplicate `ToolStatusEvent` declaration in chat types
- **API Proxy Route**: Added Next.js catch-all route for `/api/v1/lpa/review/*` to enable local development without nginx

## [0.4.0.0] - 2026-05-15

### Added

- **LexMind Design System**: Complete visual rebrand with professional, modern design language
- **Design Documentation**: DESIGN.md with brand guidelines, color tokens, typography scale, and component specs
- **Design Preview**: Interactive HTML preview showcasing all design system components
- **Persistent Sidebar**: New AppSidebar component with navigation, user info, and controls
- **App Icon**: Custom icon.png for favicon and brand identity
- **Language & Theme Controls**: Moved to sidebar bottom for better accessibility

### Changed

- **Dashboard Layout**: Removed top header bar, simplified to sidebar + content layout
- **Landing Page**: Redesigned with LexMind branding and improved hero section
- **Dashboard Page**: Updated stat cards and case list with new design tokens
- **Settings Page**: Applied design system styles
- **Profile Page**: Applied design system styles
- **Auth Pages**: Updated login/register with new brand icon
- **Global Styles**: Replaced with design system CSS variables and tokens
- **Color System**: Migrated to warm gray (Stone) palette, deep indigo brand colors
- **Typography**: Unified to DM Sans family with structured type scale

### Removed

- **Polish Language**: Removed PL locale support (zh/en only)
- **Header Component**: Removed from dashboard layout (controls moved to sidebar)

### Fixed

- **Translation Keys**: Added missing `landing.register` translation for zh/en
- **Icon Conflict**: Resolved Next.js conflicting public/page file error for icon.png

## [0.3.0.0] - 2026-05-08

### Added

- **Multi-Document-Type Support**: Generalized the review pipeline to support contract, NDA, and employment contract types beyond LPA
- **Document Type Configurations**: `document_types.py` with configs for lpa, contract, nda, employment — chapter keywords, entity patterns, fact tool schemas, risk rules, and prompt templates
- **Risk Rule Modules**: Separate rule modules for contract (15 rules), NDA (12 rules), and employment (13 rules) contracts
- **Document Type Selector**: Frontend dropdown in cases UI to choose document type when creating a case
- **Document Type Badges**: Visual indicators for non-LPA document types in case list and detail views
- **Pipeline Parameterization**: All pipeline agents now accept `document_type` parameter to use type-specific configurations
- **API Proxy Fix**: Updated catch-all route from `[...path]` to `[[...path]]` for proper Next.js path forwarding
- **Test Coverage**: 69 new tests validating all document type configurations (rule structure, keyword maps, rule classification)

### Changed

- **LPA Rule Classification**: Fixed simple_rule_ids to include A2 and A3 rules
- **Pipeline Agents**: Fact extractor, chapter reviewer, chapter splitter, orchestrator, and report generator now use document-type-specific configs
- **Frontend i18n**: Updated translations for document types in English, Chinese, and Polish

### Fixed

- **API Proxy Route**: Fixed catch-all route pattern that was causing 404 errors on API forwarding

## [0.2.0.0] - 2026-05-08

### Added

- **LPA Case Management**: Create, view, edit, and delete legal cases with full CRUD operations
- **Document Upload**: Upload PDF, DOCX, and TXT files to cases with automatic content parsing
- **AI Document Summaries**: Automatic LLM-generated summaries for uploaded legal documents
- **Case-Scoped Chat**: Discuss specific cases with AI, with document context injected into the system prompt
- **Cases Dashboard**: New frontend pages for case list, case detail, and case chat
- **API Proxy Routes**: Next.js catch-all proxy for `/api/lpa-cases/*` endpoints
- **Internationalization**: Cases UI translated to English, Chinese, and Polish
- **Navigation**: Cases link added to header and sidebar with Briefcase icon
- **Test Coverage**: 106 new tests covering repository, service, routes, schemas, and case context

### Changed

- Non-admin users now redirect to `/cases` after login instead of dashboard
- Backend agents modernized to use `str | None` instead of `Optional[str]`
- Import sorting standardized across all backend modules

### Fixed

- Pre-existing test failure in `test_agents.py` caused by outdated mock of `OpenAIResponsesModel`
