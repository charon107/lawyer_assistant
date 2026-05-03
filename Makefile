.PHONY: install format lint test run clean help db-init

# === Quick Start (one command to rule them all) ===

# === Setup ===
install:
	uv sync --directory backend --dev
	@if git rev-parse --git-dir > /dev/null 2>&1; then \
		uv run --directory backend pre-commit install; \
	else \
		echo "⚠️  Not a git repository - skipping pre-commit install"; \
		echo "   Run 'git init && make install' to set up pre-commit hooks"; \
	fi
	@echo ""
	@echo "✅ Installation complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  • cd backend && cp .env.example .env"
	@echo "  • Edit backend/.env with your settings"
	@echo "  • make run              # Start development server"

# === Code Quality ===
format:
	uv run --directory backend ruff format app tests cli
	uv run --directory backend ruff check app tests cli --fix

lint:
	uv run --directory backend ruff check app tests cli
	uv run --directory backend ruff format app tests cli --check
	uv run --directory backend ty check

# === Testing ===
test:
	uv run --directory backend pytest tests/ -v

test-cov:
	uv run --directory backend pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# === Database ===
db-init:
	cd backend && uv run lpa_review_app db migrate -m "initial" || true
	cd backend && uv run lpa_review_app db upgrade
	@echo ""
	@echo "✅ Database initialized!"

db-migrate:
	@read -p "Migration message: " msg; \
	uv run --directory backend lpa_review_app db migrate -m "$$msg"

db-upgrade:
	uv run --directory backend lpa_review_app db upgrade

db-downgrade:
	uv run --directory backend lpa_review_app db downgrade

db-current:
	uv run --directory backend lpa_review_app db current

db-history:
	uv run --directory backend lpa_review_app db history

# === Server ===
run:
	uv run --directory backend lpa_review_app server run --reload

run-prod:
	uv run --directory backend lpa_review_app server run --host 0.0.0.0 --port 8000

routes:
	uv run --directory backend lpa_review_app server routes

# === Users ===
create-admin:
	@echo "Creating admin user..."
	uv run --directory backend lpa_review_app user create-admin

user-create:
	uv run --directory backend lpa_review_app user create

user-list:
	uv run --directory backend lpa_review_app user list

# === Cleanup ===
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ty_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml

# === Help ===
help:
	@echo ""
	@echo "lpa_review_app - Available Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies + pre-commit hooks"
	@echo ""
	@echo "Development:"
	@echo "  make run           Start dev server (with hot reload)"
	@echo "  make test          Run tests"
	@echo "  make lint          Check code quality"
	@echo "  make format        Auto-format code"
	@echo ""
	@echo "Database:"
	@echo "  make db-init       Initialize database (start + migrate)"
	@echo "  make db-migrate    Create new migration"
	@echo "  make db-upgrade    Apply migrations"
	@echo "  make db-downgrade  Rollback last migration"
	@echo "  make db-current    Show current migration"
	@echo ""
	@echo "Users:"
	@echo "  make create-admin  Create admin user (for SQLAdmin access)"
	@echo "  make user-create   Create new user (interactive)"
	@echo "  make user-list     List all users"
	@echo ""
	@echo "Other:"
	@echo "  make routes        Show all API routes"
	@echo "  make clean         Clean cache files"
	@echo ""
