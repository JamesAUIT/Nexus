# Cloud Nexus

A central control plane and operations portal for the cloud/datacentre team. Internal enterprise platform with strong security, Active Directory integration, encrypted secrets, unified infrastructure visibility, reporting, controlled automation, and a Proxmox-focused RVTools-style explorer.

## Architecture

```mermaid
flowchart LR
  subgraph clients [Clients]
    Browser[Browser]
  end
  subgraph edge [Edge]
    Nginx[Nginx optional]
  end
  subgraph app [Application]
    Web[Web Next.js]
    API[API FastAPI]
  end
  subgraph data [Data]
    Postgres[(PostgreSQL)]
    Redis[(Redis)]
  end
  subgraph workers [Workers]
    Worker[Celery Worker]
    Runner[Automation Runner]
  end
  Browser --> Nginx
  Nginx --> Web
  Nginx --> API
  Browser --> Web
  Web --> API
  API --> Postgres
  API --> Redis
  Worker --> Redis
  Worker --> API
  Runner --> API
  Runner --> Redis
```

## Tech Stack

| Layer   | Stack |
|--------|--------|
| Frontend | Next.js 15, TypeScript, App Router, Tailwind CSS, shadcn/ui, TanStack Query, TanStack Table, Zod |
| Backend  | FastAPI, Python 3.12+, SQLAlchemy 2.x, Pydantic v2, Alembic, PostgreSQL, Redis |
| Jobs     | Celery with Redis |
| Auth     | SSO-first (OIDC/SAML), LDAP fallback, local break-glass admin, AD group → role mapping |
| Security | AES-256-GCM for connector secrets, Argon2id for passwords, RBAC, audit logging |

## Prerequisites

- Docker and Docker Compose (v2)
- Make (optional, for convenience targets)

## Quick Start

```bash
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD, SECRET_KEY, ENCRYPTION_KEY, ADMIN_PASSWORD
make up
make migrate
# Optional: set DEMO_MODE=true or SEED_DB=1 in .env then:
make seed
```

- **Web UI (HTTPS via nginx):** https://localhost:443 (self-signed certificate; browser will warn)  
- **API:** same host, paths under `/api/…` and `/health` (or expose ports with `docker-compose.override.yml`; see [.env.example](.env.example))  
- **API docs:** https://localhost/docs  

## Environment

See [.env.example](.env.example). Never commit `.env` or secrets. Connector secrets are encrypted at rest with AES-256-GCM.

## Project Structure

See [STRUCTURE.md](STRUCTURE.md) for the full tree.

- **apps/web** — Next.js frontend  
- **apps/api** — FastAPI backend  
- **services/worker** — Celery worker  
- **services/automation-runner** — Automation runner (stub in Phase 1)  
- **services/connector-*** — Integration connectors (NetBox, Proxmox, vSphere, etc.)  
- **packages/** — shared-types, shared-ui, shared-utils  
- **infra/** — Docker and nginx config  
- **docs/** — Architecture, deployment, development  

## Development

| Command | Description |
|---------|-------------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make build` | Rebuild images |
| `make logs` | Follow logs |
| `make migrate` | Run DB migrations |
| `make seed` | Seed demo data (when DEMO_MODE or SEED_DB=1) |
| `make shell-api` | Shell in API container |
| `make shell-web` | Shell in Web container |
| `make test` | Run API tests (pytest in `api` container; installs `requirements-dev.txt`) |
| `make lint` | Ruff check API (`src` in container) |
| `make lint-web` | Next.js ESLint (requires Node/npm on host) |
| `make ci` | `test` + `lint` (API via Docker) |

## Deployment

- Clone or `git pull` on the server, then run `bash deploy.sh` (see [Deployment](docs/deployment.md) for Git URLs, Debian steps, and troubleshooting).
- Use Docker Compose with env-based config.
- Put a reverse proxy (e.g. nginx) in front of web and api; see `infra/nginx/`.
- Do not commit secrets; inject via env or secret manager.

## Security

- No secrets in the repository.
- Connector credentials encrypted at rest (AES-256-GCM).
- Local admin password hashed with Argon2id.
- RBAC on protected endpoints; sensitive actions audited.

## Roadmap

- **Phase 1:** Scaffold, Docker, backend/frontend base, auth/encryption/RBAC, seed — **delivered** (CI runs API tests + Ruff and web lint/build).
- **Phase 2:** Connector framework, **live NetBox (sites) & Proxmox (cluster resources) sync**, vSphere/VyOS/AD config stubs, sync jobs, drift/audit — **delivered** (extend connectors as needed).
- **Phase 3:** Core UI (search, links, reports, runbooks, saved queries, health checks).
- **Phase 4:** Script library, automation-runner, Proxmox Explorer, Cloud Ops, exports, docs polish.

### Project status (what “complete” means here)

**Phase 1 is complete:** you can clone, configure `.env`, run `deploy.sh` or `docker compose up --build`, migrate, and operate the platform. GitHub Actions validates API (Ruff + pytest) and web (ESLint + production build) on each push/PR.

**Phase 2 is complete** for the scoped integrations: registry-based connectors, Celery sync jobs, drift run endpoint, **live NetBox site sync** and **live Proxmox resource sync**, with vSphere/VyOS/AD remaining config-level stubs until extended.

**Phases 3–4 and hardening** (richer UI, automation-runner, email, SSO, rate limits, deeper NetBox objects, etc.) are tracked in [Production hardening & TODOs](docs/PRODUCTION-HARDENING.md).

## Documentation

- [Architecture](docs/architecture.md)
- [Deployment](docs/deployment.md)
- [Development](docs/development.md)
- [Production hardening & TODOs](docs/PRODUCTION-HARDENING.md)
