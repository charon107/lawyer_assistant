# LexMind

A FastAPI project

Generated with [Full-Stack AI Agent Template](https://github.com/vstorm-co/full-stack-ai-agent-template).

## Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI + Pydantic v2 |
| **Database** | SQLite |
| **Auth** | JWT + API Key + refresh tokens |
| **AI Framework** | pydantic_ai (openai) |
| **Frontend** | Next.js 15 + React 19 + Tailwind v4 |

## Quick Start

```bash
# Install dependencies
make install
# Start the server
make run
```

**Access:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Admin: http://localhost:8000/admin
- Frontend: http://localhost:3000 (run `cd frontend && bun dev`)

## Manual Setup

If you prefer to set up step by step:

```bash
# 1. Install dependencies
make install
# 3. Create and apply migrations
make db-migrate    # Enter: "Initial migration"
make db-upgrade

# 4. Create admin user
make create-admin

# 5. Start backend
make run
# 6. Start frontend (new terminal)
cd frontend && bun install && bun dev
```

## Commands

Run `make help` for all available commands. Key ones:

| Command | Description |
|---------|-------------|
| `make run` | Start dev server with hot reload |
| `make test` | Run tests |
| `make lint` | Check code quality |
| `make format` | Auto-format code |
| `make db-migrate` | Create new migration |
| `make db-upgrade` | Apply migrations |
| `make create-admin` | Create admin user |


## AI Agent

Using **pydantic_ai** with **openai** provider.
Chat with the agent at http://localhost:3000/chat

### Customize

- **System prompt:** `app/agents/prompts.py`
- **Add tools:** See `docs/howto/add-agent-tool.md`
- **Agent config:** `.env` → `AI_MODEL`, `AI_TEMPERATURE`

## Message Ratings

Users can rate AI responses with 👍/👎 and optional feedback comments.
Administrators can view analytics and export rating data.
- Rate messages at http://localhost:3000/chat
- Admin dashboard at http://localhost:3000/admin/ratings

See `docs/howto/use-ratings.md` for full documentation.

## Project Structure

```
backend/app/
├── api/routes/v1/        # API endpoints
├── core/config.py        # Settings (from .env)
├── services/             # Business logic
├── repositories/         # Data access
├── schemas/              # Pydantic models
├── db/models/            # Database models
├── agents/               # AI agents & tools
├── commands/             # CLI commands (auto-discovered)
└── ...
```

## Guides

| Guide | Description |
|-------|-------------|
| `docs/howto/add-api-endpoint.md` | Add a new API endpoint |
| `docs/howto/add-agent-tool.md` | Create a new agent tool |
| `docs/howto/customize-agent-prompt.md` | Customize agent behavior |
| `docs/howto/add-background-task.md` | Add background tasks |

## Environment Variables

All config is in `backend/.env`. Key variables:

```bash
OPENAI_API_KEY=sk-...
```

See `backend/.env.example` for all available variables.

## Deployment

### Frontend (Vercel)

```bash
cd frontend
npx vercel --prod
```

Set environment variables in Vercel dashboard:
- `BACKEND_URL` = your backend URL
- `BACKEND_WS_URL` = your backend WebSocket URL
- `NEXT_PUBLIC_AUTH_ENABLED` = `true`

### Backend (Docker)

```bash
make docker-prod
```

---

*Generated with [Full-Stack AI Agent Template](https://github.com/vstorm-co/full-stack-ai-agent-template) v0.2.7*
