# Cloud Nexus — Development

## Local setup

1. Copy `.env.example` to `.env` and set `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `ENCRYPTION_KEY`, `ADMIN_PASSWORD`. For local Docker, use service names: `postgres`, `redis`.
2. Start stack: `make up` or `docker compose up -d`.
3. Migrate: `make migrate` (see **Migrations** below).
4. Seed (optional): set `DEMO_MODE=true` or `SEED_DB=1` in `.env`, then `make seed` (see **Seed data & demo mode**).
5. Web: http://localhost:3000 — API: http://localhost:8000 — Docs: http://localhost:8000/docs.

## Migrations

- Backend uses Alembic. Migrations live in `apps/api/alembic/versions/`.
- Apply all: from `apps/api`, run `alembic upgrade head`.
- Create new: `alembic revision -m "description"`, then edit the generated file.
- Downgrade one step: `alembic downgrade -1`.

## Seed data & demo mode

- Seed runs only when `DEMO_MODE=true` or `SEED_DB=1` (or env `SEED_DB=1`). It creates admin user, sample site/rack/cluster/host/VM, connectors, sync job, useful links, runbooks, report/health definitions, link templates, script definitions, ops request templates, and sample change event.
- With demo mode, default admin password is `admin` (override with `ADMIN_PASSWORD`). Without demo mode, use `ADMIN_PASSWORD` for the break-glass admin.
- Run seed: from repo root `make seed`, or from `apps/api`: `python -m src.db.seed` (with `PYTHONPATH` set to include `apps/api`).

## Backend tests

- From repo root: `make test` (runs pytest in API container).
- From `apps/api`: `pytest tests/ -v` (ensure `PYTHONPATH` includes `apps/api` so `src` resolves, or run `python -m pytest tests/ -v` from `apps/api` with `PYTHONPATH=.`).
- Tests live in `apps/api/tests/`. Basic smoke tests: health, OpenAPI schema, API v1 paths.

## Frontend smoke tests

- From `apps/web`: `npm run build` to verify the app builds.
- Optional: add Playwright or Cypress for E2E; currently no automated frontend tests. Manual smoke: log in, open Dashboard, Search, and one list page (e.g. VMs).

## Docker startup

- `docker compose up -d` starts postgres, redis, api, web (and optional worker). Ensure `.env` has correct `DATABASE_URL` and `REDIS_URL` for the compose network.
- First run: run migrations and optionally seed as above.

## Running API or Web alone

- API: from `apps/api`, `pip install -r requirements.txt`, set `DATABASE_URL`/`REDIS_URL` to local postgres/redis, then `uvicorn src.main:app --reload`.
- Web: from `apps/web`, `npm install`, `npm run dev`. Set `NEXT_PUBLIC_API_URL=http://localhost:8000`.

## Monorepo layout

- `apps/api` — FastAPI backend.
- `apps/web` — Next.js frontend.
- `services/worker` — Celery worker.
- `services/automation-runner` — Automation runner (stub).
- `services/connector-*` — Connectors (Phase 2).
- `packages/shared-types`, `shared-ui`, `shared-utils` — Shared code.
- `infra/` — Docker and nginx config.
- `docs/` — Architecture, deployment, development.

## Making changes

- Backend: add models in `apps/api/src/models/`, schemas in `schemas/`, routes under `api/v1/`. Create Alembic migration for schema changes.
- Frontend: add pages under `app/(dashboard)/`, components in `components/`. Use `@/lib/api` for API calls.
- Follow existing patterns; keep RBAC and audit in mind for new endpoints.
