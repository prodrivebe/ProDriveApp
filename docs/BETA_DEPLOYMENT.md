# ProDrive Beta Deployment Guide

## Overview

This guide covers deploying ProDrive for a single-tenant beta pilot with Docker Compose. For multi-tenant SaaS production, add a reverse proxy, TLS, and managed PostgreSQL/Redis.

## Prerequisites

* Docker 24+ and Docker Compose v2
* Domain or static IP for beta host
* TLS certificate (Let's Encrypt recommended)
* Secrets manager or secure `.env` storage

## 1. Configure environment

```bash
cp .env.example .env
```

Required production values:

```env
APP_ENV=production
DEBUG=false
LOG_JSON=true
JWT_SECRET_KEY=<generate-64-char-random-secret>
POSTGRES_PASSWORD=<strong-password>
CORS_ORIGINS=https://beta.yourcompany.com
SEED_BETA=true
```

Generate a secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**Important:** Set `SEED_BETA=true` only on first deploy. Set to `false` after seed completes.

## 2. Deploy stack

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Services:

| Service | Purpose |
|---------|---------|
| postgres | Primary database with persistent volume |
| redis | Real-time pub/sub and presence |
| api | FastAPI backend with migrations on startup |

## 3. Verify deployment

```bash
curl -s http://localhost:8000/api/v1/health
curl -s http://localhost:8000/api/v1/health/ready
./scripts/beta/smoke_test.sh
```

Readiness returns `503` if database or Redis is unavailable.

## 4. Dispatcher frontend

Build and serve the React app behind the same domain or a subdomain:

```bash
cd frontend
npm ci
npm run build
```

Serve `frontend/dist` via Nginx/Caddy with API proxied to port 8000.

Example Nginx locations:

* `/api/` → `http://127.0.0.1:8000/api/`
* `/uploads/` → `http://127.0.0.1:8000/uploads/`
* `/` → static files from `frontend/dist`

## 5. Driver app

Point the Flutter app API base URL to the beta host. Build release APK:

```bash
cd driver_app
flutter pub get
flutter build apk --release
```

Distribute APK via secure channel (not public store for beta).

## 6. Backup and recovery

### Backup

```bash
./scripts/backup-db.sh
```

Backups written to `./backups/prodrive_<timestamp>.sql.gz`.

Schedule daily via cron:

```cron
0 2 * * * /opt/prodrive/scripts/backup-db.sh
```

Also back up the `uploads_data` Docker volume.

### Restore

```bash
./scripts/restore-db.sh ./backups/prodrive_YYYYMMDD_HHMMSS.sql.gz
```

Test restore on a staging instance before beta go-live.

## 7. Monitoring

* **Liveness:** `GET /api/v1/health`
* **Readiness:** `GET /api/v1/health/ready`
* **Logs:** JSON to stdout — ship to your log platform
* **Request tracing:** `X-Request-ID` response header

## 8. Upgrades

```bash
git pull
docker compose -f docker-compose.prod.yml build api
docker compose -f docker-compose.prod.yml up -d
```

Migrations run automatically via `docker-entrypoint.sh`.

## 9. Rollback

1. Stop API: `docker compose -f docker-compose.prod.yml stop api`
2. Restore database from last good backup
3. Deploy previous image tag
4. Verify smoke test

## 10. Security hardening

* Change all seed passwords after first login
* Restrict `/docs` to internal network
* Enable firewall — expose only 443 (and 22 for admin)
* Review `docs/BETA_CHECKLIST.md` before go-live
