# Sprint 13 Report — Pilot Customer Readiness and Production Deployment

Date: 2026-08-09

## Summary

Sprint 13 prepares ProDrive for deployment to a real transport company in a controlled pilot. No new business features were added. Work focused on production deployment architecture, HTTPS/reverse proxy, automated backups, monitoring and alerting configuration, operational tooling (import/export/support CLI), environment-driven feature flags and maintenance mode, auth rate limiting, and pilot documentation.

## What was implemented

### Production deployment

| Area | Deliverable |
|------|-------------|
| Architecture | Full-stack `docker-compose.prod.yml` (postgres, redis, api, web) |
| Reverse proxy | Nginx config in `deployment/nginx/` + `frontend/Dockerfile` |
| HTTPS | SSL template + `scripts/pilot/setup-ssl.sh` |
| Monitoring | Optional `docker-compose.monitoring.yml` (Prometheus, Grafana, Alertmanager) |
| Backups | Enhanced `backup-db.sh`, new `backup-uploads.sh`, `backup-all.sh`, scheduler profile |

### Operational tooling (CLI, not UI features)

| Tool | Purpose |
|------|---------|
| `app/scripts/seed_pilot.py` | Empty pilot company shell |
| `app/scripts/pilot_import.py` | CSV import (customers, drivers, trucks, trailers) |
| `app/scripts/pilot_export.py` | Export orders, audit logs, documents/photos |
| `app/scripts/pilot_support.py` | List users, reset passwords, company summary |
| `scripts/pilot/*.sh` | Shell wrappers for host operations |
| `scripts/pilot/templates/*.csv` | Import templates |

### Reliability and security

| Area | Change |
|------|--------|
| Maintenance mode | `MAINTENANCE_MODE` middleware — 503 except health/docs |
| Feature flags | `FEATURE_AI_ENABLED`, `FEATURE_PLANNING_ENABLED`, `FEATURE_REALTIME_ENABLED` |
| Auth rate limiting | `AUTH_RATE_LIMIT_PER_MINUTE` on login/refresh/reset |
| Ops endpoint | `GET /api/v1/health/ops` — flags and maintenance status |
| Bug fix | Missing `orders_router` import in `main.py` |

### Testing

| Suite | Purpose |
|-------|---------|
| `tests/test_pilot_ops.py` | Maintenance mode, feature flags, rate limit, ops endpoint |

### Documentation

* `docs/PRODUCTION_DEPLOYMENT.md`
* `docs/PILOT_ONBOARDING.md`
* `docs/PILOT_SUPPORT.md`
* `docs/ROLLBACK_PLAN.md`
* `docs/SPRINT_013_REPORT.md` (this document)

## Deployment checklist

### Infrastructure

- [ ] Linux host with Docker 24+ and Compose v2
- [ ] DNS A/AAAA record for dispatcher domain
- [ ] TLS certificate installed (Let's Encrypt or corporate)
- [ ] Firewall: expose 443 (and 22 for admin SSH only)
- [ ] `.env` production secrets configured
- [ ] `JWT_SECRET_KEY` unique and 32+ characters
- [ ] `CORS_ORIGINS` matches HTTPS dispatcher URL
- [ ] `PUBLIC_DOMAIN` set

### Deploy and verify

- [ ] `docker compose -f docker-compose.prod.yml up --build -d`
- [ ] `GET /api/v1/health` returns healthy
- [ ] `GET /api/v1/health/ready` returns ready
- [ ] `GET /api/v1/health/ops` shows expected feature flags
- [ ] `./scripts/pilot/smoke_test.sh` passes
- [ ] `./scripts/pilot/readiness_check.sh` passes
- [ ] Pilot seed or import completed (`SEED_PILOT` or CSV import)
- [ ] Default passwords changed

### Backups and recovery

- [ ] `./scripts/backup-all.sh` runs successfully
- [ ] Backup retention configured (`BACKUP_RETENTION_DAYS`)
- [ ] Optional backup scheduler profile enabled
- [ ] Restore tested on staging (`docs/ROLLBACK_PLAN.md`)

### Monitoring and alerting

- [ ] JSON logs shipped to aggregation platform
- [ ] Readiness check scheduled (cron every 5 min)
- [ ] Optional Grafana/Prometheus profile deployed
- [ ] Alert webhook configured (`ALERT_WEBHOOK_URL`)
- [ ] Disk usage monitoring for uploads volume

### Customer onboarding

- [ ] `docs/PILOT_ONBOARDING.md` workflow completed
- [ ] Fleet and customers imported or entered
- [ ] Dispatcher and driver accounts provisioned
- [ ] Driver APK built with production API URL
- [ ] `docs/BETA_TEST_PLAN.md` scenarios executed with partner

### Support readiness

- [ ] `docs/PILOT_SUPPORT.md` shared with support team
- [ ] Escalation contacts documented
- [ ] Export/audit tools tested once
- [ ] Maintenance mode drill performed

## Pilot readiness assessment

| Area | Status | Notes |
|------|--------|-------|
| Production deployment stack | **Ready** | Docker Compose with nginx frontend |
| HTTPS / TLS | **Conditional** | Template and scripts provided; operator must configure certs |
| Database backup automation | **Ready** | Scripts + optional scheduler profile |
| File storage backup | **Ready** | `backup-uploads.sh` + full backup script |
| Monitoring dashboard | **Ready** | Grafana profile + health/ops endpoints |
| Error alerting | **Conditional** | Alertmanager/webhook requires operator config |
| Audit log access | **Ready** | Export CLI + SQL; no in-app viewer |
| User activity reporting | **Ready** | Existing KPI/reports API and dashboard |
| Company onboarding | **Ready** | Documented workflow + pilot seed + CSV import |
| Import tools | **Ready** | CSV templates and CLI |
| Export tools | **Ready** | Orders, audit, documents archive |
| System settings | **Partial** | API available; UI read-only |
| Feature flags | **Ready** | Environment variables + ops endpoint |
| Maintenance mode | **Ready** | Environment variable + middleware |
| Admin support tools | **Ready** | CLI scripts documented |
| Auth rate limiting | **Ready** | Per-IP limit on auth endpoints |
| Security baseline | **Conditional** | Requires TLS, secrets, password rotation |
| Flutter CI | **Not ready** | Manual device testing still required |
| FCM push notifications | **Not ready** | In-app only |

### Overall verdict

**ProDrive is ready for a controlled pilot** with one transport company when:

1. Production deployment checklist above is complete
2. TLS and secrets are configured
3. Backup/restore is verified on staging
4. Pilot partner completes validation in `docs/BETA_TEST_PLAN.md`
5. Support team has runbook access (`docs/PILOT_SUPPORT.md`)

Not ready for:

* Public self-service signup
* Multi-region SLA
* Unsupervised production operations without monitoring
* Autonomous dispatching

## Issue register (Sprint 13 review)

### Critical

| ID | Type | Description | Mitigation |
|----|------|-------------|------------|
| C-01 | Security | TLS must be configured by operator | `setup-ssl.sh`, SSL nginx template |
| C-02 | Operations | Backup restore must be tested | Rollback plan + staging drill |
| C-03 | Security | Uploads volume loss if not backed up | `backup-uploads.sh` in `backup-all.sh` |

### High

| ID | Type | Description | Mitigation |
|----|------|-------------|------------|
| H-01 | Feature | No FCM push | Document in support runbook |
| H-02 | UX | Settings UI read-only | API updates documented |
| H-03 | Testing | Flutter not in CI | Manual pilot device testing |
| H-04 | Ops | No in-app audit viewer | Export CLI + SQL documented |
| H-05 | Security | No account lockout (only rate limit) | Monitor auth logs |

### Medium

| ID | Type | Description | Mitigation |
|----|------|-------------|------------|
| M-01 | Ops | Grafana dashboard minimal | Extend with log-based metrics post-pilot |
| M-02 | Feature | No in-app onboarding wizard | `PILOT_ONBOARDING.md` manual wizard |
| M-03 | AI | Heuristic parsers | Set partner expectations |
| M-04 | Feature | Customer create/edit UI deferred | CSV import |

## Test commands

```bash
cd backend
pytest tests/test_pilot_ops.py tests/test_health.py -q
pytest -q

cd ../frontend
npm test
npm run build

./scripts/pilot/smoke_test.sh
./scripts/pilot/readiness_check.sh
```

## Definition of Done

- [x] Production deployment architecture documented and implemented
- [x] HTTPS/reverse proxy configuration
- [x] Production Docker setup with frontend
- [x] Database and file backup automation
- [x] Monitoring dashboard configuration (Grafana profile)
- [x] Error alerting configuration (Alertmanager + readiness script)
- [x] Audit and activity access documented (export + existing reports)
- [x] Onboarding workflow documented with import tools
- [x] Export and support CLI tools
- [x] Feature flags and maintenance mode
- [x] Auth rate limiting
- [x] Pilot documentation pack
- [x] Deployment checklist and pilot readiness assessment
