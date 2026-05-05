# Model Configuration Redesign

**Date**: 2026-05-05
**Status**: Draft
**Scope**: Profile page model configuration overhaul

---

## Problem

Current model config UX requires users to manually type model names, has only two hardcoded providers (OpenAI/Anthropic), and lacks connection validation. Users don't know if their API key works until they try to use the chat.

## Design

### Provider Metadata (Frontend)

Define a `PROVIDERS` constant in `frontend/src/lib/providers.ts`:

```typescript
interface ProviderMeta {
  id: string;              // "deepseek" | "openai" | "anthropic" | "moonshot" | "zhipu" | "qwen"
  name: string;            // Display name
  defaultBaseUrl: string;  // Pre-filled on select
  apiKeyPlaceholder: string;
  type: "openai_compatible" | "anthropic";
  models?: string[];       // Hardcoded fallback (Anthropic only)
}

const PROVIDERS: ProviderMeta[] = [
  { id: "deepseek", name: "DeepSeek", defaultBaseUrl: "https://api.deepseek.com", apiKeyPlaceholder: "sk-...", type: "openai_compatible" },
  { id: "openai", name: "OpenAI", defaultBaseUrl: "https://api.openai.com/v1", apiKeyPlaceholder: "sk-...", type: "openai_compatible" },
  { id: "anthropic", name: "Anthropic", defaultBaseUrl: "https://api.anthropic.com", apiKeyPlaceholder: "sk-ant-...", type: "anthropic", models: ["claude-sonnet-4-6", "claude-haiku-4-5", "claude-opus-4-7"] },
  { id: "moonshot", name: "Moonshot AI", defaultBaseUrl: "https://api.moonshot.cn/v1", apiKeyPlaceholder: "sk-...", type: "openai_compatible" },
  { id: "zhipu", name: "Zhipu AI", defaultBaseUrl: "https://open.bigmodel.cn/api/paas/v4", apiKeyPlaceholder: "...", type: "openai_compatible" },
  { id: "qwen", name: "Qwen (Alibaba)", defaultBaseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1", apiKeyPlaceholder: "sk-...", type: "openai_compatible" },
];
```

### Database Schema Change

**User model** (`backend/app/db/models/user.py`):

Remove:
- `openai_api_key`
- `anthropic_api_key`
- `ai_model`

Add:
- `llm_api_key` (String(500), nullable) — single encrypted field
- `llm_model` (String(100), nullable) — selected model name

Keep:
- `llm_provider` (String(50), nullable) — provider id
- `llm_base_url` (String(500), nullable) — customizable base URL

**Alembic migration**: Drop 3 columns, add 2 columns.

### API Schema Changes

**UserUpdate** (`backend/app/schemas/user.py`):

```python
class UserUpdate(BaseSchema):
    email: EmailStr | None = None
    password: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
    role: UserRole | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str | None = None
```

**UserRead**:

```python
class UserRead(UserBase, TimestampSchema):
    id: str
    role: UserRole = UserRole.USER
    avatar_url: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_base_url: str | None = None
    has_llm_key: bool = False  # Replaces has_openai_key / has_anthropic_key

    @model_validator(mode="before")
    @classmethod
    def compute_api_key_flags(cls, data):
        if hasattr(data, "llm_api_key"):
            data.has_llm_key = bool(data.llm_api_key)
        return data
```

### New Endpoint: Test Connection

**POST /api/v1/users/me/test-connection**

```python
@router.post("/me/test-connection")
def test_llm_connection(
    current_user: CurrentUser,
) -> dict:
    """Test the user's LLM connection. Returns {success: bool, message: str}."""
```

Logic:
1. Read `llm_provider`, `llm_api_key`, `llm_base_url`, `llm_model` from current_user
2. If any missing, return `{success: false, message: "配置不完整"}`
3. Based on provider type:
   - `openai_compatible`: GET `{base_url}/models` with `Authorization: Bearer {api_key}`
   - `anthropic`: POST `{base_url}/v1/messages` with `x-api-key: {api_key}`, body: `{"model": "...", "max_tokens": 1, "messages": [{"role": "user", "content": "hi"}]}`
4. Return `{success: true/false, message: "连接成功" / error details}`

### Frontend Changes

**Profile page** (`frontend/src/app/[locale]/(dashboard)/profile/page.tsx`):

Replace the current model config section with:

1. **Provider dropdown** — shows all providers from `PROVIDERS`
2. **Model dropdown** — populated after provider selection:
   - OpenAI-compatible: call `GET {base_url}/models` after saving API key
   - Anthropic: use hardcoded list
3. **API Key input** — password field with show/hide toggle
4. **Base URL input** — auto-filled from provider default, editable
5. **Save button** — saves config, then auto-triggers connection test
6. **Connection status badge** — shows "连接成功" (green) / "连接失败" (red) / "未测试" (gray)

**Flow (two-phase save)**:
```
Phase 1: User selects provider → base URL auto-fills → user enters API key →
  user clicks save → PATCH /api/v1/users/me (provider + key + base_url, no model yet)

Phase 2: If provider is openai_compatible →
  GET {base_url}/models (backend proxy, using saved key) → populate model dropdown →
  user selects model → PATCH /api/v1/users/me (model only) →
  POST /api/v1/users/me/test-connection → show result badge

If provider is Anthropic →
  show hardcoded model dropdown immediately (no API call needed) →
  user selects model → PATCH /api/v1/users/me (model) →
  POST /api/v1/users/me/test-connection → show result badge
```

**New endpoint: List Models**
POST /api/v1/users/me/list-models — uses saved API key + base URL to fetch available models from provider. Returns `{models: string[]}`.

### Files to Change

| File | Change |
|------|--------|
| `backend/app/db/models/user.py` | Remove 3 fields, add 2 fields |
| `backend/app/schemas/user.py` | Update UserUpdate, UserRead |
| `backend/app/services/user.py` | Update field handling in update() |
| `backend/app/api/routes/v1/users.py` | Add test-connection + list-models endpoints |
| `backend/alembic/versions/xxx_llm_config.py` | Migration |
| `frontend/src/lib/providers.ts` | New: provider metadata |
| `frontend/src/app/[locale]/(dashboard)/profile/page.tsx` | Redesign model config UI |
| `frontend/src/types/auth.ts` | Update User type |
| `frontend/src/app/api/users/me/test-connection/route.ts` | New: proxy to backend |
| `frontend/src/app/api/users/me/list-models/route.ts` | New: proxy to backend |

### Out of Scope

- Per-conversation model override (future)
- Token usage tracking
- Multiple API key profiles
- Provider-specific model parameter tuning (temperature, etc.)
