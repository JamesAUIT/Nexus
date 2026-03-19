# Cloud Nexus — Deployment

## Requirements

- Docker and Docker Compose v2
- `.env` file (copy from `.env.example`); set at least:
  - `POSTGRES_PASSWORD`
  - `SECRET_KEY` (min 32 bytes)
  - `ENCRYPTION_KEY` (32 bytes, hex or base64)
  - `ADMIN_PASSWORD` for break-glass admin

## One-shot deploy (Debian 13 VM)

From the repo root on a Debian 13 VM, run:

```bash
sudo ./deploy.sh
```

This will install Docker and Docker Compose (if missing), create `.env` from `.env.example` if needed (you must then edit `.env` and re-run, or use `./deploy.sh --prompt-env` to set secrets interactively), start the stack, run migrations, and seed if `DEMO_MODE=true` or `SEED_DB=1`. Options:

- `--no-install-docker` — skip Docker install (use existing Docker)
- `--skip-seed` — do not run seed even when DEMO_MODE/SEED_DB is set
- `--prompt-env` — when creating `.env`, prompt for required secrets

## Start (manual)

```bash
cp .env.example .env
# Edit .env
docker compose --env-file .env up -d
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m src.db.seed   # with DEMO_MODE=true or SEED_DB=1
```

## Reverse proxy

Use `infra/nginx/` or your own reverse proxy in front of `web:3000` and `api:8000`. Set `NEXT_PUBLIC_API_URL` to the public API base URL so the frontend can call the API.

## Production

- Do not use `DEMO_MODE=true` in production.
- Rotate `SECRET_KEY` and `ENCRYPTION_KEY` via secret manager; do not commit.
- Use TLS at the reverse proxy; keep postgres and redis on internal network only.
