# 仓库瘦身 — 执行报告（Phase 2–5）

> 日期：2026-06-02 · 分支：`chore/repo-slimming-dead-code`
> 配套审计：见同目录 [`dead-code-audit-2026-06-02.md`](./dead-code-audit-2026-06-02.md)
> 原则：零行为变更 · 仅删除 SAFE_REMOVE · 不重构/不优化/不引入抽象

---

## Phase 2 — 安全分类结果

| 项 | 分类 | 依据 |
|---|---|---|
| `components/chat/chat-widget.tsx` | **SAFE_REMOVE** | 0 引用；无 `next/dynamic`/字符串路径/barrel 引用 |
| `components/layout/breadcrumb.tsx` | **SAFE_REMOVE** | 0 引用；不在 `layout/index.ts` |
| `components/layout/landing-nav.tsx` | **SAFE_REMOVE** | 0 引用；不在 barrel |
| `components/ui/popover.tsx` | **SAFE_REMOVE** | 仅 barrel 转发，7 个导出符号 ui/ 外 0 消费 |
| `components/ui/scroll-area.tsx` | **SAFE_REMOVE** | 同上 |
| `components/ui/separator.tsx` | **SAFE_REMOVE** | 同上（其它 `.Separator` 来自别的 radix 包） |
| `@radix-ui/react-{popover,scroll-area,separator}` | **SAFE_REMOVE** | 仅被上述被删文件引入 |
| `tabula-py` | **SAFE_REMOVE** | 全树 0 import（`file_upload` 用 pypdf+python-docx） |
| `tqdm`（顶层声明） | **SAFE_REMOVE** | 0 直接 import；经 sentence-transformers 传递保留 |
| `python-multipart` 重复声明 | **SAFE_REMOVE** | 纯清单去重，包保留 |
| `python-dotenv` | **KEEP** | `config.py` `SettingsConfigDict(env_file=...)` 需要它解析 `.env`（否则启动 ImportError）→ 移除=环境变量行为变化 |
| `openai`（顶层声明） | **REVIEW_REQUIRED** | 与 `pydantic-ai-slim[openai]` extra 重复，但属清单判断，未动 |
| `commands/example.py`（模板）/`commands/cleanup.py`（空壳） | **REVIEW_REQUIRED** | 位于 `commands/**`，经 `register_commands` 运行时自动发现并注册为 CLI 命令；按运行时安全规则不静态删除 |
| `agents/**`,`schemas/**`,`repositories/**`,`services/**`,`core/**` | **KEEP** | 运行时加载，未在本次触碰 |
| admin 代理重复逻辑 / sidebar store / nav 数组 / chat hooks 克隆 | **REVIEW_REQUIRED** | 属重构，违反"仅瘦身"约束，未动 |

---

## Phase 3 — 执行 + 逐批验证

**基线（改动前）**：backend `ruff` 通过；backend `pytest` = **6 失败（预存）/ 520 通过 / 1 跳过**；frontend `build` exit 0；frontend `lint` = 5 error + 15 warning（均预存，含生成文件 triple-slash 与代理路由 `any`）。验收门槛：**不引入新失败**。

### Batch A — 前端孤儿 + 死 radix 依赖（commit `858c4df`）
- 删 6 文件 + `ui/index.ts` 移除 3 个 barrel 导出 + `package.json` 移除 3 个 radix 依赖；`bun install` 移除 3 包。
- 验证：`bun run build` **exit 0**；`lint` = 5 error / **14 warning**（少 1，landing-nav 警告消失），**无新增**。

### Batch B — 后端死依赖（commit `bca0796`）
- `pyproject.toml` 删 `tabula-py`、`tqdm`、`python-multipart` 重复行；`uv lock` 连带移除传递依赖 `pandas`、`python-dateutil`、`six`。
- 已核验 `app/`、`cli/` 无 pandas/dateutil/six 直接 import。
- 验证：`ruff` 通过；`pytest` = **6 失败（同一批预存）/ 520 通过**，**无新增失败**。

> 执行中插曲：`uv sync` 默认裁掉 dev extras（含 ruff/ty/pytest），改用 `uv sync --extra dev` 恢复，与依赖删除无关。

---

## Phase 4 — 验证

| 检查项 | 结果 |
|---|---|
| 后端启动 | ✅ `app.main:app` 导入成功，OpenAPI 生成 **57 条路由** |
| API 文档加载 | ✅ `app.openapi()` 正常生成 |
| auth 工作 | ✅ `/api/v1/auth/{login,register,refresh,logout,me}` 全部注册；auth 逻辑未改，相关测试在 520 通过内 |
| chat 端点 | ✅ `/api/v1/conversations*`、`/commercial*`、agent 路由齐全 |
| agent 初始化 | ✅ `agents.assistant`/`agents.commercial.agent`/`agents.tools.law_tools` 导入成功；agent 测试通过 |
| 前端启动 | ✅ 生产 `build` exit 0（全量编译+类型检查通过） |
| tabula/pandas 缺失安全 | ✅ `import tabula` 抛 ImportError 而 app 仍正常启动 |

---

## Phase 5 — 最终报告

### 1. 删除的文件（6）
```
frontend/src/components/chat/chat-widget.tsx
frontend/src/components/layout/breadcrumb.tsx
frontend/src/components/layout/landing-nav.tsx
frontend/src/components/ui/popover.tsx
frontend/src/components/ui/scroll-area.tsx
frontend/src/components/ui/separator.tsx
```

### 2. 删除的导出
- `ui/index.ts`：`Separator`、`ScrollArea`/`ScrollBar`、`Popover`/`PopoverTrigger`/`PopoverContent`/`PopoverAnchor`（随孤儿文件移除）

### 3. 删除的依赖
- **npm（直接，3）**：`@radix-ui/react-popover`、`@radix-ui/react-scroll-area`、`@radix-ui/react-separator`
- **Python（直接，2 + 1 去重）**：`tabula-py`、`tqdm`、`python-multipart`（重复声明）
- **Python（传递，4，随 tabula-py 移除）**：`pandas`、`python-dateutil`、`six`（+ tabula-py 本体）

### 4. LOC 缩减
- **源码：净 −343 行（新增 0 / 删除 343）** —— 纯删除
- 锁文件：`uv.lock` −92，`bun.lock` −13
- 新增文档（审计+本报告）：+126（不计入代码）

### 5. 仍待评审（REVIEW_REQUIRED，本次未动）
- `openai` 顶层声明冗余（与 extra 重复）
- `commands/example.py`（模板）、`commands/cleanup.py`（空壳）—— 运行时注册的 CLI 命令，删除会改变 CLI 表面
- admin catch-all 代理重复逻辑（`conversations`/`logs` 仅差 1 行）
- `sidebar-store.ts` ≡ `chat-sidebar-store.ts`；`Sidebar`/`AppSidebar` 导航数组重复；`use-chat`/`use-commercial-chat` 克隆 —— 均属重构

### 6. 风险摘要
- **整体风险：低。** 仅删除零引用的前端文件与零 import 的依赖；未触碰任何后端 `.py`、schema、auth、agent、prompt、env。
- 行为不变量全部满足：API 契约、DB schema、auth 流程、前端行为、agent/prompt 行为、环境变量 —— 均无变化。
- 预存的 6 个 pytest 失败（`test_law_parser_categories` ×2、`test_migrations` ×4）与本次无关，未做修改（超出瘦身范围）。
- `ty check` 30 项诊断、frontend lint 5 error 均为预存，未因本次变更增加。
