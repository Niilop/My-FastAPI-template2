.DEFAULT_GOAL := help
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 5173
.PHONY: help setup dev backend frontend migrate check check-backend check-frontend smoke

help:
	@printf '%s\n' 'make setup          Install locked dependencies; create .env if absent' 'make dev            Start backend and frontend; Ctrl+C stops both' 'make backend        Start only the backend with reload' 'make frontend       Start only the frontend' 'make migrate        Apply migrations to the configured database' 'make check          Run backend and frontend checks (Chromium required)' 'make check-backend  Run Ruff and pytest' 'make check-frontend Run lint, formatting, build, and mocked browser tests' 'make smoke          Build and test the full stack in disposable Docker containers'

setup:
	uv sync --all-packages --locked
	uv run --no-sync python -m scripts.setup_env
	npm --prefix frontend ci

dev:
	uv run --no-sync python -m scripts.dev --backend-port $(BACKEND_PORT) --frontend-port $(FRONTEND_PORT)

backend:
	uv run --no-sync uvicorn backend.main:app --reload

frontend:
	npm --prefix frontend run dev

migrate:
	uv run --no-sync alembic -c backend/alembic.ini upgrade head

check: check-backend check-frontend

check-backend:
	uv run --no-sync ruff check .
	uv run --no-sync ruff format --check .
	uv run --no-sync pytest

check-frontend:
	npm --prefix frontend run lint
	npm --prefix frontend run format:check
	npm --prefix frontend run build
	npm --prefix frontend test

smoke:
	bash scripts/smoke.sh
