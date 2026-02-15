.PHONY: up down build dev-backend dev-frontend lint test db-migrate doctor loadtest loadtest-trend

up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

dev-backend:
	cd backend && poetry run uvicorn src.null_engine.main:app --reload --host 0.0.0.0 --port 3301

dev-frontend:
	cd frontend && pnpm dev

lint:
	cd backend && poetry run ruff check src tests
	cd frontend && pnpm lint

test:
	cd backend && poetry run pytest
	cd frontend && pnpm test

db-migrate:
	cd backend && poetry run alembic upgrade head

db-revision:
	cd backend && poetry run alembic revision --autogenerate -m "$(msg)"

doctor:
	@echo "[root] python: $$(python3 --version 2>&1)"
	@echo "[backend] poetry: $$(cd backend && poetry --version 2>&1)"
	@echo "[backend] runtime python: $$(cd backend && poetry run python --version 2>&1)"
	@echo "[frontend] node: $$(node --version 2>&1)"
	@echo "[frontend] pnpm: $$(pnpm --version 2>&1)"

loadtest:
	cd backend && poetry run python scripts/loadtest.py --base-url http://localhost:3301 --requests 400 --concurrency 20

loadtest-trend:
	cd backend && poetry run python scripts/loadtest.py --base-url http://localhost:3301 --requests 600 --concurrency 30 --history-out ../artifacts/loadtest-history.jsonl --trend-out ../artifacts/loadtest-trend.md --history-window 30
