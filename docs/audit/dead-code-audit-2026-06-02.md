# 仓库审计报告 — 死代码 / 死依赖 / 孤儿文件 / 未用导出 / 重复逻辑

> 日期：2026-06-02
> 范围：`backend/`（app + cli）+ `frontend/src/`
> 性质：**只识别，未删除、未改动任何代码。**
> 方法：依赖逐项 import 核查 · ruff(F401/F811/F841) · 基于路径与符号的引用扫描 · catch-all 代理 diff。
> 关联：见同目录《架构重复审计》（sidebar store / nav 数组 / chat hooks 等结构性重复）。

---

## 摘要

| 类别 | 确认数量 |
|---|---|
| 死依赖（backend） | 3（+1 冗余声明，+1 重复条目） |
| 死依赖（frontend） | 3 |
| 孤儿文件（frontend） | 6 |
| 死/空壳代码（backend） | 2 |
| 重复逻辑 | 1（admin 代理）+ 交叉引用架构报告 |

backend 的 import 卫生良好：`ruff --select F401,F811,F841` **全部通过**，无未用导入/变量。问题集中在**模块级 / 依赖级**——ruff 不覆盖这一层。

---

## 1. 死依赖（Dead Dependencies）

### 1.1 后端 `backend/pyproject.toml`

| 依赖 | 证据 | 结论 |
|---|---|---|
| `tqdm>=4.66.0` | 全仓仅出现在 `pyproject.toml:25`，无任何 `import tqdm` | **死依赖**，可移除 |
| ~~`python-dotenv>=1.0.0`~~ | **更正（2026-06-02 复核）**：无直接 `import dotenv`，但 `core/config.py` 使用 `SettingsConfigDict(env_file=find_env_file())`，pydantic-settings 的 `DotEnvSettingsSource` **必须**安装 `python-dotenv` 才能解析 `env_file`（否则启动抛 `ImportError`）。 | **KEEP**（必需的间接依赖；移除将破坏 `.env` 加载 = 环境变量行为变化） |
| `tabula-py>=2.10.0` | 词边界搜索 `\btabula\b` **0 命中**（此前的"命中"实为 `tabulate` 子串）；该库为重型依赖（需 Java/JVM） | **死依赖**，优先移除（体积/JVM 负担大） |

### 1.2 后端 — 声明问题（非删除，是修正）

| 问题 | 证据 | 建议 |
|---|---|---|
| `openai>=1.40.0` 顶层声明冗余 | 无直接 `import openai`；已由 `pydantic-ai-slim[openai]` extra 传递引入 | 删除顶层显式声明，避免版本双轨；功能不受影响 |
| `python-multipart` **重复声明** | `pyproject.toml` 同时列出 `python-multipart>=0.0.20`（第 16 行）与 `python-multipart>=0.0.12`（第 21 行） | 合并为一条（保留 `>=0.0.20`） |

### 1.3 前端 `frontend/package.json`

| 依赖 | 证据 | 结论 |
|---|---|---|
| `@radix-ui/react-popover` | 仅被 `ui/popover.tsx` 引入，而该组件在 ui/ 之外 **0 消费**（代码中 `popover` 命中均为 Tailwind 颜色类 `bg-popover`） | **死依赖** |
| `@radix-ui/react-scroll-area` | 仅被 `ui/scroll-area.tsx` 引入，`ScrollArea`/`ScrollBar` 在 ui/ 之外 **0 消费** | **死依赖** |
| `@radix-ui/react-separator` | 仅被 `ui/separator.tsx` 引入，`Separator` 在 ui/ 之外 **0 消费**（其它 `.Separator` 命中来自 `DropdownMenuPrimitive`/`SelectPrimitive`，是不同 radix 包） | **死依赖** |

> 反向确认：`@radix-ui/react-tooltip` **在用**（`TooltipProvider` → `app/providers.tsx:7`；admin 页里的 `<Tooltip>` 是 recharts 的）。其余 radix 组件（accordion/dialog/dropdown/select/tabs/avatar/label/slot/alert-dialog）均有真实消费。

---

## 2. 孤儿文件（Orphan Files）— 前端

确认从未被 import、JSX 引用、barrel 转发或 `next/dynamic` 动态加载：

| 文件 | 导出 | 证据 |
|---|---|---|
| [`components/chat/chat-widget.tsx`](../../frontend/src/components/chat/chat-widget.tsx) | `ChatWidget` | `ChatWidget`/`chat-widget` 全仓 0 引用 |
| [`components/layout/breadcrumb.tsx`](../../frontend/src/components/layout/breadcrumb.tsx) | `Breadcrumb` | 不在 `layout/index.ts` barrel 中，0 引用 |
| [`components/layout/landing-nav.tsx`](../../frontend/src/components/layout/landing-nav.tsx) | `LandingNav` | 0 引用 |
| [`components/ui/popover.tsx`](../../frontend/src/components/ui/popover.tsx) | `Popover*` | 仅 `ui/index.ts:61` 转发，0 消费 |
| [`components/ui/scroll-area.tsx`](../../frontend/src/components/ui/scroll-area.tsx) | `ScrollArea`,`ScrollBar` | 仅 `ui/index.ts:44` 转发，0 消费 |
| [`components/ui/separator.tsx`](../../frontend/src/components/ui/separator.tsx) | `Separator` | 仅 `ui/index.ts:31` 转发，0 消费 |

> 后 3 个 ui 文件与第 1 节 1.3 的 3 个死 radix 依赖一一对应——移除组件文件即可同时移除依赖。

---

## 3. 死代码 / 空壳（Dead & Stub Code）— 后端

命令系统经 `cli/commands.py:266 register_commands(cmd_cli)` 自动发现 `app/commands/` 下全部模块，因此以下文件**已注册但内容为脚手架**：

| 文件 | 性质 | 证据 |
|---|---|---|
| [`commands/example.py`](../../backend/app/commands/example.py) | **模板脚手架** | 文件 docstring：「This is a template … Copy this file and modify it」；仅注册一个 `hello` 问候命令 |
| [`commands/cleanup.py`](../../backend/app/commands/cleanup.py) | **空壳（no-op）** | 函数体含 `# Add your cleanup logic here` 与 `deleted_count = 0  # Replace with actual count`，不执行任何真实清理 |

> `commands/seed.py` 含真实逻辑（`get_db_session` + 数据写入），保留；如确认未使用可单独评估。
> 一致性提示：`cleanup.py` 用同步 `SessionLocal`，`seed.py` 用 `get_db_session`，命令层 session 用法不统一（非死代码，记录备查）。

---

## 4. 未用导出（Unused Exports）

| 导出 | 文件 | 说明 |
|---|---|---|
| `Popover`,`PopoverTrigger`,`PopoverContent`,`PopoverAnchor` | `ui/popover.tsx` | 随孤儿文件一并未用 |
| `ScrollArea`,`ScrollBar` | `ui/scroll-area.tsx` | 同上 |
| `Separator` | `ui/separator.tsx` | 同上 |
| `ChatWidget` / `Breadcrumb` / `LandingNav` | 见第 2 节 | 同上 |

> **工具缺口**：仓库未配置自动检测 TS 未用导出/文件的工具，本节为手工核查结果，可能不完全。建议引入 `knip`（覆盖 unused files / exports / deps）以持续守护。

---

## 5. 重复逻辑（Duplicated Logic）

### 5.1 Admin catch-all 代理处理器近乎逐字重复
- [`api/admin/conversations/[[...path]]/route.ts`](../../frontend/src/app/api/admin/conversations/[[...path]]/route.ts)（36 行）
- [`api/admin/logs/[[...path]]/route.ts`](../../frontend/src/app/api/admin/logs/[[...path]]/route.ts)（36 行）
- **证据**：两文件 `diff` 仅 1 行不同——后端路径前缀 `/api/v1/admin/conversations` vs `/api/v1/admin/logs`。`system`(62)/`users`(65) 体量更大但同模式。
- **建议**：抽出共享 `createAdminProxy(prefix)` 工厂，各路由只传前缀。

### 5.2 交叉引用《架构重复审计》
- `sidebar-store.ts` ≡ `chat-sidebar-store.ts`（逐字重复）
- `Sidebar` / `AppSidebar` 的 `navigation`+`adminNav` 数组逐字重复
- `use-chat.ts` / `use-commercial-chat.ts`（文档承认的克隆）

---

## 6. 建议处理顺序（仅供参考，未执行）

1. **零风险**：移除 `tqdm`、`python-dotenv`、`tabula-py`；去重 `python-multipart`；删冗余 `openai` 顶层声明。（重跑 `uv run pytest` 验证）
2. **低风险**：删 6 个孤儿前端文件 + 对应 3 个死 radix 依赖；`example.py`/`cleanup.py` 脚手架。（重跑 `bun run build` + `bun test`）
3. **小重构**：5.1 代理工厂；架构报告的 sidebar store / nav 数组合并。
4. **守护**：接入 `deptry`（Python 死依赖）+ `knip`（TS 死依赖/导出/文件）到 CI。

---

## 附：已核查、确认**非**问题

- `services/agent.py` vs `agent_stream.py`、`routes/commercial.py` vs `commercial_ws.py`、四个 `law_*` 命令、`law_search.py` vs `law_data/`、`lib/api-client.ts` vs `lib/server-api.ts` — 均为正当职责拆分。
- 前端其余依赖（recharts / react-markdown / rehype-highlight / remark-gfm / sonner / react-query / cva / tailwind-merge / clsx / nanoid / next-intl）均有真实使用。
- backend `ruff F401/F811/F841` 全过。
