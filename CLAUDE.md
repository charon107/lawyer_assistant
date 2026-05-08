## Project Overview

**lpa_review_app** — FastAPI application generated with Full-Stack AI Agent Template.

Stack:

- FastAPI
- Pydantic v2
- SQLite
- SQLAlchemy
- JWT + API Key Auth
- PydanticAI
- Next.js 15
- Bun
- uv

This repository uses TWO AI engineering systems together:

1. GStack
   - role-based engineering workflow
   - planning / review / QA / deploy / security

2. Superpowers
   - development discipline
   - TDD
   - structured planning
   - systematic execution
   - review rigor

GStack decides:
- WHICH workflow to invoke

Superpowers decides:
- HOW implementation work must be done

---

# =========================================================
# Core Engineering Workflow
# =========================================================

NEVER jump directly into coding for meaningful work.

Always follow:

```text
Clarify
→ Plan
→ Test First
→ Implement
→ Review
→ QA
→ Ship
→ Document
````

Default feature workflow:

```text
/office-hours
/plan-eng-review
/plan-design-review      # if UI involved

TDD implementation

/review
/qa
/ship
/document-release
```

---

# =========================================================

# Commands

# =========================================================

## Backend

```bash
cd backend

uv run uvicorn app.main:app --reload --port 8000

uv run pytest

uv run pytest tests/test_file.py::test_name -v

uv run ruff check . --fix

uv run ruff format .

uv run ty check
```

## Database

```bash
uv run alembic upgrade head

uv run alembic revision --autogenerate -m "Description"
```

## Frontend

```bash
cd frontend

bun dev

bun test

bun run lint
```

---

# =========================================================

# Required Verification

# =========================================================

Before saying work is complete:

## Backend minimum verification

```bash
cd backend

uv run ruff check . --fix

uv run ruff format .

uv run ty check

uv run pytest
```

## Frontend minimum verification

```bash
cd frontend

bun run lint

bun test
```

Do NOT skip tests unless:

* impossible
* explicitly instructed
* environment limitation exists

If skipped:

* explain WHY
* explain RISK

---

# =========================================================

# Project Structure

# =========================================================

```text
backend/app/
├── main.py
├── api/
│   ├── deps.py
│   ├── exception_handlers.py
│   └── routes/v1/
├── core/
│   ├── config.py
│   ├── security.py
│   ├── exceptions.py
│   └── middleware.py
├── db/
│   ├── base.py
│   ├── session.py
│   └── models/
├── schemas/
├── repositories/
├── services/
├── agents/
├── worker/
└── commands/
```

---

# =========================================================

# Architecture Rules

# =========================================================

Architecture:

```text
Routes
→ Services
→ Repositories
```

STRICTLY preserve this architecture.

---

## Routes

Location:

```text
api/routes/v1/
```

Rules:

* HTTP layer only
* validate input
* call services
* return response schemas
* NEVER import repositories
* NEVER contain business logic

Use:

```python
-> Any
```

Example:

```python
@router.get("/{id}", response_model=ConversationRead)
async def get_conversation(
    id: UUID,
    service: ConversationSvc,
    user: CurrentUser,
) -> Any:
    return await service.get(id, user_id=user.id)
```

---

## Services

Rules:

* business logic only
* class-based
* constructor:

```python
__init__(self, db)
```

* orchestrate repositories
* raise domain exceptions
* NEVER raise HTTPException
* NEVER commit DB session

---

## Repositories

Rules:

* pure data access only
* keyword-only args
* NEVER commit
* use:

```python
db.flush()
db.refresh()
```

Example:

```python
async def create_user(
    db: AsyncSession,
    *,
    email: str,
    name: str,
) -> User:
    user = User(email=email, name=name)

    db.add(user)

    await db.flush()

    await db.refresh(user)

    return user
```

---

# =========================================================

# Dependency Injection

# =========================================================

Use Annotated aliases from:

```text
api/deps.py
```

Example:

```python
DBSession = Annotated[AsyncSession, Depends(get_db_session)]

UserSvc = Annotated[UserService, Depends(get_user_service)]

CurrentUser = Annotated[User, Depends(get_current_user)]
```

Rules:

* prefer aliases
* avoid raw Depends() in routes
* keep route signatures clean

---

# =========================================================

# Schema Rules

# =========================================================

Use Pydantic v2.

Patterns:

```text
*Create
*Update
*Read
*List
```

Rules:

* separate schemas per operation
* update schemas use optional fields
* use Field()
* use validators
* use ConfigDict(from_attributes=True)

List schema:

```python
class ItemList(BaseSchema):
    items: list[ItemRead]
    total: int
```

---

# =========================================================

# Exception Rules

# =========================================================

All domain exceptions extend:

```python
AppException
```

Use domain exceptions ONLY.

Never raise:

* HTTPException
* raw ValueError
* generic Exception

Example:

```python
raise NotFoundError(
    message="User not found",
    details={"user_id": id},
)
```

---

# =========================================================

# Response Rules

# =========================================================

## Single item

```python
@router.get("/{id}", response_model=ConversationRead)
```

## List

```python
@router.get("", response_model=ConversationList)
```

## Create

```python
@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
```

## Delete

```python
@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
```

---

# =========================================================

# General Coding Rules

# =========================================================

Rules:

* imports:

  * stdlib
  * third-party
  * local

* use TYPE_CHECKING for circular refs

* use:

```python
datetime.now(UTC)
```

never:

```python
datetime.utcnow()
```

* use compare_digest for secrets
* explicit names over clever abstractions
* keep functions small
* avoid broad rewrites
* avoid touching unrelated files
* avoid unnecessary dependencies
* avoid giant commits
* keep migrations small
* preserve backward compatibility when possible

---

# =========================================================

# TDD Rules

# =========================================================

MANDATORY for:

* features
* bugs
* services
* repositories
* business logic
* parsers
* indexing
* search
* workflows

Use:

```text
RED
→ GREEN
→ REFACTOR
```

Workflow:

1. write failing test
2. confirm test fails
3. implement minimum code
4. confirm test passes
5. refactor safely
6. rerun tests

Never implement large logic first.

If code already exists:

* write characterization tests before refactor

---

# =========================================================

# GStack

# =========================================================

Use GStack for:

* planning
* architecture
* design
* QA
* review
* security
* shipping
* deployment

Use `/browse` for ALL browser interactions.

NEVER use:

```text
mcp__claude-in-chrome__*
```

---

## Available Skills

```text
/office-hours
/plan-ceo-review
/plan-eng-review
/plan-design-review
/plan-devex-review

/autoplan

/design-consultation
/design-shotgun
/design-html
/design-review

/devex-review

/review
/investigate

/qa
/qa-only

/cso

/ship
/land-and-deploy
/canary

/benchmark

/document-release

/retro

/browse
/open-gstack-browser
/connect-chrome
/setup-browser-cookies

/pair-agent

/codex

/careful
/freeze
/guard
/unfreeze

/setup-deploy
/setup-gbrain
/sync-gbrain

/gstack-upgrade

/learn
```

---

# =========================================================

# GStack Skill Routing

# =========================================================

## Product ideas

Use:

```text
/office-hours
```

---

## Architecture

Use:

```text
/plan-eng-review
```

---

## Business scope / MVP

Use:

```text
/plan-ceo-review
```

---

## UI / UX

Use:

```text
/plan-design-review
/design-consultation
/design-shotgun
/design-review
```

---

## Developer Experience

Use:

```text
/plan-devex-review
/devex-review
```

---

## Full Planning Pipeline

Use:

```text
/autoplan
```

---

## Bugs

Use:

```text
/investigate
```

before coding.

---

## Code Review

Use:

```text
/review
```

after meaningful changes.

---

## Browser QA

Use:

```text
/qa
```

---

## Security Review

Use:

```text
/cso
```

for:

* auth
* permissions
* file access
* secrets
* external integrations
* AI tools

---

## Deployment

Use:

```text
/ship
```

Then:

```text
/land-and-deploy
```

---

## Production Monitoring

Use:

```text
/canary
```

---

# =========================================================

# Superpowers

# =========================================================

Use Superpowers for:

* disciplined thinking
* planning
* TDD
* execution rigor
* systematic reviews

Core Superpowers:

```text
brainstorming
writing-plans
executing-plans
test-driven-development
requesting-code-review
finishing-a-development-branch
```

---

# =========================================================

# Superpowers Principles

# =========================================================

Always prefer:

```text
Evidence over guesses

Tests over assumptions

Small iterations over giant rewrites

Systematic debugging over random edits

Review before merge

Simplicity over cleverness
```

---

# =========================================================

# Feature Workflow

# =========================================================

For NEW FEATURES:

```text
/office-hours

/plan-ceo-review

/plan-eng-review

/plan-design-review     # if UI exists
```

Then:

```text
writing-plans
```

Then:

```text
test-driven-development
```

Then implement.

Then:

```text
/review
```

Then:

```text
/qa
```

Then:

```text
/ship
```

Then:

```text
/document-release
```

---

# =========================================================

# Bug Fix Workflow

# =========================================================

ALWAYS start with:

```text
/investigate
```

Then:

1. reproduce bug
2. write failing regression test
3. confirm failure
4. fix bug
5. confirm pass
6. rerun nearby tests
7. /review

Never fix blindly.

---

# =========================================================

# Refactor Workflow

# =========================================================

Before refactor:

```text
/review
```

Then:

```text
/investigate
```

Then:

* characterization tests
* small safe batches

Rules:

* preserve behavior
* no mixed feature/refactor PRs
* avoid giant rewrites

---

# =========================================================

# Full Repository Cleanup Workflow

# =========================================================

For:

* dead code
* stale experiments
* unused dependencies
* duplicate modules
* obsolete scripts
* historical leftovers

First:

```text
/review full-repo cleanup audit
```

Then:

```text
/investigate cleanup candidates
```

Then:

* remove only SAFE items
* small batches only
* rerun tests after each batch

Then:

```text
/review
```

Then:

```text
/qa
```

Never delete code without evidence.

Require:

* import tracing
* runtime entrypoint checks
* config reference checks
* dynamic loading checks
* test checks

---

# =========================================================

# Security Rules

# =========================================================

For sensitive changes:

```text
/guard
/cso
```

Never:

* log secrets
* expose tokens
* weaken auth
* bypass validation
* bypass permission checks

Always:

* validate inputs
* sanitize external data
* use least privilege

---

# =========================================================

# AI Agent Rules

# =========================================================

For:

```text
backend/app/agents/
```

Rules:

* model output is untrusted
* validate tool input
* validate tool output
* never execute arbitrary generated code
* never expose secrets to prompts
* add tests for failures
* add timeout handling
* add retry handling
* prefer structured outputs

---

# =========================================================

# QA Rules

# =========================================================

Use:

```text
/qa
```

for:

* UI flows
* forms
* authentication
* uploads
* search
* navigation
* browser behavior

Use:

* real browser testing
* interaction testing
* regression testing

Not just unit tests.

---

# =========================================================

# Documentation Rules

# =========================================================

Run:

```text
/document-release
```

when changing:

* APIs
* env vars
* setup
* commands
* schema
* auth
* workflows
* deployment
* agents

Keep synchronized:

* README
* docs
* examples
* .env.example

---

# =========================================================

# Database Rules

# =========================================================

Rules:

* repositories NEVER commit
* session lifecycle controls transaction
* schema changes require migrations
* avoid destructive migrations
* review migrations carefully
* preserve SQLite compatibility

---

# =========================================================

# Review Standards

# =========================================================

Reviews MUST check:

* correctness
* architecture
* boundaries
* tests
* error handling
* security
* performance
* migrations
* backward compatibility
* dead code
* duplicate logic
* documentation drift

Critical findings block shipping.

---

# =========================================================

# When To Ask User

# =========================================================

DO NOT ask before:

* reading files
* searching code
* running tests
* linting
* planning
* adding tests
* safe reviews

ASK before:

* deleting major code
* destructive migrations
* changing auth behavior
* adding paid services
* major dependency changes
* deployment
* public API breaking changes

---

# =========================================================

# Completion Criteria

# =========================================================

Never say DONE unless:

* implementation matches approved plan
* tests added/updated
* tests pass
* lint passes
* types pass
* /review completed
* /qa completed if applicable
* docs updated if needed

Final response format:

```text
Summary

Tests run

Files changed

Risks / follow-ups
```

```
```
