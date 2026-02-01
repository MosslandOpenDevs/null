.PHONY: up down build dev-backend dev-frontend lint test db-migrate

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
