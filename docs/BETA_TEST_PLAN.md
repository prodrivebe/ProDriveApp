# ProDrive Beta Test Plan

Version: Beta 1.0  
Audience: Transport company dispatchers, drivers, and ProDrive engineering

## Goals

Validate ProDrive in real transport operations without autonomous AI or automatic dispatching. Confirm reliability, usability, and data isolation before wider rollout.

## Test environment

| Component | URL / access |
|-----------|--------------|
| API | `https://<beta-host>/api/v1` |
| Dispatcher web | `https://<beta-host>/` |
| Driver app | Android APK / Play internal track |
| Swagger (internal) | `/docs` (restrict by network) |

Default beta seed accounts (change passwords immediately):

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@example.com` | From `SEED_ADMIN_PASSWORD` |
| Dispatcher | `dispatcher@beta.local` | `Dispatch123!` |
| Driver 1 | `driver1@beta.local` | `Driver123!` |
| Driver 2 | `driver2@beta.local` | `Driver123!` |

## Test scenarios

### 1. Authentication and roles

1. Log in as dispatcher — dashboard loads
2. Log in as driver — home screen loads, dispatcher routes blocked
3. Refresh token after 15 minutes — session continues
4. Log out — tokens cleared

**Pass criteria:** No unauthorized access; standard error envelope on 401.

### 2. Order lifecycle (dispatcher)

1. Create customer (or use seed customer)
2. Create order manually with pickup + delivery + vehicles
3. Assign driver, truck, trailer
4. Verify order appears on Planning board (Assigned column)
5. Use AI order assistant — parse message, edit fields, approve → order created
6. Reject an AI suggestion — status tracked

**Pass criteria:** Orders created only after explicit approval; timeline entries recorded.

### 3. Driver workflow

1. Driver accepts assigned order
2. Complete workflow: arrive pickup → load → transit → deliver → complete
3. Verify VIN entry, photo upload, damage report, CMR upload
4. Complete order when checklist satisfied

**Pass criteria:** Status transitions enforced; evidence stored; timeline updated.

### 4. Planning and loading

1. Open Planning board — filter by date/driver
2. Drag order to assign column (with driver selected) or assign via order detail
3. Open Loading board for assigned order
4. Generate loading optimization — review reasoning
5. Approve optimization — plan persisted
6. Validate plan — resolve any warnings
7. Confirm plan manually

**Pass criteria:** No automatic assignment; loading plan requires approval.

### 5. Real-time operations

1. Open dispatcher dashboard and planning board in two browsers
2. Assign order in one — other updates within seconds
3. Driver completes workflow step — boards refresh

**Pass criteria:** WebSocket reconnect works; no stale data after reconnect.

### 6. Multi-tenant isolation (engineering)

Run automated suite:

```bash
cd backend
pytest tests/test_multi_tenant_beta.py -q
```

**Pass criteria:** Cross-company access returns 404.

### 7. Regression smoke

```bash
./scripts/beta/smoke_test.sh
cd backend && pytest tests/test_e2e_beta.py tests/test_security_beta.py -q
```

## Defect reporting

Include:

* Steps to reproduce
* User role and account
* Order ID / screenshot
* Timestamp and browser/app version
* Expected vs actual behaviour

Severity guide:

| Severity | Example |
|----------|---------|
| Critical | Data leak across companies; order lost |
| High | Cannot assign driver; workflow blocked |
| Medium | UI glitch with workaround |
| Low | Cosmetic issue |

## Exit criteria for beta

* All Critical and High defects resolved or accepted with mitigation
* Core scenarios 1–5 passed by beta partner
* Backup/restore tested once
* 5 consecutive days stable operation
