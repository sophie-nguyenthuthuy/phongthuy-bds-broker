.PHONY: help dev-up dev-down api-dev web-dev install lint format type-check test test-api test-ontology db-migrate db-revision db-reset seed clean

UV ?= uv
PNPM ?= pnpm

help:  ## Show this help.
	@awk 'BEGIN{FS=":.*##"; printf "Targets:\n"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ─── Infra ────────────────────────────────────────────────────────
dev-up:  ## Start Postgres + Redis (Docker)
	docker compose up -d postgres redis

dev-down:  ## Stop dev infra
	docker compose down

# ─── Install ──────────────────────────────────────────────────────
install:  ## Install all deps (api + web + ontology)
	$(UV) sync --all-packages
	cd apps/web && $(PNPM) install

# ─── Run ──────────────────────────────────────────────────────────
api-dev:  ## Run API in dev mode
	cd apps/api && $(UV) run uvicorn phongthuy_bds.main:app --reload --host 0.0.0.0 --port 8000

web-dev:  ## Run web in dev mode
	cd apps/web && $(PNPM) dev

# ─── DB ───────────────────────────────────────────────────────────
db-migrate:  ## Apply migrations
	cd apps/api && $(UV) run alembic upgrade head

db-revision:  ## Create new migration: make db-revision m="add x"
	cd apps/api && $(UV) run alembic revision --autogenerate -m "$(m)"

db-reset:  ## DESTRUCTIVE — drop schema, re-migrate, seed
	cd apps/api && $(UV) run alembic downgrade base && $(UV) run alembic upgrade head
	$(MAKE) seed

seed:  ## Seed demo tenant + broker + sample customer
	cd apps/api && $(UV) run python -m phongthuy_bds.scripts.seed_demo

# ─── Quality ──────────────────────────────────────────────────────
lint:  ## Run ruff + eslint
	$(UV) run ruff check apps/api packages/ontology
	cd apps/web && $(PNPM) lint

format:  ## Apply ruff format + prettier
	$(UV) run ruff format apps/api packages/ontology
	cd apps/web && $(PNPM) format

type-check:  ## Run mypy + tsc
	$(UV) run mypy apps/api packages/ontology
	cd apps/web && $(PNPM) type-check

# ─── Test ─────────────────────────────────────────────────────────
test: test-ontology test-api  ## Run all tests

test-api:  ## Run API tests
	cd apps/api && $(UV) run pytest -v

test-ontology:  ## Run ontology tests
	cd packages/ontology && $(UV) run pytest -v

# ─── Misc ─────────────────────────────────────────────────────────
clean:  ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
