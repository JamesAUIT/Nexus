# Cloud Nexus — Deployment

## Requirements

- Docker and Docker Compose v2
- `.env` file (copy from `.env.example`); set at least:
  - `POSTGRES_PASSWORD`
  - `SECRET_KEY` (min 32 bytes)
  - `ENCRYPTION_KEY` (32 bytes, hex or base64)
  - `ADMIN_PASSWORD` for break-glass admin

## Get the code (Git)

**Clone** (first time on the server):

```bash
git clone https://github.com/JamesAUIT/Nexus.git cloud-nexus
cd cloud-nexus
```

SSH (if your SSH key is added to GitHub):

```bash
git clone git@github.com:JamesAUIT/Nexus.git cloud-nexus
cd cloud-nexus
```

Use your own fork or GitLab URL instead of the above if you host the repo elsewhere.

**Pull updates** (after the repo is already on disk):

```bash
cd /path/to/cloud-nexus
git pull
bash deploy.sh
```

Use the directory that **contains** `deploy.sh` (run `test -f deploy.sh && echo OK`). If `./deploy.sh` says “Permission denied”, run `chmod +x deploy.sh` once or always use `bash deploy.sh`.

Keep `.env` on the server; it is not in Git (see `.gitignore`). Resolve merge conflicts locally if you changed tracked files.

## One-shot deploy (Debian 13 VM)

From the repo root on a Debian 13 VM:

**No sudo** — if Docker Engine and Compose v2 are already installed and your user can run `docker` (e.g. in the `docker` group):

```bash
bash deploy.sh
```

**First-time Docker on the host** (apt install needs root once):

```bash
sudo bash deploy.sh --install-docker
```

After that, use `bash deploy.sh` as a normal user (default is not to run apt).

The script creates `.env` from `.env.example` if needed (you must then edit `.env` and re-run, or use `./deploy.sh --prompt-env` to set secrets interactively), starts the stack, runs migrations, and seeds if `DEMO_MODE=true` or `SEED_DB=1`. Options:

- `--install-docker` — run Debian apt install for Docker (requires root)
- `--no-install-docker` — do not run apt Docker install (default; use existing Docker)
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

## Reverse proxy (HTTPS on 443)

Compose includes **nginx** (`infra/nginx/`) listening on **443** (TLS) and **80** (redirect to HTTPS). The UI and `/api/…` share the same host; leave `NEXT_PUBLIC_API_URL` empty in `.env` for same-origin API calls. Replace the generated self-signed certificate in production (mount real certs or rebuild the image).

For local development without TLS, you can expose `web` on 3000 and `api` on 8000 via `docker-compose.override.yml` (see `docker-compose.override.example.yml`) and set `NEXT_PUBLIC_API_URL=http://localhost:8000`.

## Troubleshooting

| Symptom | What to do |
|--------|------------|
| `-bash: ./deploy.sh#: No such file` | You pasted a `#` from a comment onto the command. Run `./deploy.sh` or `bash deploy.sh` with **no** `#` at the end. |
| `Permission denied` on `./deploy.sh` | Run `chmod +x deploy.sh` once, or use `bash deploy.sh` (no execute bit needed). |
| `deploy.sh` not found | You are not in the repo root. `cd` to the folder that contains `deploy.sh` (avoid nesting clones: e.g. one `git clone …` under `/opt/cloud-nexus`, not `cloud-nexus/cloud-nexus/cloud-nexus`). |

## Production

- Do not use `DEMO_MODE=true` in production.
- Rotate `SECRET_KEY` and `ENCRYPTION_KEY` via secret manager; do not commit.
- Use TLS at the reverse proxy; keep postgres and redis on internal network only.
