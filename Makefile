# Cloud Nexus — Makefile
# Uses Docker Compose v2 (docker compose). Requires .env (copy from .env.example).
#
# Roadmap-aligned builds (see README):
#   Phase 1 — scaffold: core stack (api, web, nginx, worker, automation-runner)
#   Phase 2 — connectors: stub images under services/connector-*
#   Phase 3 — Core UI: Next.js web app (same image as Phase 1; rebuild after UI work)

COMPOSE = docker compose
ENV_FILE = .env

.PHONY: up down build logs migrate seed shell-api shell-web test lint lint-web ci \
	build-phase1 build-phase2 build-phase3 build-all-phases

up:
	$(COMPOSE) --env-file $(ENV_FILE) up -d

down:
	$(COMPOSE) --env-file $(ENV_FILE) down

build:
	$(COMPOSE) --env-file $(ENV_FILE) build

# Phase 1: core application images (docker-compose.yml)
build-phase1:
	$(COMPOSE) --env-file $(ENV_FILE) build api web nginx worker automation-runner

# Phase 2: connector stub images (not started by default compose)
build-phase2:
	docker build -t cloud-nexus-connector-ad ./services/connector-ad
	docker build -t cloud-nexus-connector-cohesity ./services/connector-cohesity
	docker build -t cloud-nexus-connector-idrac ./services/connector-idrac
	docker build -t cloud-nexus-connector-netbox ./services/connector-netbox
	docker build -t cloud-nexus-connector-pbs ./services/connector-pbs
	docker build -t cloud-nexus-connector-proxmox ./services/connector-proxmox
	docker build -t cloud-nexus-connector-pure ./services/connector-pure
	docker build -t cloud-nexus-connector-vsphere ./services/connector-vsphere
	docker build -t cloud-nexus-connector-vyos ./services/connector-vyos

# Phase 3: Core UI (Next.js); rebuild when changing apps/web or shared UI consumed by web
build-phase3:
	$(COMPOSE) --env-file $(ENV_FILE) build web

build-all-phases: build-phase1 build-phase2 build-phase3

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

# API tests/lint: install dev deps in container (root), then run as project user not required for pytest/ruff
test:
	$(COMPOSE) --env-file $(ENV_FILE) run --rm -u root api sh -c "pip install --no-cache-dir -q -r requirements-dev.txt && pytest tests/ -q"

lint:
	$(COMPOSE) --env-file $(ENV_FILE) run --rm -u root api sh -c "pip install --no-cache-dir -q -r requirements-dev.txt && ruff check src"

# Web: requires Node/npm on host (production web image has no devDependencies)
lint-web:
	cd apps/web && npm ci && npm run lint

# API checks via Docker; add `lint-web` locally when Node is available
ci: test lint
