# ProDrive Pilot Support Runbook

Support guide for engineering and customer success during the controlled pilot.

## Support tiers

| Tier | Scope | Response target |
|------|-------|-----------------|
| L1 | Customer admin — passwords, user creation, basic navigation | 4 business hours |
| L2 | Engineering — data issues, workflow bugs, import/export | 1 business day |
| L3 | Engineering lead — data loss, security, outage | 4 hours (business) |

## Common requests

### Reset user password

```bash
./scripts/pilot/support-tools.sh reset-password user@company.com 'NewSecurePass1!'
```

Or use password reset flow: `POST /api/v1/auth/password-reset/request`.

### List company users

```bash
./scripts/pilot/support-tools.sh list-users
```

### Export orders for customer reporting

```bash
./scripts/pilot/export-data.sh orders ./exports/orders.csv
```

### Export audit trail

```bash
./scripts/pilot/export-data.sh audit ./exports/audit.json --audit-limit 5000
```

Audit log viewer: export JSON and review in any JSON viewer, or query PostgreSQL:

```sql
SELECT created_at, entity, action, user_id, old_value, new_value
FROM audit_logs
WHERE company_id = '<company-uuid>'
ORDER BY created_at DESC
LIMIT 100;
```

### Export documents and photos

```bash
./scripts/pilot/export-data.sh documents ./exports/evidence.zip
```

Requires access to the uploads volume (`UPLOAD_ROOT_DIR`).

## Monitoring dashboard

| Tool | URL | Use |
|------|-----|-----|
| Grafana | `http://<host>:3000` | Availability overview |
| Health ops | `GET /api/v1/health/ops` | Maintenance and feature flags |
| KPI API | `GET /api/v1/reports/kpi` | User activity summary |
| JSON logs | Docker `logs prodrive-api` | Request errors, auth failures |

User activity dashboard: dispatcher **Dashboard** page and `GET /api/v1/reports/kpi`, `/reports/drivers`, `/reports/orders`.

## Error alerting

1. Schedule `./scripts/pilot/readiness_check.sh` every 5 minutes.
2. Configure `ALERT_WEBHOOK_URL` in Alertmanager for Slack or email.
3. Alert on:
   * Readiness probe failure
   * Maintenance mode unexpectedly enabled
   * Elevated 5xx rate in JSON logs (`status=500`)

Example log filter (Loki/CloudWatch):

```text
{container="prodrive-api"} |= "request completed" | status >= 500
```

## Maintenance mode

Enable for planned upgrades:

```env
MAINTENANCE_MODE=true
MAINTENANCE_MESSAGE=ProDrive is undergoing scheduled maintenance. Retry in 15 minutes.
```

Restart API:

```bash
docker compose -f docker-compose.prod.yml up -d api
```

Health endpoints remain available. Dispatcher shows API errors until maintenance is disabled.

## Feature flags

Disable features during incidents without full outage:

```env
FEATURE_AI_ENABLED=false
FEATURE_PLANNING_ENABLED=false
FEATURE_REALTIME_ENABLED=false
```

Restart API after change. Verify via `GET /api/v1/health/ops`.

## Admin support tools

| Tool | Command |
|------|---------|
| Import CSV data | `./scripts/pilot/import-data.sh <entity> <file.csv>` |
| Export orders | `./scripts/pilot/export-data.sh orders <file.csv>` |
| Export audit | `./scripts/pilot/export-data.sh audit <file.json>` |
| Export evidence | `./scripts/pilot/export-data.sh documents <file.zip>` |
| List users | `./scripts/pilot/support-tools.sh list-users` |
| Reset password | `./scripts/pilot/support-tools.sh reset-password <email> <password>` |
| Company summary | `./scripts/pilot/support-tools.sh company-summary` |
| Smoke test | `./scripts/pilot/smoke_test.sh` |
| Readiness check | `./scripts/pilot/readiness_check.sh` |
| Full backup | `./scripts/backup-all.sh` |
| DB restore | `./scripts/restore-db.sh <backup.sql.gz>` |

## Incident checklist

1. Confirm scope — one user, one company, or full outage?
2. Check `./scripts/pilot/readiness_check.sh`
3. Inspect `docker compose -f docker-compose.prod.yml logs api --tail 200`
4. Check disk space on uploads volume
5. If data corruption suspected — stop writes, enable maintenance mode, restore from backup
6. Document incident in pilot channel; update `docs/SPRINT_013_REPORT.md` issue register if new gap found

## Known pilot limitations

Refer to `docs/SPRINT_013_REPORT.md` for the full register. Key items:

* No FCM push — in-app notifications only
* No in-app audit viewer — use export or SQL
* Settings page read-only in UI — use API
* No account lockout beyond auth rate limiting
* Flutter app not in CI — manual device testing required

## Escalation contacts

| Role | Responsibility |
|------|----------------|
| Engineering on-call | Outages, data recovery |
| Product owner | Scope, pilot timeline |
| Customer admin | User management, training |

Fill in names and contact details before go-live.
