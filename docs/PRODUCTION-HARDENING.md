# Cloud Nexus — Production Hardening, Security, and TODOs

## Security gaps and mitigations

| Area | Gap | Mitigation |
|------|-----|------------|
| **Secrets** | Default `secret_key` and `encryption_key` in settings | Set env vars in production; rotate keys via secure process |
| **Admin password** | Default `changeme` when `DEMO_MODE` is false | Require strong password; document break-glass procedure |
| **CORS** | May need explicit origins in production | Configure `CORSMiddleware` with allowed origins |
| **Rate limiting** | No rate limiting on auth or API | Add rate limiting (e.g. slowapi) for login and sensitive endpoints |
| **HTTPS** | No TLS termination in app | Use reverse proxy (nginx) for TLS; set `X-Forwarded-*` and `trusted_proxy` |
| **Audit** | Some mutations may not log to audit_log | Review all POST/PUT/DELETE; ensure `log_audit` where appropriate |
| **Script execution** | Script Library records execution but no runner | Do not connect arbitrary runner from UI; use approved automation-runner only |

## Placeholder / stub integrations

- **Proxmox connector**: `test_connectivity` and `sync` are stubs; no real Proxmox API calls.
- **NetBox / vSphere / VyOS / AD connectors**: Stub implementations.
- **iDRAC scan**: Writes placeholder BIOS/iDRAC version; no Redfish API.
- **Drift service**: Creates findings from DB state; no live NetBox comparison.
- **Operations Requests send**: Status set to `sent` but no email sent; integrate with mail gateway.
- **Report CSV/XLSX**: Run creates run record only; file generation not implemented.
- **HAProxy push/rollback**: Placeholder endpoints return "not implemented".
- **Health checks**: Stale snapshots and storage threshold logic are stubs.

## Production hardening checklist

- [ ] Set `SECRET_KEY`, `ENCRYPTION_KEY`, `ADMIN_PASSWORD` from secure store.
- [ ] Disable or restrict `DEMO_MODE` and `SEED_DB` in production.
- [ ] Configure CORS and trusted proxy.
- [ ] Enable rate limiting on auth and write endpoints.
- [ ] Run migrations from CI/CD or release process; never auto-migrate on app startup in production.
- [ ] Back up PostgreSQL and encrypted connector configs.
- [ ] Use dedicated DB user with least privilege; no superuser for app.
- [ ] Log to structured logger (JSON) and ship to SIEM.
- [ ] Harden Redis (password, no external bind if not needed).

## TODOs (codebase)

- Automation-runner service: execute approved scripts only; no UI-triggered arbitrary execution.
- Email integration for Operations Requests (SMTP or API).
- Real Proxmox/NetBox sync and Redfish iDRAC fetch.
- Report and health-check logic (CSV export, full check implementations).
- Load balancer config push/rollback implementation.
- Optional: SSO/OIDC and LDAP wiring (settings exist; routes to implement).

## Naming and consistency

- Product name: **Cloud Nexus** (titles, nav, docs, UI headers).
- API: `/api/v1/` prefix; kebab-case for multi-word paths.
- Frontend: Next.js App Router; `(dashboard)` group; page titles and sidebar labels aligned with docs.
