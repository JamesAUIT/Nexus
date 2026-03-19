# Cloud Nexus — Monorepo structure

```
cloud-nexus/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docker-compose.override.example.yml
├── Makefile
├── STRUCTURE.md
│
├── apps/
│   ├── web/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── next.config.js
│   │   ├── tailwind.config.ts
│   │   ├── postcss.config.js
│   │   ├── components.json
│   │   ├── next-env.d.ts
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── public/
│   │   │   └── .gitkeep
│   │   └── src/
│   │       ├── app/
│   │       │   ├── layout.tsx
│   │       │   ├── page.tsx
│   │       │   ├── globals.css
│   │       │   ├── api/
│   │       │   │   └── .gitkeep
│   │       │   ├── (auth)/
│   │       │   │   ├── layout.tsx
│   │       │   │   └── login/
│   │       │   │       └── page.tsx
│   │       │   └── (dashboard)/
│   │       │       ├── layout.tsx
│   │       │       ├── dashboard/
│   │       │       ├── search/
│   │       │       ├── sites/
│   │       │       ├── racks/
│   │       │       ├── hosts/
│   │       │       ├── vms/
│   │       │       ├── containers/
│   │       │       ├── storage/
│   │       │       ├── backups/
│   │       │       ├── network/
│   │       │       ├── drift/
│   │       │       ├── sync-jobs/
│   │       │       ├── audit/
│   │       │       ├── settings/
│   │       │       ├── links/
│   │       │       ├── reports/
│   │       │       ├── runbooks/
│   │       │       ├── script-library/
│   │       │       ├── health/
│   │       │       ├── saved-queries/
│   │       │       ├── proxmox-explorer/
│   │       │       └── cloud-ops/
│   │       │           ├── page.tsx
│   │       │           ├── patch/
│   │       │           ├── load-balancer/
│   │       │           ├── diagnostics/
│   │       │           └── snapshots/
│   │       ├── components/
│   │       │   ├── app-sidebar.tsx
│   │       │   └── ui/
│   │       │       ├── button.tsx
│   │       │       ├── card.tsx
│   │       │       ├── input.tsx
│   │       │       ├── label.tsx
│   │       │       ├── table.tsx
│   │       │       ├── dropdown-menu.tsx
│   │       │       └── avatar.tsx
│   │       ├── providers/
│   │       │   └── query-provider.tsx
│   │       ├── lib/
│   │       │   ├── api.ts
│   │       │   ├── utils.ts
│   │       │   └── query-client.ts
│   │       ├── hooks/
│   │       │   └── index.ts
│   │       └── types/
│   │           └── index.ts
│   │
│   └── api/
│       ├── pyproject.toml
│       ├── requirements.txt
│       ├── Dockerfile
│       ├── .dockerignore
│       ├── alembic.ini
│       ├── alembic/
│       │   ├── env.py
│       │   ├── script.py.mako
│       │   └── versions/
│       │       └── 001_initial.py
│       └── src/
│           ├── __init__.py
│           ├── main.py
│           ├── config/
│           │   ├── __init__.py
│           │   └── settings.py
│           ├── db/
│           │   ├── __init__.py
│           │   ├── base.py
│           │   ├── session.py
│           │   └── seed.py
│           ├── models/
│           │   ├── __init__.py
│           │   ├── role.py
│           │   ├── user.py
│           │   ├── connector.py
│           │   ├── site.py
│           │   └── audit_log.py
│           ├── schemas/
│           │   ├── __init__.py
│           │   ├── user.py
│           │   └── connector.py
│           ├── api/
│           │   ├── deps.py
│           │   ├── auth/
│           │   │   ├── __init__.py
│           │   │   └── routes.py
│           │   └── v1/
│           │       ├── __init__.py
│           │       ├── router.py
│           │       └── sites.py
│           ├── core/
│           │   ├── __init__.py
│           │   ├── security.py
│           │   ├── encryption.py
│           │   ├── rbac.py
│           │   └── audit.py
│           ├── services/
│           │   └── __init__.py
│           └── tasks/
│               └── __init__.py
│
├── services/
│   ├── worker/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── src/
│   │       ├── __init__.py
│   │       └── celery_app.py
│   ├── automation-runner/
│   │   ├── Dockerfile
│   │   └── src/
│   │       └── runner.py
│   ├── connector-netbox/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── src/
│   │       ├── __init__.py
│   │       └── client.py
│   ├── connector-proxmox/
│   ├── connector-vsphere/
│   ├── connector-pure/
│   ├── connector-idrac/
│   ├── connector-cohesity/
│   ├── connector-pbs/
│   ├── connector-vyos/
│   └── connector-ad/
│       └── (same: Dockerfile, pyproject.toml, src/__init__.py, src/client.py)
│
├── packages/
│   ├── shared-types/
│   │   ├── package.json
│   │   └── src/
│   │       └── index.ts
│   ├── shared-ui/
│   │   ├── package.json
│   │   └── src/
│   │       └── index.ts
│   └── shared-utils/
│       ├── package.json
│       └── src/
│           └── index.ts
│
├── infra/
│   ├── docker/
│   │   └── .dockerignore
│   └── nginx/
│       ├── Dockerfile
│       └── nginx.conf
│
└── docs/
    ├── architecture.md
    ├── deployment.md
    └── development.md
```

Each `connector-*` service has: `Dockerfile`, `pyproject.toml`, `src/__init__.py`, `src/client.py` (stub).
