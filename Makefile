.PHONY: install dev-backend dev-frontend test test-backend test-frontend lint typecheck migrate seed

install:
	uv sync --dev
	cd apps/web && npm install

dev-backend:
	uv run uvicorn services.api_gateway.app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd apps/web && npm run dev

test:
	uv run pytest

test-backend:
	uv run pytest tests services

test-frontend:
	cd apps/web && npm test -- --runInBand

lint:
	uv run ruff check .

typecheck:
	cd apps/web && npm run typecheck

migrate:
	uv run alembic upgrade head

seed:
	uv run python scripts/seed_database.py
