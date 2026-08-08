# 013 — Dispatcher Dashboard

**Status:** Complete (Sprint 002)

## Feature Name

React dispatcher web application — operations center for transport companies.

## Business Goal

Allow dispatchers to create orders, assign drivers, monitor fleet, and resolve issues without spreadsheets or phone tag — per `docs/DISPATCHER.md`.

## User Stories

| ID | Role | Story | Priority |
|----|------|-------|----------|
| US-1 | As a **dispatcher**, I want to log in so that I can manage today's operations. | Must |
| US-2 | As a **dispatcher**, I want an operations board so that I see active orders at a glance. | Must |
| US-3 | As a **dispatcher**, I want to create orders with AI assist so that I enter data faster. | Must |
| US-4 | As a **dispatcher**, I want to assign drivers so that jobs go to the right person. | Must |
| US-5 | As a **dispatcher**, I want global search so that I find orders/VINs/customers quickly. | Must |
| US-6 | As a **dispatcher**, I want notifications so that I see driver actions. | Should |
| US-7 | As a **dispatcher**, I want a map view so that I see stops geographically. | Could (v2) |

## Acceptance Criteria

- [x] AC-1: Login with admin/dispatcher; drivers rejected.
- [x] AC-2: Dashboard shows KPI widgets from `/reports/kpi`.
- [x] AC-3: Orders list with status filter and detail page.
- [x] AC-4: Create order wizard (customer → details → review).
- [x] AC-5: Assign driver/truck/trailer on order detail.
- [x] AC-6: Global search in top bar.
- [x] AC-7: Customers, fleet, notifications, reports pages (read-only v1).
- [ ] AC-8: Customer create/edit UI.
- [ ] AC-9: Map view.
- [ ] AC-10: Production build in Docker / CI.
- [ ] AC-11: E2E or component tests.

## Database Changes

None — consumes existing API. Backend adds CORS for `localhost:5173`.

## API Endpoints (consumed)

| Screen | Endpoints |
|--------|-----------|
| Auth | `/auth/login`, `/auth/me`, `/auth/logout` |
| Dashboard | `/reports/kpi`, `/reports/orders`, `/notifications` |
| Orders | `/orders`, `/orders/{id}`, `/orders/{id}/timeline`, `/orders/{id}/assign-driver` |
| Create | `/customers`, `/ai/parse-order`, `/orders` POST |
| Fleet | `/fleet/overview`, `/drivers`, `/trucks`, `/trailers` |
| Search | `/search?q=` |

## Permissions

Dispatcher dashboard blocked for `DRIVER` role. All API calls use JWT; backend enforces tenant + role.

## Validation Rules

Client displays API error messages; no business validation duplicated in React.

## Edge Cases

| Scenario | Expected behaviour |
|----------|-------------------|
| Token expired | Redirect to login |
| API unreachable | User-friendly error, no stack traces |
| Empty lists | Empty states with guidance |

## Tests Required

| Layer | Status |
|-------|--------|
| Backend (existing) | 72 tests pass |
| Frontend unit | Not started |
| CI `npm run build` | Not in CI yet |

## Definition of Done

- [ ] All Must acceptance criteria checked
- [ ] `npm run build` passes
- [ ] README updated
- [ ] Spec status → Implemented
- [ ] Committed to Git

## Implementation location

`dispatcher-dashboard/` — Vite + React 19 + TypeScript + MUI 6

## Run locally

```bash
docker compose up -d          # backend
cd dispatcher-dashboard
npm install && npm run dev    # http://localhost:5173
```
