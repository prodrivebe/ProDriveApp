# ProDrive Production Deployment

Version: Pilot (Sprint 13)

## Architecture

```text
Internet
   │
   ▼
Nginx (TLS termination, static frontend, reverse proxy)
   ├── /              → React dispatcher (frontend/dist)
   ├── /api/          → FastAPI (prodrive-api:8000)
   ├── /ws            → WebSocket upgrade to API
   └── /uploads/      → API file storage

FastAPI API
   ├── PostgreSQL 16 (persistent volume)
   ├── Redis 7 (AOF persistence)
   └── uploads volume (photos, documents, logos)

Optional monitoring profile
   ├── Prometheus
   ├── Alertmanager
   └── Grafana
```

## Prerequisites

| Requirement | Minimum |
|-------------|---------|
| Host OS | Linux (Ubuntu 22.04+ recommended) |
| Docker | 24+ |
| Docker Compose | v2 |
| Domain | DNS A/AAAA record to host |
| TLS | Let's Encrypt or corporate certificate |
| Secrets | Strong JWT secret, DB password, Grafana password |

## 1. Prepare environment

```bash
cp .env.example .env
```

Production values:

```env
APP_ENV=production
DEBUG=false
LOG_JSON=true
JWT_SECRET_KEY=<64-char-random-secret>
POSTGRES_PASSWORD=<strong-password>
CORS_ORIGINS=https://dispatch.yourcompany.com
PUBLIC_DOMAIN=dispatch.yourcompany.com
SEED_PILOT=true
SEED_BETA=false
MAINTENANCE_MODE=false
FEATURE_AI_ENABLED=true
FEATURE_PLANNING_ENABLED=true
FEATURE_REALTIME_ENABLED=true
AUTH_RATE_LIMIT_PER_MINUTE=20
BACKUP_RETENTION_DAYS=14
```

Set `SEED_PILOT=true` only on first deploy. Set to `false` after the pilot company shell is created.

Generate secrets:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 2. Deploy production stack

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Services:

| Service | Role |
|---------|------|
| postgres | Primary database |
| redis | Realtime pub/sub |
| api | FastAPI backend with migrations |
| web | Nginx + React dispatcher |

Verify:

```bash
./scripts/pilot/smoke_test.sh
./scripts/pilot/readiness_check.sh
```

## 3. HTTPS and domain

HTTP-only pilot (internal network):

* Stack exposes port 80 via the `web` service (`WEB_PORT`).

Production HTTPS:

1. Point DNS for `PUBLIC_DOMAIN` to the host.
2. Run `./scripts/pilot/setup-ssl.sh` for certbot instructions.
3. Place certificates in `deployment/nginx/ssl/`.
4. Render `deployment/nginx/conf.d/prodrive-ssl.conf` from the template.
5. Rebuild the `web` image or mount the SSL config.

Update `CORS_ORIGINS` to match the HTTPS dispatcher URL.

## 4. Automated backups

Host cron (recommended):

```cron
0 2 * * * cd /opt/prodrive && ./scripts/backup-all.sh >> ./backups/backup.log 2>&1
```

Docker backup profile (optional):

```bash
docker compose -f docker-compose.prod.yml --profile backup up -d backup
```

Backups:

| Type | Output |
|------|--------|
| Database | `./backups/prodrive_YYYYMMDD_HHMMSS.sql.gz` |
| Uploads | `./backups/uploads_YYYYMMDD_HHMMSS.tar.gz` |

Restore database:

```bash
./scripts/restore-db.sh ./backups/prodrive_YYYYMMDD_HHMMSS.sql.gz
```

Test restore on staging before every production upgrade.

## 5. Monitoring and alerting

Enable monitoring profile:

```bash
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.monitoring.yml --profile monitoring up -d
```

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/health` | Liveness |
| `GET /api/v1/health/ready` | Readiness (DB + Redis) |
| `GET /api/v1/health/ops` | Maintenance mode and feature flags |
| Grafana `:3000` | Pilot dashboard |
| Alertmanager `:9093` | Alert routing |

Configure `ALERT_WEBHOOK_URL` in Alertmanager for Slack, PagerDuty, or email relay.

Schedule `./scripts/pilot/readiness_check.sh` every 5 minutes for external alerting.

## 6. Feature flags and maintenance mode

Toggle without redeploying code (restart API after env change):

| Variable | Effect |
|----------|--------|
| `MAINTENANCE_MODE=true` | Returns 503 for all API routes except health/docs |
| `FEATURE_AI_ENABLED=false` | Disables `/api/v1/ai/*` |
| `FEATURE_PLANNING_ENABLED=false` | Disables `/api/v1/planning/*` |
| `FEATURE_REALTIME_ENABLED=false` | Disables realtime REST and WebSocket |

## 7. Driver app

Build release APK against the production domain:

```bash
cd driver_app
flutter pub get
flutter build apk --release --dart-define=API_BASE_URL=https://dispatch.yourcompany.com/api/v1
```

Distribute via secure MDM or direct APK — not public store for pilot.

## 8. Upgrades

```bash
git pull
docker compose -f docker-compose.prod.yml build api web
docker compose -f docker-compose.prod.yml up -d
./scripts/pilot/smoke_test.sh
```

See `docs/ROLLBACK_PLAN.md` if verification fails.

## 9. Security baseline

* Change all seed passwords after first login
* Restrict port exposure to 443 (and 22 for admin SSH)
* Keep `/docs` internal-only in production
* Review auth logs for brute-force attempts (rate limiting enabled)
* Back up database and uploads volume together

## 10. Related documents

* `docs/PILOT_ONBOARDING.md` — customer onboarding workflow
* `docs/PILOT_SUPPORT.md` — support runbook
* `docs/ROLLBACK_PLAN.md` — rollback procedure
* `docs/BETA_TEST_PLAN.md` — functional validation scenarios
* `docs/SPRINT_013_REPORT.md` — pilot readiness assessment
