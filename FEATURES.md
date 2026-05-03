# LPA Contract Review Agent — Developed Features

## Backend

### Auth & Security
- JWT-based authentication (access + refresh tokens)
- API Key authentication (header-based, service-to-service)
- bcrypt password hashing
- Role-based access control (USER / ADMIN)
- Request ID middleware for request correlation

### AI Agent — Conversational Chat
- PydanticAI-powered agent with streaming via WebSocket
- Multi-provider support: OpenAI-compatible (DeepSeek, Groq, etc.) + Anthropic (Claude)
- Default model: **deepseek-v4-pro** (via OpenAI-compatible API)
- Model factory abstraction — switch provider/model via `.env` config
- Tool system: `@agent.tool` decorator for registering custom tools (e.g., `current_datetime`)
- Built-in capabilities: `WebSearch`, `WebFetch`
- LPA-specialized system prompt (Chinese private-equity lawyer persona)
- Conversation persistence (SQLite): messages, tool calls, ratings
- File attachment support (images, documents) in chat
- Message rating (helpful/not helpful) with feedback comments

### LPA Contract Review Pipeline
- 6-stage pipeline: Preprocess → Chapter Split → Fact Extract → Chapter Review → Cross-Check → Report
- PDF, DOCX, TXT document parsing (pypdf, python-docx)
- 18 risk rules across 3 categories (GP/LP rights, economic terms, governance)
- Structured JSON output per stage
- Markdown report generation with risk severity classification
- REST endpoints: upload, poll status, get report, confirm chapters
- WebSocket for real-time pipeline progress
- Follow-up Q&A chat against completed review context

### API & Infrastructure
- FastAPI with OpenAPI docs (Swagger + ReDoc)
- Layered architecture: Routes → Services → Repositories
- Pydantic v2 schemas with validation
- SQLite (sync) with SQLAlchemy ORM
- Alembic migrations
- Auto-create tables on startup (dev convenience)
- CORS middleware
- Structured error handling (domain exceptions → HTTP status codes)

## Frontend (Next.js 15)

### Pages
- Landing page with feature showcase
- Dashboard with API status, active conversations, storage overview
- Profile page (update info, change password, delete account)
- Settings page
- Authentication pages (login, register, OAuth callback)
- Error pages (404, 403, 500, global error)

### Chat
- Real-time streaming chat via WebSocket
- Conversation sidebar (create, rename, archive, delete)
- Tool call visualization (approval dialog, result cards)
- Message actions: copy, rate (helpful/not helpful), share
- File upload in chat
- Dark/light theme toggle

### i18n
- Chinese (zh) translations across all components
- i18n routing with locale prefix (`/[locale]/...`)

### Layout
- Responsive sidebar navigation
- Auth guard component
- Breadcrumb navigation
- Header with user menu
