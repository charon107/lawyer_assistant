# Lawyer-Assistant 仓库全面审查报告

**审查日期：** 2026-05-09  
**审查范围：** 全仓库架构冗余、历史死代码、重复实现  
**审查方法：** 三路并行深度扫描（agents/services/repos、frontend/root-files），逐文件阅读 + 全局引用搜索  

---

## 一、确认可删除的死代码/冗余文件

| # | 文件/目录 | 原因 | 严重度 |
|---|-----------|------|--------|
| 1 | `asset/` 目录 (`background-moon.png`, `background-sun.png`) | 与 `frontend/public/bg-moon.png`、`bg-sun.png` **完全相同**（MD5 一致），只是文件名不同。`frontend/public/` 是实际被服务的规范副本 | 🗑️ 可直接删除 |
| 2 | `frontend/src/hooks/use-projects.ts` | **空文件**（1 字节），全仓库零引用，未在 `hooks/index.ts` 中导出 | 🗑️ 可直接删除 |
| 3 | `frontend/src/stores/project-store.ts` | **空文件**（1 字节），全仓库零引用，未在 `stores/index.ts` 中导出 | 🗑️ 可直接删除 |

---

## 二、版本/变更日志不同步

| # | 文件 | 问题 | 建议 |
|---|------|------|------|
| 4 | 根目录 `VERSION` | 内容为 `0.2.0.0`，而 `backend/VERSION` 已更新为 `0.3.0.0`，版本脱节 | 同步为 `0.3.0.0` 或删除根目录版本文件，以 backend 为准 |
| 5 | 根目录 `CHANGELOG.md` | 只有 `0.2.0` 条目，缺失 `0.3.0`（多文档类型支持等功能）。`backend/CHANGELOG.md` 包含完整记录 | 同步最新条目或删除根目录版本，以 backend 为准 |

---

## 三、后端死函数（确认无人调用）

以下函数/符号经全局搜索确认**无外部调用方**，可安全删除：

| # | 函数/符号 | 文件位置 | 说明 |
|---|-----------|----------|------|
| 6 | `run_agent()` | `backend/app/agents/assistant.py:226` | 定义后从未被 import 或调用 |
| 7 | `load_contract_text()` | `backend/app/agents/lpa/document_preprocessor.py:251` | 兼容性包装函数，零引用 |
| 8 | `verify_chapters()` | `backend/app/agents/lpa/chapter_splitter.py:211` | 直通函数，零引用 |
| 9 | `get_contract_rule()` / `get_all_contract_rules()` | `backend/app/agents/rules/contract_rules.py` | 仅文件内定义，外部零调用 |
| 10 | `get_employment_rule()` / `get_all_employment_rules()` | `backend/app/agents/rules/employment_rules.py` | 仅文件内定义，外部零调用 |
| 11 | `get_nda_rule()` / `get_all_nda_rules()` | `backend/app/agents/rules/nda_rules.py` | 仅文件内定义，外部零调用 |
| 12 | 模块级 `register_tool` | `backend/app/agents/lpa/llm_client.py:18` | 被 import 但实际使用的是实例方法 `self._llm.register_tool()`，模块级符号从未生效 |

---

## 四、🔴 运行时 Bug（代码审查发现）

### Bug 1：`cross_checker.py` 调用不存在的方法

- **文件：** `backend/app/agents/lpa/cross_checker.py:54`
- **问题：** 调用 `self._llm.call()` 但 `LLMClient` 类没有 `call` 方法。该类只有 `chat()` 和 `agent_loop()` 两个公开方法。
- **影响：** 当 cross-check 阶段触发 LLM 调用时，运行时抛出 `AttributeError`，整个审查流水线中断。
- **修复：** 将 `self._llm.call(...)` 改为 `self._llm.chat(...)`，并适配参数签名。

### Bug 2：`fact_extractor.py` 参数名不匹配

- **文件：** `backend/app/agents/lpa/fact_extractor.py:131`
- **问题：** 调用 `self._llm.agent_loop(... user_prompt=...)` 但 `LLMClient.agent_loop()` 的签名参数名是 `user_message`。
- **影响：** 当 fact extraction 阶段触发 LLM agent loop 时，运行时抛出 `TypeError`，流水线中断。
- **修复：** 将 `user_prompt=` 改为 `user_message=`。

---

## 五、架构层面问题

### 5.1 业务逻辑泄漏到路由层

- **位置：** `backend/app/api/routes/v1/lpa_cases.py` 第 207-331 行
- **问题：** `_generate_summary_async()` 和 `_generate_analysis_async()` 两个函数包含约 120 行业务逻辑，直接操作 LLM agent、解析 JSON 响应、通过 `lpa_case_repo` 直接读写数据库。
- **影响：** 违反项目自身的 service-layer 分层约定（`AGENTS.md` 中明确要求 services 层处理业务逻辑）。测试困难，代码复用不可能。
- **建议：** 将这些逻辑迁移到 `LPACaseService` 或新建 `LPAAnalysisService`。

### 5.2 Repository 直接从路由层访问

- **位置：** `backend/app/api/routes/v1/agent.py:143-151`
- **问题：** 路由直接 import 并调用 `lpa_case_repo`（`get_case_by_id`、`get_documents_by_case`、`get_analyses_by_case`），绕过 service 层。
- **影响：** 同 5.1，违反分层架构。其他所有路由都通过 service 访问数据。
- **建议：** 通过 `LPACaseService` 封装这些查询。

### 5.3 ChatFile CRUD 重复实现

- **位置：** `backend/app/repositories/chat_file.py` 和 `backend/app/repositories/lpa_case_repo.py`
- **问题：** 两个 repository 都对 `ChatFile` 模型做 CRUD 操作：
  - `chat_file_repo.create()` — 创建 ChatFile
  - `lpa_case_repo.create_document()` — 创建 ChatFile（额外带 `case_id`）
  - `chat_file_repo.get_by_id()` ≈ `lpa_case_repo.get_document_by_id()` — 几乎相同的 `db.get(ChatFile, id)`
- **建议：** 统一到 `chat_file_repo`，`lpa_case_repo` 只做 case 级别的查询组合（如 `get_documents_by_case`），创建/删除 ChatFile 委托给 `chat_file_repo`。

### 5.4 内存会话存储

- **位置：** `backend/app/services/lpa_service.py:15`
- **问题：** `_sessions` 是模块级 `dict`，存储 LPA 审查流水线的会话状态。
- **影响：**
  - 服务器重启后会话丢失
  - 无 TTL 淘汰机制，长时间运行可能导致内存泄漏
  - 无法水平扩展（多实例间不共享）
- **建议：** 代码中已有注释 "migrate to Redis for production"。短期可加 TTL 淘汰，长期迁移到 Redis 或 SQLite。

### 5.5 `lpa_case_repo` 未注册到 `repositories/__init__.py`

- **位置：** `backend/app/repositories/__init__.py`
- **问题：** `__all__` 列表导出了 `user_repo`、`conversation_repo`、`chat_file_repo`、`conversation_share_repo`、`message_rating_repo`，唯独缺少 `lpa_case_repo`。
- **影响：** 不是 bug，但违反一致性。消费者需要使用 `from app.repositories import lpa_case_repo`（模块级 import）而非 `from app.repositories.lpa_case_repo import ...`。

### 5.6 未使用的 `base_url` 参数

- **位置：** `backend/app/services/lpa_chat_service.py:29`
- **问题：** `__init__` 接受 `base_url` 参数（默认 `https://api.deepseek.com`），但第 43 行硬编码了同一 URL，参数从未被使用。
- **影响：** 调用方传入自定义 `base_url` 会被静默忽略，造成误导。

### 5.7 关键词列表重复

- **位置：** `backend/app/agents/lpa/chapter_splitter.py` 的 `LPA_CHAPTER_KEYWORDS` vs `backend/app/agents/lpa/document_types.py` 的 `_LPA_CHAPTER_KEYWORDS`
- **问题：** 两处维护了几乎相同的 LPA 章节关键词列表。`document_types.py` 是 orchestrator 使用的规范版本，`chapter_splitter.py` 是向后兼容的默认值。
- **建议：** 统一到 `document_types.py`，`chapter_splitter` 从那里引用。

---

## 六、确认不冗余的部分 ✅

以下经逐文件审查确认**不是重复实现**，架构设计合理：

| 对比项 | 结论 |
|--------|------|
| `agents/skills/` vs `agents/lpa/` | **不同子系统** — skills 提供律师人格方法论（对话 agent 的领域专业知识），lpa 是文档审查自动化流水线。目的不同，无功能重叠。 |
| `model_factory.py` vs `llm_client.py` | **不同框架** — 前者为 PydanticAI 对话 agent 创建模型对象，后者是 LPA 流水线的独立 OpenAI 兼容客户端（自带 agent loop）。不可互换。 |
| `prompts/` 根目录 vs `agents/prompts.py` | **不同产品** — 前者是 LPA 流水线的 5 个 markdown 模板（chapter_split、review、cross_check 等），后者是对话 agent 的 2 个 Python 字符串常量。零重叠。 |
| `chat-store` vs `conversation-store` (前端) | **不同关注点** — 前者管理流式消息的临时状态（`messages[]`、`isStreaming`），后者管理会话元数据和 CRUD（`conversations[]`、`currentConversationId`）。两个 store 都被活跃使用。 |
| `/api/conversations` vs `/api/v1/admin/conversations` (前端路由) | **不同权限** — 前者代理用户端会话 API，后者代理管理员端 API（带 `requireAdmin` 检查）。 |
| `file_storage.py` vs `file_upload.py` | **分层合理** — 前者是基础设施层（文件存储抽象），后者是业务逻辑层（上传验证、解析、DB 记录）。`classify_file()` 的薄包装可接受。 |
| `.claude/rules/` vs `CLAUDE.md` vs `AGENTS.md` | **各有定位** — `.claude/rules/` 是 glob-scoped 的细粒度规则，`CLAUDE.md` 是 Claude 特有工作流指令，`AGENTS.md` 是通用 agent 简报。存在重叠但非冗余（见第七节设计债务）。 |
| `docker-compose.yml` vs `docker-compose.prod.yml` | **标准实践** — 前者本地构建，后者用预构建 GHCR 镜像。共享配置可优化但拆分本身合理。 |
| `scripts/server-setup.sh` | **仍然有用** — Ubuntu 24.04 一次性服务器 provisioning 脚本，引用了正确的仓库路径。 |

---

## 七、文档重叠（设计债务）

### 问题

`CLAUDE.md`（1206 行，14.8KB）与以下三个来源存在约 80% 内容重叠：

- `AGENTS.md`（53 行）— 通用 agent 简报
- `docs/` 目录（20 个文件）— 详细文档（architecture.md、patterns.md、testing.md 等）
- `.claude/rules/`（6 个规则文件）— glob-scoped 的代码规范

具体重叠内容：
- 架构约定 → `CLAUDE.md` + `docs/architecture.md` + `.claude/rules/architecture.md`
- 代码规范 → `CLAUDE.md` + `.claude/rules/code-style.md`
- 测试模式 → `CLAUDE.md` + `docs/testing.md` + `.claude/rules/testing.md`
- API 约定 → `CLAUDE.md` + `.claude/rules/api-conventions.md`
- Schema/Model 规则 → `CLAUDE.md` + `.claude/rules/schemas-models.md`

### 建议

`CLAUDE.md` 瘦身，只保留 Claude 特有的工作流规则（GStack/Superpowers discipline、feature/bug/refactor workflow），将通用内容通过引用指向 `docs/` 和 `AGENTS.md`。当前任何架构约定变更需要同步更新 3 处，维护成本高。

---

## 八、总结统计

| 类别 | 数量 |
|------|------|
| 可直接删除的文件/目录 | 3 项 |
| 版本/日志不同步 | 2 项 |
| 死函数（零引用） | 7 处（含 3 对 get_*_rule 函数组） |
| 运行时 Bug | 2 个（P0） |
| 架构分层问题 | 5 处 |
| 设计债务 | 2 处（文档重叠、关键词重复） |
| 确认不冗余的模块对 | 9 组 |

---

## 九、建议优先级

### 立即修（P0 — 运行时必崩）

1. `cross_checker.py:54` — `self._llm.call()` → `self._llm.chat()`
2. `fact_extractor.py:131` — `user_prompt=` → `user_message=`

### 快速清理（P1 — 5 分钟内完成）

3. 删除 `asset/` 目录
4. 删除 `frontend/src/hooks/use-projects.ts`
5. 删除 `frontend/src/stores/project-store.ts`
6. 同步根目录 `VERSION` 和 `CHANGELOG.md`

### 清理死代码（P2 — 需确认无外部调用方）

7. 删除 `run_agent()`、`load_contract_text()`、`verify_chapters()`
8. 删除 `rules/` 下的 `get_*_rule()` / `get_all_*_rules()` 函数组
9. 清理 `llm_client.py` 模块级未使用的 `register_tool` import

### 架构改进（P3 — 中期重构）

10. 将 `lpa_cases.py` 中的业务逻辑迁移到 service 层
11. 统一 ChatFile CRUD 到 `chat_file_repo`
12. `lpa_case_repo` 注册到 `repositories/__init__.py`
13. 移除 `LPAChatService` 中未使用的 `base_url` 参数
14. 统一 `chapter_splitter.py` 和 `document_types.py` 的关键词列表
15. 内存会话存储加 TTL 淘汰，长期迁移到 Redis

---

*报告生成工具：Hermes Agent /review 全仓库审查模式*  
*审查基于逐文件阅读 + 全局引用搜索，非静态分析工具猜测*
