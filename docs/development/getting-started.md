# Getting Started & Configuration Reference

## Initial Setup

```bash
cd backend

# Copy the example file (may already exist if generated with --generate-env)
cp .env.example .env

# Generate a secure secret key
openssl rand -hex 32
# Paste the output as SECRET_KEY in .env
```

## Configuration

All configuration is managed via environment variables, loaded from `backend/.env` using [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).

Settings are defined in `app/core/config.py` and accessed via the global `settings` object:

```python
from app.core.config import settings

print(settings.AI_MODEL)
print(settings.DEBUG)
```

### Project Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_NAME` | `lexmind` | Display name for the project |
| `API_V1_STR` | `/api/v1` | API version prefix |
| `DEBUG` | `false` | Enable debug mode (verbose errors, auto-reload) |
| `ENVIRONMENT` | `local` | One of: `development`, `local`, `staging`, `production` |
| `TIMEZONE` | `UTC` | IANA timezone (e.g. `UTC`, `Europe/Warsaw`, `America/New_York`) |
| `MODELS_CACHE_DIR` | `./models_cache` | Directory for cached ML models |
| `MEDIA_DIR` | `./media` | Directory for uploaded files |
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum file upload size in megabytes |

### Authentication

#### JWT

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (insecure default) | JWT signing key. **Must** be changed in production. Generate with: `openssl rand -hex 32` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | `10080` | Refresh token lifetime (7 days) |
| `ALGORITHM` | `HS256` | JWT signing algorithm |

Production validation: `SECRET_KEY` must be at least 32 characters and cannot use the default value in `ENVIRONMENT=production`.

#### API Key

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `change-me-in-production` | Shared API key for programmatic access |
| `API_KEY_HEADER` | `X-API-Key` | HTTP header name for API key |

Production validation: `API_KEY` cannot use the default value in `ENVIRONMENT=production`.

### Database (SQLite)

| Variable | Default | Description |
|----------|---------|-------------|
| `SQLITE_PATH` | `./data/lexmind.db` | Path to SQLite database file |

### AI Agent

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (empty) | OpenAI API key |
| `AI_MODEL` | `gpt-4.1-mini` | Default LLM model for chat |
| `AI_TEMPERATURE` | `0.7` | LLM temperature (0.0 = deterministic, 1.0 = creative) |
| `AI_AVAILABLE_MODELS` | (auto-configured) | JSON list of models shown in the UI model selector |
| `AI_FRAMEWORK` | `pydantic_ai` | AI framework (informational) |
| `LLM_PROVIDER` | `openai` | LLM provider (informational) |

#### Customizing Available Models

Override `AI_AVAILABLE_MODELS` in `.env` to customize the model selector:

```bash
AI_AVAILABLE_MODELS=["gpt-4.1-mini","gpt-4.1","claude-sonnet-4-6"]
```

### CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:8080"]` | Allowed origins (JSON array) |
| `CORS_ALLOW_CREDENTIALS` | `true` | Allow credentials (cookies) |
| `CORS_ALLOW_METHODS` | `["*"]` | Allowed HTTP methods |
| `CORS_ALLOW_HEADERS` | `["*"]` | Allowed HTTP headers |

Production validation: `CORS_ORIGINS` cannot contain `"*"` in `ENVIRONMENT=production`.

---

## Commands Reference

This project provides commands via two interfaces: **Make** targets for common workflows and a **project CLI** for fine-grained control.

### Make Commands

Run these from the project root directory.

#### Quick Start

| Command | Description |
|---------|-------------|
| `make install` | Install backend dependencies with uv + pre-commit hooks |

#### Development

| Command | Description |
|---------|-------------|
| `make run` | Start development server with hot reload |
| `make run-prod` | Start production server (0.0.0.0:8000) |
| `make routes` | Show all registered API routes |
| `make test` | Run tests with verbose output |
| `make test-cov` | Run tests with coverage report (HTML + terminal) |
| `make format` | Auto-format code with ruff |
| `make lint` | Lint and type-check code (ruff + ty) |
| `make clean` | Remove cache files (__pycache__, .pytest_cache, etc.) |

#### Database

| Command | Description |
|---------|-------------|
| `make db-init` | Create initial migration + apply |
| `make db-migrate` | Create new migration (prompts for message) |
| `make db-upgrade` | Apply pending migrations |
| `make db-downgrade` | Rollback last migration |
| `make db-current` | Show current migration revision |
| `make db-history` | Show full migration history |

#### Users

| Command | Description |
|---------|-------------|
| `make create-admin` | Create admin user (interactive) |
| `make user-create` | Create new user (interactive) |
| `make user-list` | List all users |

---

### Project CLI

All project CLI commands are invoked via:

```bash
cd backend
uv run lexmind <group> <command> [options]
```

#### Server Commands

```bash
uv run lexmind server run              # Start dev server
uv run lexmind server run --reload     # With hot reload
uv run lexmind server run --port 9000  # Custom port
uv run lexmind server routes           # Show all registered routes
```

#### Database Commands

```bash
uv run lexmind db init                  # Run all migrations
uv run lexmind db migrate -m "message"  # Create new migration
uv run lexmind db upgrade               # Apply pending migrations
uv run lexmind db upgrade --revision e3f  # Upgrade to specific revision
uv run lexmind db downgrade             # Rollback last migration
uv run lexmind db downgrade --revision base  # Rollback to start
uv run lexmind db current               # Show current revision
uv run lexmind db history               # Show migration history
```

#### User Commands

```bash
# Create user (interactive prompts for email/password)
uv run lexmind user create

# Create user non-interactively
uv run lexmind user create --email user@example.com --password secret

# Create user with specific role
uv run lexmind user create --email admin@example.com --password secret --role admin

# Create user with superuser flag
uv run lexmind user create --email admin@example.com --password secret --superuser

# Create admin (shortcut)
uv run lexmind user create-admin --email admin@example.com --password secret

# Change user role
uv run lexmind user set-role user@example.com --role admin

# List all users
uv run lexmind user list
```

#### Custom Commands

Custom commands are auto-discovered from `app/commands/`. Run them via:

```bash
uv run lexmind cmd <command-name> [options]
```

### Adding Custom Commands

Commands are auto-discovered from `app/commands/`. Create a new file:

```python
# app/commands/my_command.py
import click
from app.commands import command, success, error

@command("my-command", help="Description of what this does")
@click.option("--name", "-n", required=True, help="Name parameter")
def my_command(name: str):
    """Your command logic here."""
    success(f"Done: {name}")
```

Run it:

```bash
uv run lexmind cmd my-command --name test
```

---

## Production Checklist

Before deploying to production, ensure these variables are properly set:

1. `SECRET_KEY` — Generate a unique 64-character hex key: `openssl rand -hex 32`
2. `API_KEY` — Generate a unique key: `openssl rand -hex 32`
3. `ENVIRONMENT` — Set to `production`
4. `DEBUG` — Set to `false`
5. `CORS_ORIGINS` — List only your actual frontend domain(s)
6. `OPENAI_API_KEY` — Your production API key
