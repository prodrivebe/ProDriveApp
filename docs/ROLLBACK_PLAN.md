# ProDrive Rollback Plan

Use this plan when a production deployment causes unacceptable errors and must be reverted.

## Rollback decision criteria

Rollback when any of the following persist after 15 minutes:

* Readiness probe fails (`GET /api/v1/health/ready` returns 503)
* Smoke test fails on critical paths (login, orders list, driver workflow)
* Data corruption or cross-tenant leak confirmed
* Error rate above 5% on authenticated API routes

Do **not** rollback for single-user issues — use support tools instead.

## Rollback levels

| Level | Scope | Downtime |
|-------|-------|----------|
| L1 — Application | Revert API/web containers | 2–5 min |
| L2 — Database | Restore DB from backup | 15–60 min |
| L3 — Full stack | L1 + L2 + uploads restore | 30–90 min |

## L1 — Application rollback

### 1. Enable maintenance mode

```env
MAINTENANCE_MODE=true
```

```bash
docker compose -f docker-compose.prod.yml up -d api
```

### 2. Deploy previous image

```bash
git checkout <previous-good-commit>
docker compose -f docker-compose.prod.yml build api web
docker compose -f docker-compose.prod.yml up -d
```

Or pin a known-good image tag if using a registry.

### 3. Verify

```bash
./scripts/pilot/smoke_test.sh
./scripts/pilot/readiness_check.sh
```

### 4. Disable maintenance mode

```env
MAINTENANCE_MODE=false
```

```bash
docker compose -f docker-compose.prod.yml up -d api
```

## L2 — Database rollback

**Warning:** Restores the entire database. All data created after the backup timestamp is lost.

### 1. Enable maintenance mode

### 2. Stop API

```bash
docker compose -f docker-compose.prod.yml stop api web
```

### 3. Restore database

```bash
./scripts/restore-db.sh ./backups/prodrive_YYYYMMDD_HHMMSS.sql.gz
```

### 4. Start stack and verify

```bash
docker compose -f docker-compose.prod.yml up -d
./scripts/pilot/smoke_test.sh
```

### 5. Disable maintenance mode

## L3 — Full stack rollback (database + uploads)

Required when file evidence (photos, CMR) must match database state.

### 1. Maintenance mode + stop services

```bash
docker compose -f docker-compose.prod.yml stop api web backup
```

### 2. Restore database (L2 step 3)

### 3. Restore uploads volume

```bash
docker compose -f docker-compose.prod.yml down
docker volume rm prodriveapp_uploads_data  # destructive — confirm backup exists
docker volume create prodriveapp_uploads_data
docker run --rm \
  -v prodriveapp_uploads_data:/uploads \
  -v "$(pwd)/backups:/backups:ro" \
  alpine sh -c "cd /uploads && tar -xzf /backups/uploads_YYYYMMDD_HHMMSS.tar.gz"
```

Adjust volume name to match `docker volume ls`.

### 4. Start stack, verify, disable maintenance

## Migration rollback

Alembic downgrade is **not** recommended in production unless tested on staging.

Preferred approach:

1. L1 application rollback to pre-migration code
2. L2 database restore to pre-migration backup

If downgrade is required:

```bash
docker compose -f docker-compose.prod.yml exec api alembic downgrade -1
```

Only after staging validation of the downgrade path.

## Post-rollback actions

- [ ] Notify pilot partner of data window lost (if L2/L3)
- [ ] Record incident timeline
- [ ] Identify root cause before re-deploying
- [ ] Update `docs/SPRINT_013_REPORT.md` issue register
- [ ] Re-run full `docs/BETA_TEST_PLAN.md` before next deploy attempt

## Backup verification schedule

Test L2 restore on staging **monthly** and before every production upgrade.

```bash
# Staging only
./scripts/restore-db.sh ./backups/latest.sql.gz
./scripts/pilot/smoke_test.sh
```

## Emergency contacts

Document on-call names and phone numbers before go-live. See `docs/PILOT_SUPPORT.md`.
