# ProDrive Pilot Onboarding

Use this guide when onboarding a real transport company for a controlled pilot.

## Overview

Pilot onboarding prepares one company tenant with fleet data, users, and operational validation — without demo orders unless requested.

Estimated timeline: **2–3 business days**.

## Phase 1 — Infrastructure (Day 0)

Complete `docs/PRODUCTION_DEPLOYMENT.md` through smoke test pass.

Checklist:

- [ ] Production `.env` configured with unique secrets
- [ ] HTTPS active on dispatcher domain
- [ ] `GET /api/v1/health/ready` returns `ready`
- [ ] Automated backups scheduled (DB + uploads)
- [ ] Monitoring or scheduled readiness checks configured
- [ ] Rollback plan reviewed (`docs/ROLLBACK_PLAN.md`)

## Phase 2 — Company shell (Day 1)

### Option A: Empty pilot tenant (recommended)

```bash
SEED_PILOT=true docker compose -f docker-compose.prod.yml up -d api
```

Creates:

* One company record
* One admin user (`SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD`)
* Default company settings

Set `SEED_PILOT=false` immediately after first successful start.

### Option B: Demo dataset for training

Use `SEED_BETA=true` once if the partner wants pre-loaded orders for training. Switch to `false` after seed completes.

## Phase 3 — Data import (Day 1)

Prepare CSV files from customer spreadsheets using templates in `scripts/pilot/templates/`.

Import order:

1. Customers
2. Trucks and trailers
3. Drivers (creates user accounts)

```bash
./scripts/pilot/import-data.sh customers ./data/customers.csv
./scripts/pilot/import-data.sh trucks ./data/trucks.csv
./scripts/pilot/import-data.sh trailers ./data/trailers.csv
./scripts/pilot/import-data.sh drivers ./data/drivers.csv --default-password 'TempPilot123!'
```

After import:

- [ ] Verify fleet in dispatcher UI (`/fleet`, `/drivers`)
- [ ] Verify customers in dispatcher UI (`/customers`)
- [ ] Force password change for all imported driver accounts

## Phase 4 — User provisioning (Day 1)

| Role | Count (typical pilot) | Created via |
|------|----------------------|-------------|
| Admin | 1 | Pilot seed |
| Dispatcher | 1–3 | Admin → Users UI or support CLI |
| Driver | 1–5 | CSV import |

Support CLI:

```bash
./scripts/pilot/support-tools.sh list-users
./scripts/pilot/support-tools.sh reset-password dispatcher@company.com 'NewSecurePass1!'
```

## Phase 5 — Company settings (Day 1)

Configure via API (`PUT /api/v1/companies/settings`) or future settings UI:

* Timezone
* Default currency
* Branding (logo upload via `POST /api/v1/companies/me/logo`)
* Vehicle photo requirements

Current dispatcher settings page is read-only; use API or direct DB update for pilot.

## Phase 6 — Driver app rollout (Day 2)

1. Build APK with production API URL
2. Install on pilot driver devices
3. Confirm login, current order view, offline queue
4. Run one supervised transport end-to-end

## Phase 7 — Validation (Day 2–3)

Execute scenarios from `docs/BETA_TEST_PLAN.md` with the pilot partner:

- [ ] Login and role isolation
- [ ] Order create → assign → driver accept
- [ ] VIN verification, photos, damage, CMR
- [ ] AI suggestions require approval
- [ ] Planning board assignment
- [ ] Real-time board updates

Record sign-off in the checklist below.

## Phase 8 — Handover

Deliver to the pilot partner:

| Item | Location |
|------|----------|
| Dispatcher URL | Production domain |
| Support contact | `docs/PILOT_SUPPORT.md` |
| Known limitations | `docs/SPRINT_013_REPORT.md` |
| Escalation path | Engineering on-call |

## Onboarding wizard (manual checklist)

ProDrive does not include an in-app onboarding wizard in the pilot release. Follow this document as the wizard substitute.

| Step | Action | Owner |
|------|--------|-------|
| 1 | Deploy production stack | Engineering |
| 2 | Create company shell | Engineering |
| 3 | Import master data | Engineering + Customer |
| 4 | Create dispatcher accounts | Customer admin |
| 5 | Install driver app | Customer + Engineering |
| 6 | Run test plan | Customer + Engineering |
| 7 | Go-live sign-off | All parties |

## Sign-off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Engineering | | | |
| Product | | | |
| Pilot partner | | | |
