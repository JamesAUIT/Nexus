# Cloud Nexus — Architecture

## Overview

Cloud Nexus is a central control plane and operations portal for the cloud/datacentre team. It integrates multiple systems (Proxmox, vSphere, NetBox, Pure, iDRAC, Cohesity, PBS, VyOS, AD) with a single UI, RBAC, audit logging, and encrypted connector secrets.

## Principles

- **NetBox as source of truth** for intended state; other systems are discovered live state.
- **Drift detection** between intended and live state.
- **SSO-first** auth with LDAP fallback and local break-glass admin.
- **No secrets in repo**; connector credentials encrypted at rest (AES-256-GCM).
- **RBAC** on every protected endpoint; all sensitive actions audited.

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, TypeScript, App Router, Tailwind, shadcn/ui, TanStack Query, Zod |
| Backend | FastAPI, Python 3.12+, SQLAlchemy 2.x, Pydantic v2, Alembic |
| Data | PostgreSQL, Redis |
| Jobs | Celery (Redis broker) |
| Deployment | Docker Compose, optional nginx reverse proxy |

## Containers

- **web** — Next.js app (port 3000).
- **api** — FastAPI app (port 8000).
- **worker** — Celery worker.
- **automation-runner** — Stub in Phase 1; runs scripts/automation in Phase 4.
- **postgres** — PostgreSQL 16.
- **redis** — Redis 7.
- **nginx** (optional) — Reverse proxy for web + api.

## Modules (UI)

Dashboard, Search, Sites, Racks, Hosts, VMs, Containers, Storage, Backups, Network, Drift, Sync Jobs, Audit Log, Settings, Useful Links, Reports, Runbooks, Script Library, Health Checks, Saved Queries, Proxmox Explorer, Cloud Ops (Patch, Load Balancer, Diagnostics, Snapshots).

## Roadmap

- **Phase 1**: Scaffold (this document and repo state).
- **Phase 2**: Connector framework; **NetBox (sites)** and **Proxmox (cluster resources)** live sync; vSphere/VyOS/AD stubs; sync jobs; drift/audit framework.
- **Phase 3**: Core UI, search, links, reports, runbooks, saved queries, health checks.
- **Phase 4**: Script library, automation-runner, Proxmox Explorer, Cloud Ops, exports, tests.
