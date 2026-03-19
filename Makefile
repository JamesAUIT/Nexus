# Cloud Nexus — Makefile
# Uses Docker Compose v2 (docker compose). Requires .env (copy from .env.example).

COMPOSE = docker compose
ENV_FILE = .env

.PHONY: up down build logs migrate seed shell-api shell-web test lint

up:
	$(COMPOSE) --env-file $(ENV_FILE) up -d

down:
	$(COMPOSE) --env-file $(ENV_FILE) down

build:
	$(COMPOSE) --env-file $(ENV_FILE) build

logs:
	$(COMPOSE) --env-file $(ENV_FILE) logs -f

migrate:
	$(COMPOSE) --env-file $(ENV_FILE) run --rm api alembic upgrade head

seed:
	$(COMPOSE) --env-file $(ENV_FILE) run --rm api python -m src.db.seed

shell-api:
	$(COMPOSE) --env-file $(ENV_FILE) run --rm api sh

shell-web:
	$(COMPOSE) --env-file $(ENV_FILE) run --rm web sh

test:
	$(COMPOSE) --env-file $(ENV_FILE) run --rm api pytest || true

lint:
	$(COMPOSE) --env-file $(ENV_FILE) run --rm api ruff check src || true
