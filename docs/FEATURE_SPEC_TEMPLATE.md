# Feature Specification Template

Use this document before implementing any new ProDrive feature. Copy it to `docs/features/<feature-slug>.md`, fill in every section, and link it from `docs/TASKS.md` or the sprint plan.

Reference docs: [PROJECT.md](PROJECT.md), [API.md](API.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DECISIONS.md](DECISIONS.md), [TASKS.md](TASKS.md)

---

## Feature Name

**Short name:** _e.g. Driver Push Notifications_

**Slug:** _e.g. driver-push-notifications_

**Milestone / Sprint:** _e.g. Sprint 002 — Milestone 11_

**Owner:** _name or role_

**Status:** Proposed | In Progress | Done

---

## Business Goal

Describe the measurable outcome in one paragraph.

Answer:

- What problem does this solve?
- Who benefits (dispatcher, driver, admin, company)?
- How does it align with ProDrive goals (reduce dispatcher workload, reduce driver mistakes, reduce empty km, etc.)?

**Example:** Enable drivers to receive order assignments instantly on their device so dispatchers do not need to call drivers manually, reducing assignment delay and missed jobs.

---

## User Stories

Write stories in standard format. Include all affected roles.

| ID | Role | Story | Priority |
|----|------|-------|----------|
| US-1 | As a **driver**, I want … so that … | Must |
| US-2 | As a **dispatcher**, I want … so that … | Should |
| US-3 | As an **admin**, I want … so that … | Could |

**Example (US-1):** As a **driver**, I want to receive a push notification when an order is assigned to me so that I can accept it without checking the app constantly.

---

## Acceptance Criteria

Testable conditions. Use Given / When / Then where helpful.

- [ ] **AC-1:** Given … when … then …
- [ ] **AC-2:** …
- [ ] **AC-3:** Unauthorized users receive `403 FORBIDDEN`.
- [ ] **AC-4:** Invalid input returns `422` with structured error code.
- [ ] **AC-5:** Multi-tenant isolation: company A cannot access company B data.

**Non-functional (if applicable):**

- [ ] API response time under _X ms_ for typical load
- [ ] Works with existing Docker Compose setup
- [ ] No breaking changes to existing clients (or version bump documented)

---

## Database Changes

List every schema change. If none, state **None**.

| Change | Type | Details |
|--------|------|---------|
| _table_name_ | New table / Alter / Index | Columns, FKs, indexes, soft-delete |
| _…_ | Migration file | `009_<name>.py` |

**Conventions:**

- UUID primary keys
- `company_id` on all tenant-scoped tables
- `created_at`, `updated_at`; soft delete via `deleted_at` where applicable
- Alembic migration required for every change

**Example:**

| Change | Type | Details |
|--------|------|---------|
| `push_delivery_log` | New table | `id`, `company_id`, `device_token_id`, `status`, `sent_at`, `error` |
| Migration | `009_push_delivery_log.py` | Depends on `008_device_tokens_schema` |

---

## API Endpoints

Follow [API.md](API.md) conventions: REST, JSON, `{ success, data, meta }` wrapper, workflow verbs where appropriate.

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/v1/…` | ADMIN, DISPATCHER | … |
| POST | `/api/v1/…` | DRIVER | … |

**Request / response schemas:** Link to Pydantic schema names or include JSON examples.

**Side effects:** Notifications, audit events, timeline entries, file storage.

**Example:**

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| POST | `/notifications/register-device` | Any authenticated | Register FCM token |
| POST | `/internal/push/send` | System only | _Not exposed — background job_ |

---

## Permissions

Define who can do what. Use existing role helpers where possible (`require_order_manager`, `require_order_actor`, `require_driver`, etc.).

| Action | ADMIN | DISPATCHER | DRIVER |
|--------|-------|------------|--------|
| View | ✓ | ✓ | Assigned only |
| Create | ✓ | ✓ | ✗ |
| Update | ✓ | ✓ | ✗ |
| Delete | ✓ | ✗ | ✗ |
| Workflow action | ✓ | ✓ | Assigned driver only |

**Tenant rule:** All queries filtered by `current_user.company_id`.

**Example:** Drivers may only register device tokens for their own user account.

---

## Validation Rules

List input validation and business rules enforced in **service layer** (not only Pydantic).

| Field / Rule | Validation | Error code |
|--------------|------------|------------|
| _email_ | Valid email, unique per company | `INVALID_EMAIL` |
| _status transition_ | Must follow `WORKFLOW_TRANSITIONS` | `INVALID_ORDER_STATUS` |
| _file upload_ | Max size, MIME type | `FILE_TOO_LARGE` |

**Example:**

| Rule | Validation | Error code |
|------|------------|------------|
| Device token | 1–512 chars, non-empty | `INVALID_DEVICE_TOKEN` |
| Platform | `android` or `ios` | `INVALID_PLATFORM` |

---

## Edge Cases

Document non-happy-path behaviour explicitly.

| Scenario | Expected behaviour |
|----------|-------------------|
| Duplicate request | Idempotent or clear conflict error |
| Resource not found | `404` with `*_NOT_FOUND` code |
| Wrong company | `403 FORBIDDEN` |
| Soft-deleted entity | Treated as not found |
| Concurrent update | Last write wins / optimistic lock / reject |
| Offline client (driver app) | Queue action; sync on reconnect |
| Missing optional data | Sensible default or partial success |

**Example:** If driver rejects order after dispatcher reassigned another driver, return `409` or `422` with clear message.

---

## Tests Required

Minimum test coverage for ProDrive backend features.

| Test file | Cases |
|-----------|-------|
| `tests/test_<module>.py` | Happy path |
| | Authorization (403 for wrong role) |
| | Tenant isolation |
| | Validation errors (422) |
| | Not found (404) |
| | Edge cases listed above |

**Commands:**

```bash
docker run --rm -v ./backend:/app -w /app python:3.13-slim \
  bash -lc "pip install -q '.[dev]'; python -m pytest -q tests/test_<module>.py"
```

**Flutter / React (if applicable):** Widget or integration tests, or manual test plan linked here.

---

## Definition of Done

A feature is complete only when **all** items are checked:

- [ ] Feature spec approved (this document)
- [ ] Code implemented (routes → service → repository → models)
- [ ] Alembic migration applied and tested (`upgrade` / `downgrade`)
- [ ] All new tests pass; full suite green (`pytest -q`)
- [ ] No critical bugs / regressions
- [ ] API documented in [API.md](API.md) or OpenAPI reflects changes
- [ ] [TASKS.md](TASKS.md) checkboxes updated
- [ ] Significant decisions added to [DECISIONS.md](DECISIONS.md) (if architectural)
- [ ] Peer review completed
- [ ] Committed to Git with conventional commit message
- [ ] Docker Compose smoke test passes from clean clone (if backend-affecting)

---

## Blank Copy-Paste Template

```markdown
## Feature Name
**Short name:**
**Slug:**
**Milestone / Sprint:**
**Owner:**
**Status:** Proposed

## Business Goal


## User Stories
| ID | Role | Story | Priority |
|----|------|-------|----------|

## Acceptance Criteria
- [ ] AC-1:
- [ ] AC-2:

## Database Changes
| Change | Type | Details |
|--------|------|---------|

## API Endpoints
| Method | Path | Roles | Description |
|--------|------|-------|-------------|

## Permissions
| Action | ADMIN | DISPATCHER | DRIVER |
|--------|-------|------------|--------|

## Validation Rules
| Field / Rule | Validation | Error code |
|--------------|------------|------------|

## Edge Cases
| Scenario | Expected behaviour |
|----------|-------------------|

## Tests Required
| Test file | Cases |
|-----------|-------|

## Definition of Done
- [ ] …
```
