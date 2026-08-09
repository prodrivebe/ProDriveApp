# ProDrive Beta Checklist

Use this checklist before onboarding a transport company for beta testing.

## Infrastructure

- [ ] `APP_ENV=production` or `APP_ENV=beta` configured
- [ ] `JWT_SECRET_KEY` replaced with a strong random value (32+ chars)
- [ ] `DEBUG=false` in production
- [ ] PostgreSQL backups scheduled (`scripts/backup-db.sh`)
- [ ] Upload volume backed up or replicated
- [ ] Redis persistence enabled (`docker-compose.prod.yml`)
- [ ] HTTPS termination configured (reverse proxy)
- [ ] CORS origins restricted to beta dispatcher URL(s)

## Deployment verification

- [ ] `docker compose -f docker-compose.prod.yml up --build -d`
- [ ] `GET /api/v1/health` returns `healthy`
- [ ] `GET /api/v1/health/ready` returns `ready` with database and redis `ok`
- [ ] Alembic migrations applied (`alembic upgrade head`)
- [ ] Beta seed loaded if needed (`SEED_BETA=true` once)
- [ ] `scripts/beta/smoke_test.sh` passes

## Security

- [ ] Default admin password changed after first login
- [ ] Dispatcher and driver accounts use unique passwords
- [ ] Role-based access verified (driver cannot access dispatcher routes)
- [ ] Multi-tenant isolation verified (see `tests/test_multi_tenant_beta.py`)
- [ ] File upload size limits confirmed
- [ ] Audit logging enabled for auth and order mutations

## Functional readiness

- [ ] Login / refresh token flow works (dispatcher web + driver app)
- [ ] Order create → assign → driver accept workflow tested
- [ ] VIN verification, photos, damage, CMR upload tested
- [ ] AI order parse requires approval before order creation
- [ ] AI driver recommendation requires manual assign
- [ ] Planning board loads and assignment works
- [ ] Loading board optimization requires approval
- [ ] Real-time updates visible on Operations/Planning boards
- [ ] Notifications delivered in-app

## Monitoring

- [ ] JSON structured logging enabled (`LOG_JSON=true`)
- [ ] Log aggregation configured (CloudWatch, Loki, etc.)
- [ ] Health/readiness probes wired to orchestrator
- [ ] Error rate alerting configured
- [ ] Disk usage monitoring for uploads volume

## Documentation handed to beta partner

- [ ] `docs/BETA_TEST_PLAN.md`
- [ ] `docs/BETA_DEPLOYMENT.md`
- [ ] Dispatcher login URL and credentials process
- [ ] Driver app install instructions
- [ ] Support escalation contact

## Sign-off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Engineering | | | |
| Product | | | |
| Beta partner | | | |
