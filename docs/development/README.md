# Development

This section covers setup, configuration, testing, and implementation guides for developing LexMind.

## Contents

- **[Getting Started & Configuration](./getting-started.md)** — Environment setup and configuration reference
  - Initial setup steps
  - Environment variables reference
  - Project settings
  - Authentication configuration
  - Database setup
  - AI agent configuration
  - CORS settings
  - Production checklist
  - Make commands reference
  - Project CLI reference
  - Custom commands

- **[Testing Guide](./testing.md)** — Writing and running tests
  - Running tests
  - Test structure and naming
  - Fixtures
  - Async tests
  - API endpoint tests
  - Service tests
  - Authentication testing

- **[Adding Features](./adding-features.md)** — Step-by-step feature implementation workflow
  - Planning and requirements
  - TDD approach
  - Code organization
  - Documentation

- **[How-To Guides](./guides/)** — Practical guides for common development tasks
  - [Add Agent Tools](./guides/agent-tools.md) — Create new AI agent capabilities
  - [Add API Endpoints](./guides/api-endpoints.md) — Follow repository + service pattern
  - [Customize Agent Prompts](./guides/customize-prompts.md) — Modify agent behavior
  - [Use Ratings System](./guides/ratings-system.md) — User feedback mechanisms

---

## Getting Started Quickly

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Configure environment:**
   ```bash
   cp backend/.env.example backend/.env
   # Edit .env with your settings
   ```

3. **Start development server:**
   ```bash
   make run
   ```

4. **Run tests:**
   ```bash
   make test
   ```

---

**First time?** Start with [Getting Started & Configuration](./getting-started.md)

**Adding a feature?** Follow [Adding Features](./adding-features.md)

**Need a how-to?** Check [How-To Guides](./guides/)
