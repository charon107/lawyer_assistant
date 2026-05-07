# LPA Review App — Bug Report & Gap Analysis

**审计日期**: 2026-05-04  
**测试文件**: `docs/Sample-Cornerstone-LPA-10.08.21.pdf`  
**目标用户**: 律所客户部署  

---

## 一、致命 Bug（会导致系统完全不可用）

### BUG-001: ChapterReviewer 参数名错误 — Stage 3 完全崩溃

**文件**: `backend/app/agents/lpa/chapter_reviewer.py`  
**行号**: 79, 96  

**问题**: `_review_simple()` 和 `_review_complex()` 调用 `self._llm.chat()` 时传入 `user_prompt=`，但 `LLMClient.chat()` 的参数名是 `user_message`。

```python
# chapter_reviewer.py 第 77-82 行（_review_simple）
resp = self._llm.chat(
    system_prompt=system_prompt,
    user_prompt=user_prompt,       # ❌ 错误！应为 user_message
    model=self.V3_MODEL,
    temperature=0.1,
)

# chapter_reviewer.py 第 94-101 行（_review_complex）
resp = self._llm.chat(
    system_prompt=system_prompt,
    user_prompt=user_prompt,       # ❌ 错误！应为 user_message
    model=self.R1_MODEL,
    temperature=0.1,
    max_tokens=8192,
)
```

**影响**: 每次章节审查（Stage 3）都会抛出 `TypeError: chat() got an unexpected keyword argument 'user_prompt'`。**整个 LPA 审查流水线在有 API Key 的情况下完全无法工作**。异常会被 `except Exception` 捕获并返回空 findings，导致报告中所有章节都显示"未发现风险"——这比崩溃更危险，因为用户会误以为合同没有问题。

**修复方法**:
```python
# 将两处 user_prompt=user_prompt 改为 user_message=user_prompt
resp = self._llm.chat(
    system_prompt=system_prompt,
    user_message=user_prompt,      # ✅ 修正
    model=self.V3_MODEL,
    temperature=0.1,
)
```

**严重程度**: 🔴 致命 — 核心审查功能完全失效，且静默失败会误导律师

---

### BUG-002: 前端 `fetchFullResult` 永远无法获取数据

**文件**: `frontend/src/hooks/use-lpa-review.ts`  
**行号**: 183-200  

**问题**: 当用户直接通过 URL 访问 `/review/{id}` 页面时，hook 初始化 `reviewId: null`。`fetchFullResult()` 检查 `if (!state.reviewId) return null`，但没有任何机制从 URL 参数设置 `reviewId`。

```typescript
// review/[id]/page.tsx 第 21-24 行
useEffect(() => {
    if (reviewId) {           // reviewId 来自 URL params
        review.fetchFullResult(API_BASE);  // 但 hook 内部的 state.reviewId 始终是 null
    }
}, [reviewId]);
```

**影响**: 
- 从上传页跳转到详情页：正常（因为 `startReview` 设置了 `reviewId`）
- 直接访问/刷新详情页：**所有数据为空**，页面只显示"加载报告中..."
- 分享链接给同事：**完全无法使用**

**修复方法**: hook 需要接受外部 `reviewId` 参数，或在 `fetchFullResult` 中接受 `reviewId` 参数：

```typescript
// 方案 A: 修改 fetchFullResult 接受 reviewId 参数
const fetchFullResult = useCallback(async (apiBase: string, id?: string) => {
    const rid = id || state.reviewId;
    if (!rid) return null;
    // ... fetch with rid
}, [state.reviewId]);

// 方案 B: 在 hook 中增加 setReviewId 方法
const setReviewId = useCallback((id: string) => {
    setState(prev => ({ ...prev, reviewId: id }));
}, []);
```

**严重程度**: 🔴 致命 — 用户无法查看已完成的审查报告

---

### BUG-003: `.env.example` 缺少 `DEEPSEEK_API_KEY` 配置

**文件**: `backend/.env.example`  

**问题**: LPA pipeline 的所有 LLM 调用都使用 `os.getenv("DEEPSEEK_API_KEY")`，但 `.env.example` 中只有 `OPENAI_API_KEY`，没有 `DEEPSEEK_API_KEY`。

```python
# lpa.py 第 24 行
api_key = os.getenv("DEEPSEEK_API_KEY", "")
```

**影响**: 律所客户按照 `.env.example` 配置后，LPA 审查会以**离线模式**（规则引擎）运行，产出质量极低。客户可能不知道需要额外配置 `DEEPSEEK_API_KEY`。

**修复方法**: 在 `.env.example` 中添加：
```bash
# === LPA Review (DeepSeek) ===
DEEPSEEK_API_KEY=              # DeepSeek API key for LPA contract review
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

**严重程度**: 🔴 致命 — 部署后核心功能静默降级

---

## 二、高危 Bug（影响功能正确性或安全性）

### BUG-004: LPA 审查端点无认证保护

**文件**: `backend/app/api/routes/v1/lpa.py`  
**行号**: 33-124  

**问题**: 所有 LPA 端点（`/lpa/review`、`/lpa/review/{id}`、`/lpa/review/{id}/chat` 等）都没有使用 `Depends(get_current_user)` 或任何认证依赖。

```python
@router.post("/review")
async def start_review(
    file: UploadFile = File(...),
    service: LPAReviewService = Depends(_get_lpa_service),  # ← 无 auth
):
```

**影响**: 
- 任何人都可以上传合同触发昂贵的 LLM API 调用
- 任何人都可以查看其他人的审查结果（通过猜测 review_id）
- 无法追踪谁上传了什么合同

**修复方法**: 添加认证依赖：
```python
from app.api.deps import CurrentUser

@router.post("/review")
async def start_review(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(),  # ✅ 添加认证
    service: LPAReviewService = Depends(_get_lpa_service),
):
```

**严重程度**: 🟠 高危 — 律所客户的数据安全无法保障

---

### BUG-005: 审查会话纯内存存储，重启即丢失

**文件**: `backend/app/services/lpa_service.py`  
**行号**: 17  

**问题**: 审查会话存储在 Python 字典 `_sessions: Dict[str, Dict[str, Any]] = {}` 中。

```python
# lpa_service.py 第 17 行
_sessions: Dict[str, Dict[str, Any]] = {}
```

**影响**: 
- 服务器重启/容器重建后，所有进行中和已完成的审查全部丢失
- 包含用户上传的合同原文、审查报告等重要数据
- 律师可能花费数小时等待审查完成后，数据突然消失
- `asyncio.Event()` 存储在 dict 中无法序列化，无法直接迁移到 Redis

**修复方法**: 添加数据库持久化层：
```python
# 1. 创建 db/models/lpa_review.py
class LPAReview(Base):
    __tablename__ = "lpa_reviews"
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    status = Column(String)
    progress = Column(Float)
    file_content = Column(LargeBinary)  # 或存储到文件系统
    result_json = Column(Text)          # JSON 序列化的完整结果
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

**严重程度**: 🟠 高危 — 律所客户无法接受数据丢失

---

### BUG-006: 全局可变状态导致并发审查数据污染

**文件**: `backend/app/agents/lpa/llm_client.py`  
**行号**: 13-14  

**问题**: `TOOL_HANDLERS` 和 `TOOLS` 是模块级全局变量，多个并发审查会共享同一个工具注册表。

```python
# llm_client.py 第 13-14 行
TOOL_HANDLERS: Dict[str, Callable] = {}  # ← 全局共享
TOOLS: List[Dict[str, Any]] = []          # ← 全局共享
```

**影响**: 
- 当两个律师同时上传合同审查时，工具注册会被覆盖
- `register_tool()` 每次调用都 `TOOLS.append()`，导致工具列表无限增长
- 可能导致 LLM 调用错误的工具或重复调用

**修复方法**: 将工具注册改为实例级别：
```python
class LLMClient:
    def __init__(self, api_key: str, base_url: str):
        self._api_key = api_key
        self._base_url = base_url
        self._tools: List[Dict] = []          # ✅ 实例级别
        self._tool_handlers: Dict[str, Callable] = {}  # ✅ 实例级别
    
    def register_tool(self, name, description, schema, handler):
        self._tools.append({"name": name, "description": description, "input_schema": schema})
        self._tool_handlers[name] = handler
```

**严重程度**: 🟠 高危 — 并发使用时数据污染

---

### BUG-007: WebSocket 直接导入内存字典，紧耦合

**文件**: `backend/app/api/routes/v1/lpa_ws.py`  
**行号**: 12  

**问题**: WebSocket 端点直接从 `lpa_service` 导入内部 `_sessions` 字典。

```python
from app.services.lpa_service import _sessions  # ← 直接导入内部状态
```

**影响**: 
- 无法替换为 Redis 或数据库存储
- 无法进行水平扩展（多实例部署时 WebSocket 无法获取其他实例的 session）
- 微秒级竞态条件：WebSocket 轮询间隔 0.5s，但 pipeline 进度更新可能更快

**修复方法**: 通过 service 接口访问，不直接导入内部状态：
```python
# 使用 service 的 get_status() 方法
from app.services.lpa_service import LPAReviewService

@router.websocket("/lpa/review/{review_id}/ws")
async def lpa_review_websocket(websocket: WebSocket, review_id: str):
    service = LPAReviewService()
    # 使用 service.get_status() 而不是直接访问 _sessions
```

**严重程度**: 🟠 高危 — 架构问题，阻碍扩展

---

### BUG-008: `confirmChapters` 未检查 HTTP 响应状态

**文件**: `frontend/src/hooks/use-lpa-review.ts`  
**行号**: 155-161  

**问题**: PUT 请求没有验证 `res.ok` 就直接设置 `awaitingChapters: false`。

```typescript
const confirmChapters = useCallback(async (chapters: any[], apiBase: string) => {
    try {
        await fetch(`${apiBase}/lpa/review/${state.reviewId}/chapters`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ chapters }),
        });
        // ❌ 没有检查 res.ok！
        setState((prev) => ({ ...prev, awaitingChapters: false }));
    } catch (e: any) { ... }
```

**影响**: 服务器返回 500 错误时，前端会显示"已确认"，但后端实际没有收到确认。审查会卡在等待章节确认状态。

**修复方法**:
```typescript
const res = await fetch(...);
if (!res.ok) {
    throw new Error("章节确认失败");
}
setState((prev) => ({ ...prev, awaitingChapters: false }));
```

**严重程度**: 🟠 高危 — 用户体验严重受损

---

### BUG-009: CSP 中间件已定义但未注册

**文件**: `backend/app/main.py`  

**问题**: `SecurityHeadersMiddleware` 在 `middleware.py` 中完整定义，但 `main.py` 中只注册了 `RequestIDMiddleware`，没有注册安全头中间件。

```python
# main.py 第 112 行
app.add_middleware(RequestIDMiddleware)
# ← 缺少: app.add_middleware(SecurityHeadersMiddleware)
```

此外，CSP 的 `connect-src 'self'` 会阻止 WebSocket 连接（`ws://` 和 `wss://`），如果启用会导致 WebSocket 功能失效。

**影响**: 
- 没有 CSP、X-Frame-Options 等安全头
- 律所客户可能被 XSS、点击劫持等攻击
- 如果启用 CSP 但不修改 `connect-src`，WebSocket 会被阻止

**修复方法**:
```python
# main.py 中添加
from app.core.middleware import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware, csp_directives={
    **SecurityHeadersMiddleware.DEFAULT_CSP_DIRECTIVES,
    "connect-src": "'self' ws: wss:",  # ✅ 允许 WebSocket
})
```

**严重程度**: 🟠 高危 — 安全漏洞

---

## 三、中危 Bug（影响功能完整性或用户体验）

### BUG-010: PDF 表格提取在 fallback 路径下为空

**文件**: `backend/app/agents/lpa/document_preprocessor.py`  
**行号**: 118  

**问题**: 当 MinerU 不可用时（大多数部署场景），pypdf fallback 路径返回 `tables: []`。

```python
# 第 118 行
return self._build_output(full_text, [], fmt, "pypdf")  # ← tables 始终为空
```

**影响**: LPA 中的费率表、分配瀑布表、出资时间表等关键结构化数据会丢失。对于使用表格呈现费用结构的 LPA，审查质量显著下降。

**修复方法**: 集成 `camelot-py` 或 `tabula-py` 进行 PDF 表格提取：
```python
import camelot
tables = camelot.read_pdf(stream.getvalue(), pages="all")
extracted = [t.df.values.tolist() for t in tables]
return self._build_output(full_text, extracted, fmt, "pypdf")
```

**严重程度**: 🟡 中危 — 影响审查质量

---

### BUG-011: OCR 结果无置信度过滤

**文件**: `backend/app/agents/lpa/document_preprocessor.py`  
**行号**: 135-136  

**问题**: PaddleOCR 结果直接拼接，不检查置信度分数。

```python
result = self._ocr.ocr(image.data, cls=True)
text = " ".join([line[1][0] for line in result[0]]) if result and result[0] else ""
# ← line[1][1] 是置信度分数，从未使用
```

**影响**: 低置信度的 OCR 识别结果（如模糊扫描件）会产生乱码文本，污染后续分析。

**修复方法**:
```python
CONFIDENCE_THRESHOLD = 0.7
lines = []
for line in (result[0] or []):
    text_part, confidence = line[1]
    if confidence >= CONFIDENCE_THRESHOLD:
        lines.append(text_part)
text = " ".join(lines)
```

**严重程度**: 🟡 中危 — 扫描件审查质量下降

---

### BUG-012: 章节截断逻辑不一致

**文件**: `backend/app/agents/lpa/chapter_reviewer.py`  
**行号**: 116  

**问题**: 截断阈值逻辑错误。

```python
limit = 8000 if len(text) > 8000 else 6000
# 当 text 长度为 6001-8000 时，limit=6000，白白丢失 2000 字符
```

**影响**: 6001-8000 字符的章节会被不必要地截断，可能丢失关键条款。

**修复方法**:
```python
limit = min(len(text), 8000)  # ✅ 直接截断到 8000，不设中间值
```

**严重程度**: 🟡 中危 — 部分章节审查不完整

---

### BUG-013: LLM JSON 解析失败时静默丢弃 findings

**文件**: `backend/app/agents/lpa/chapter_reviewer.py`  
**行号**: 83-87, 102-106  

**问题**: 当 LLM 返回的 JSON 无法解析时，异常被 `except Exception` 捕获，返回空 findings。

```python
try:
    data = self._parse_json(resp)
    return self._validate_findings(data.get("findings", []), SIMPLE_RULE_IDS)
except Exception as e:
    logger.error("Simple review failed for '%s': %s", title, e)
    return []  # ← 静默返回空结果
```

**影响**: 用户看到某章节"未发现风险"，但实际上可能是 LLM 返回了格式错误的 JSON。律师可能会误信这个结果。

**修复方法**: 返回一个明确的错误标记：
```python
except Exception as e:
    logger.error("Simple review failed for '%s': %s", title, e)
    return [{
        "rule_id": "ERROR",
        "level": "审查失败",
        "finding": f"本章节审查过程中出现技术错误: {str(e)[:100]}",
        "evidence": "",
        "suggestion": "请人工审查本章节",
    }]
```

**严重程度**: 🟡 中危 — 可能误导律师

---

### BUG-014: WebSocket 无自动重连机制

**文件**: `frontend/src/hooks/use-lpa-review.ts`  
**行号**: 89-95  

**问题**: WebSocket 连接失败后只设置错误状态，不尝试重连。

```typescript
ws.onerror = () => {
    setState((prev) => ({
        ...prev,
        status: "error",
        error: "WebSocket 连接失败",  // ← 不重连
    }));
};
```

**影响**: 网络波动时审查进度丢失，用户需要刷新页面（但刷新后 `reviewId` 丢失，参考 BUG-002）。

**修复方法**: 添加指数退避重连：
```typescript
ws.onerror = () => {
    if (retryCount < 5) {
        setTimeout(() => connectWS(reviewId, apiBase), 1000 * 2 ** retryCount);
        retryCount++;
    } else {
        setState(prev => ({ ...prev, status: "error", error: "连接失败" }));
    }
};
```

**严重程度**: 🟡 中危 — 网络不稳定时体验差

---

### BUG-015: LPA Chat 使用同步 OpenAI 客户端在 async 方法中

**文件**: `backend/app/services/lpa_chat_service.py`  
**行号**: 43-44  

**问题**: 虽然 `chat()` 是 `async def`，但实际使用的是 `AsyncOpenAI`（已正确）。  
~~此问题已被验证为误报~~。`lpa_chat_service.py` 正确使用了 `AsyncOpenAI`。

**严重程度**: ✅ 已验证无此问题

---

### BUG-016: 没有任何 LPA 相关的测试用例

**文件**: `backend/tests/`  

**问题**: 整个测试目录中没有任何针对 LPA pipeline 的测试：
- 无 `test_lpa_service.py`
- 无 `test_lpa_routes.py`
- 无 `test_document_preprocessor.py`
- 无 `test_chapter_splitter.py`
- 无 `test_fact_extractor.py`
- 无 `test_chapter_reviewer.py`
- 无 `test_cross_checker.py`
- 无 `test_report.py`
- 无 `test_orchestrator.py`
- 无测试用 LPA 样本文件（`docs/Sample-Cornerstone-LPA-10.08.21.pdf` 存在但未被测试使用）

**影响**: 
- 无法验证上述 BUG 是否被修复
- 无法防止回归
- CI/CD 流水线不运行测试就部署

**修复方法**: 至少需要：
1. 集成测试：使用 Sample PDF 跑完整 pipeline
2. 单元测试：每个 stage 的输入输出测试
3. API 测试：每个 endpoint 的请求响应测试

**严重程度**: 🟡 中危 — 质量保障缺失

---

### BUG-017: 风险规则缺少 3 个关键类别

**文件**: `backend/app/agents/lpa/risk_rules.py`  

**问题**: 当前只有 3 个类别 18 条规则，缺少 LPA 审查中至关重要的类别：

| 缺失类别 | 重要性 | 说明 |
|----------|--------|------|
| **C. 分配/瀑布 (Distribution/Waterfall)** | 🔴 极高 | carried interest 分配、clawback、优先回报计算——**这是 LPA 中对 LP 财务影响最大的条款** |
| **E. 投资条款 (Investment Terms)** | 🟠 高 | 投资限制细化、共同投资权、跟投权、后续基金限制 |
| **F. 清算/解散/争议 (Liquidation/Dissolution/Dispute)** | 🟠 高 | 清算优先级、解散触发条件、争议解决机制细节 |

**影响**: 对律师客户来说，分配瀑布（waterfall）条款的审查是 LPA 审查中**最有价值**的部分，当前完全缺失。

**修复方法**: 在 `risk_rules.py` 中添加：
```python
# C. 分配/瀑布
"C1": {
    "id": "C1", "category": "分配/瀑布",
    "title": "分配瀑布结构",
    "level": "高风险",
    "check": "是 European waterfall 还是 American waterfall；是否有 clawback 条款",
    "suggestion": "建议采用 European waterfall，LP 优先回收全部出资+优先回报后再分配 carry"
},
"C2": {
    "id": "C2", "category": "分配/瀑布",
    "title": "优先回报率 (Preferred Return / Hurdle)",
    "level": "高风险",
    "check": "hurdle rate 是否 ≥ 8%（行业标准）；是单利还是复利",
    "suggestion": "建议 hurdle rate 不低于 8%，按复利计算"
},
# ... C3 (carry计算), C4 (clawback), C5 (GP co-investment)
```

**严重程度**: 🟡 中危（从功能完整性角度）/ 🔴 高危（从律师客户价值角度）

---

## 四、低危问题（代码质量/可维护性）

### ISSUE-018: 前端所有 LPA 相关字符串硬编码中文，无 i18n

**文件**: 多个前端文件  

**问题**: 虽然项目使用了 `[locale]` 路由和 i18n 框架，但所有 LPA 审查相关的字符串（30+ 处）都硬编码为中文，未使用 `useTranslations()`。

**影响**: 无法支持英文界面。对当前律所客户（中文环境）影响不大，但如果未来需要国际化则需大量重构。

**严重程度**: 🟢 低危

---

### ISSUE-019: 前端大量使用 `any` 类型

**文件**: `frontend/src/hooks/use-lpa-review.ts`  

**问题**: `chapters: any[]`, `facts: any`, `chapterReviews: any[]`, `crossCheck: any` — 没有 TypeScript 接口定义。

**影响**: 无类型安全，IDE 无法提供自动补全和错误检查。

**严重程度**: 🟢 低危

---

### ISSUE-020: Review 详情页变量名遮蔽

**文件**: `frontend/src/app/[locale]/(dashboard)/review/[id]/page.tsx`  
**行号**: 192  

```typescript
{review.chapterReviews.map((review: any, i: number) => (
//                         ^^^^^^ 遮蔽了外部的 review (hook)
```

**影响**: 回调内部无法访问外部的 hook 状态。当前代码恰好不需要，但容易引入 bug。

**严重程度**: 🟢 低危

---

### ISSUE-021: 后端 Dockerfile 以 root 用户运行

**文件**: `backend/Dockerfile`  

**影响**: 安全最佳实践要求容器以非 root 用户运行。

**严重程度**: 🟢 低危

---

### ISSUE-022: CI/CD 不运行测试就部署

**文件**: `.github/workflows/deploy.yml`  

**问题**: deploy workflow 中没有 `pytest` 或 `ruff` 步骤。

**影响**: 包含 BUG-001 这类致命 bug 的代码会直接部署到生产环境。

**严重程度**: 🟡 中危

---

### ISSUE-023: Alembic 无迁移版本文件

**文件**: `backend/alembic/`  

**问题**: 只有 `env.py`，没有 `versions/` 目录和迁移文件。使用 `Base.metadata.create_all()` 作为替代。

**影响**: 
- 无法进行数据库 schema 版本管理
- 无法回滚数据库变更
- 生产环境不适合使用 `create_all()`

**严重程度**: 🟡 中危

---

### BUG-024: 模型名称硬编码过时

**文件**: 多个文件

**问题**: 当前代码硬编码了旧模型名 `deepseek-chat` 和 `deepseek-reasoner`，需要更新为 `deepseek-v4-flash` 和 `deepseek-v4-pro`。

**涉及位置**:
- `chapter_reviewer.py` 第 42-43 行: `V3_MODEL = "deepseek-chat"`, `R1_MODEL = "deepseek-reasoner"`
- `cross_checker.py` 第 24 行: `R1_MODEL = "deepseek-reasoner"`
- `fact_extractor.py` 第 157 行: `model="deepseek-chat"`
- `lpa_chat_service.py` 第 68 行: `model="deepseek-chat"`
- `orchestrator.py` 第 137 行: `model="deepseek-chat"`

**影响**: 如果 DeepSeek 逐步淘汰旧模型，系统会突然不可用。

**修复方法**: 统一使用 `config.py` 中的 `AI_MODEL` 设置，或在 `settings` 中新增 `LPA_FAST_MODEL` 和 `LPA_REASONING_MODEL` 配置项。

**严重程度**: 🟠 高危（模型可用性风险）

---

### BUG-025: 截断逻辑在 1M 上下文下有害

**文件**: 多个文件

**问题**: 当前截断逻辑在 DeepSeek V4（1M 上下文）下完全多余，且会导致关键条款被丢弃。

**需移除的截断**:
- `chapter_reviewer.py` 第 116 行: `limit = 8000 if len(text) > 8000 else 6000` — 章节截断
- `fact_extractor.py` 第 117 行: `document_text[:8000]` — 事实提取截断
- `fact_extractor.py` 第 174 行: `source_text[:8000]` — LLM prompt 截断

**影响**: 
- 8000+ 字的章节尾部条款被丢弃（可能是关键的分配瀑布、费用结构条款）
- 6001-8000 字的章节被错误截断到 6000 字（BUG-012 的根因）
- 事实提取只看前 8000 字，可能遗漏后续章节中的关键信息

**修复方法**: 直接删除截断逻辑，使用全文。1M 上下文足以处理任何 LPA 文档。

**严重程度**: 🟡 中危（影响审查质量）

---

### BUG-026: Prompt 路径解析在 Docker 容器中失败

**文件**: `backend/app/agents/lpa/__init__.py`
**行号**: 12

**问题**: `prompts_dir()` 假设从 `__init__.py` 向上 4 层就是项目根目录，且 `prompts/` 存在于该目录。

```python
root = this.parent.parent.parent.parent  # lpa → agents → app → backend → root
prompts = root / "prompts"
```

**Docker 中的路径**：
```
__init__.py = /app/app/agents/lpa/__init__.py
向上 4 层   = /                      ← 不是项目根目录！
期望路径    = /prompts/               ← 不存在
```

**影响**: Docker 部署后所有 Prompt 文件读取失败，`path.read_text()` 会返回空字符串（因为有 `if path.exists()` 检查），导致 LLM 审查质量严重下降或完全无效。

**修复方法**: 将 prompts 打包为 Python 包内部资源：

1. 复制 prompts 到 `backend/app/agents/lpa/prompts/`
2. 修改 `prompts_dir()` 为：
```python
def prompts_dir() -> Path:
    return Path(__file__).parent / "prompts"
```
3. 在 Dockerfile 中保留复制步骤作为双重保险
4. 项目根目录的 `prompts/` 保留作为编辑源，构建时同步到包内

**严重程度**: 🔴 致命（Docker 部署后整个 LPA 审查失效）

---

### BUG-027: Alembic env.py 缺少 ConversationShare 模型导入

**文件**: `backend/alembic/env.py`

**问题**: Alembic 只导入了 User, Conversation, Message, ToolCall, MessageRating, ChatFile，但缺少 ConversationShare 模型。当创建迁移时，ConversationShare 表不会被包含在内。

**影响**: 未来如果需要通过 Alembic 管理数据库迁移，ConversationShare 相关的变更会被遗漏。

**修复方法**: 在 alembic env.py 中添加 `from app.db.models.conversation_share import ConversationShare`。

**严重程度**: 🟢 低危（当前使用 `create_all()` 不受影响）

---

### BUG-028: 无 HTTPS 加密传输（待开发）

**文件**: `docker-compose.yml`、`nginx.conf`

**问题**: nginx 只监听 HTTP 80 端口，没有 HTTPS 443。

```yaml
# docker-compose.yml
ports:
  - "80:80"    # ← 只有 HTTP，没有 443
```

**影响**:
- 合同文件上传时**明文传输**，中间人可截获合同全文
- JWT Token 明文传输，可被窃取冒充律师身份
- 审查报告明文返回，可能包含敏感合同条款
- 浏览器会标记为"不安全"，律师客户可能不信任

**修复方案**（待实施）:

| 方案 | 优点 | 缺点 | 是否需要域名 |
|------|------|------|------------|
| **Cloudflare Tunnel** | 免费，不需要备案 | 依赖第三方 | ❌ |
| **Let's Encrypt + nginx** | 自主可控 | 需要域名 + 备案 | ✅ |
| **阿里云 SLB + 证书** | 企业级 | 成本高 | ✅ |

**当前状态**: ⏳ 待开发，暂不处理

**严重程度**: 🔴 高危（律所客户数据安全风险）— 但暂不阻塞内网测试

---

## 五、部署策略确认

### 已确认: Docker Compose 部署

**部署环境**: 阿里云 ECS

**部署架构**:
```
阿里云 ECS
  ├── docker-compose.yml
  │   ├── backend（FastAPI + LPA pipeline）
  │   ├── frontend（Next.js）
  │   └── nginx（反向代理 + WebSocket + 50MB 上传）
  ├── volumes:
  │   ├── backend_data（SQLite 数据库）
  │   ├── backend_media（加密存储的合同文件）
  │   └── nginx.conf
  └── .env（DEEPSEEK_API_KEY, SECRET_KEY, API_KEY 等）
```

**升级流程**:
```bash
git pull
docker compose build
docker compose up -d
```

**关键修复项**: BUG-026（Prompt 路径）必须在 Dockerfile 中解决。

---

## 六、律所客户需求确认

### 6.1 已确认需求

| 需求 | 确认结果 | 实现工作量 |
|------|---------|-----------|
| **数据安全** | 合同文件加密存储（AES-256），传输走 HTTPS | 低（`cryptography` 库 20-30 行） |
| **多律师隔离** | 每人一个账号，只能看自己的审查结果 | 中（需新增 LPAReview 模型 + 端点认证） |
| **审查历史** | 律师需要查看过去所有审查的列表 | 中（新增 `/review/history` 页面 + 后端接口） |
| **并发控制** | 最多 5 个同时审查 | 低（`asyncio.Semaphore(5)`） |
| **数据出境** | 合同数据可发送到 DeepSeek API | 已确认允许 |

### 6.2 存储方案建议

当前系统使用内存字典存储，重启即丢失。建议：

```
阿里云 ECS（已有）
  ├── SQLite（已有，存用户数据）
  │   └── 新增 lpa_reviews 表（绑定 user_id，持久化审查结果）
  ├── 文件存储：./media/{user_id}/{review_id}/
  │   └── 加密存储合同原文（AES-256-GCM，密钥从 .env 读取）
  ├── DeepSeek API（已有）
  └── 后续可迁移：SQLite → PostgreSQL（当律师数 > 10 或需要高并发时）
```

---

## 七、缺失功能（对照研究计划）

| 研究计划中的功能 | 当前状态 | 优先级 |
|-----------------|---------|--------|
| **RAG 知识库** (ChromaDB/Qdrant + BGE-M3) | ❌ 完全缺失 | P0 |
| **法规合规检索** | ❌ 完全缺失 | P0 |
| **版本对比** | ❌ 完全缺失 | P1 |
| **报告 PDF/DOCX 导出** | ❌ 仅 Markdown | P1 |
| **审查历史列表页** | ❌ 无此页面 | P1 |
| **LLM 调用重试/限流** | ❌ 无重试逻辑 | P1 |
| **Side letter 分析** | ❌ 完全缺失 | P2 |
| **多文档审查** | ❌ 仅支持单文件 | P2 |
| **Rate Limiting** | ❌ 完全缺失 | P1 |
| **用户权限隔离** | ❌ LPA 端点无认证 | P1 |
| **HTTPS 加密传输** | ❌ 仅 HTTP 80 端口 | P1（待开发） |

---

## 八、模型与 Prompt 策略确认

### 7.1 模型选型

| 用途 | 原模型 | 新模型 | 上下文窗口 |
|------|--------|--------|-----------|
| 章节审查（简单） | `deepseek-chat` | `deepseek-v4-flash` | 1M tokens |
| 章节审查（复杂） | `deepseek-reasoner` | `deepseek-v4-pro` | 1M tokens |
| 事实提取 | `deepseek-chat` | `deepseek-v4-flash` | 1M tokens |
| 跨章交叉检查 | `deepseek-reasoner` | `deepseek-v4-pro` | 1M tokens |
| 追问对话 | `deepseek-chat` | `deepseek-v4-flash` | 1M tokens |

**涉及文件**:
- `backend/app/agents/lpa/chapter_reviewer.py` 第 42-43 行
- `backend/app/agents/lpa/cross_checker.py` 第 24 行
- `backend/app/agents/lpa/fact_extractor.py` 第 157 行
- `backend/app/agents/lpa/llm_client.py`（base_url 默认值）
- `backend/app/services/lpa_chat_service.py` 第 68 行
- `backend/app/agents/lpa/orchestrator.py` 第 137 行

### 7.2 截断策略

**结论**: 1M 上下文下截断完全不必要。

**需移除的截断逻辑**:
- `chapter_reviewer.py` 第 116 行 `limit = 8000 if len(text) > 8000 else 6000` → 直接使用全文
- `fact_extractor.py` 第 117 行 `document_text[:8000]` → 使用全文
- `fact_extractor.py` 第 174 行 `source_text[:8000]` → 使用全文
- `lpa_chat_service.py` 第 128 行 `[:8000]` → 可保留（对话上下文确实需要精简）

### 7.3 Prompt 策略

**原则**: 宁可多标记"可能有问题"的条款，让律师自行判断。

**需修改的 Prompt 文件**:
- `prompts/simple_review.md` — 添加"宁可多标记，减少遗漏"的指引
- `prompts/complex_review.md` — 同上，强调"LP 角度，保守审查"
- `prompts/cross_check.md` — 同上

**具体修改**: 在 Prompt 中添加：
```
审查原则：
- 宁可多标记也不要遗漏——律师可以忽略误报，但不能接受遗漏
- 对模糊用语（如"合理"、"适当"、"商业上合理"）标记为低风险
- 对 "sole discretion"、"may in its absolute discretion" 等宽泛授权用语标记为中风险以上
```

---

## 九、修复优先级建议（面向律所客户部署）

### 第一批（必须修复，否则无法交付）:
1. ✅ **BUG-001**: `user_prompt` → `user_message`（1 分钟修复）
2. ✅ **BUG-002**: 前端 `fetchFullResult` reviewId 传递（30 分钟修复）
3. ✅ **BUG-003**: `.env.example` 添加 `DEEPSEEK_API_KEY`（1 分钟修复）
4. ✅ **BUG-004**: LPA 端点添加认证（1 小时修复）
5. **BUG-024**: 更新模型名为 `deepseek-v4-flash` / `deepseek-v4-pro`（30 分钟）
6. **BUG-025**: 移除截断逻辑，使用全文（30 分钟）
7. **新增**: LPAReview 数据库模型 + 持久化（1-2 天）
8. **新增**: 文件加密存储 AES-256（半天）
9. **新增**: 审查历史列表页（前端 1 天 + 后端半天）
10. **BUG-026**: 修复 Prompt 路径（Docker 部署必须，30 分钟）

### 第二批（生产环境必须）:
11. **BUG-006**: 工具注册改为实例级别（2 小时）
12. **BUG-009**: 注册安全头中间件 + 修复 CSP（30 分钟）
13. **BUG-013**: JSON 解析失败返回错误标记（30 分钟）
14. **BUG-017**: 补充 C/E/F 类风险规则（1-2 天）
15. **新增**: 并发控制 `Semaphore(5)`（1 小时）
16. **新增**: 上传文件客户端大小校验（30 分钟）
17. **新增**: Prompt 策略调整为"宁可多标"（1 小时）

### 第三批（待开发 — 不阻塞内网测试）:
18. **BUG-028**: HTTPS 加密传输（Cloudflare Tunnel 或 Let's Encrypt，半天）

### 第四批（提升质量）:
19. **BUG-010**: PDF 表格提取（半天）
20. **BUG-014**: WebSocket 自动重连（2 小时）
21. **BUG-016**: 编写测试用例（2-3 天）
22. **ISSUE-022**: CI/CD 添加测试步骤（30 分钟）
23. **ISSUE-023**: 创建 Alembic 迁移（1 小时）

---

*本报告基于代码静态审查，未实际运行测试。建议在修复 BUG-001 后使用 `Sample-Cornerstone-LPA-10.08.21.pdf` 进行端到端集成测试。*
