# Sprint 5 Report — Driver Workflow

**Date:** 2026-08-09  
**Scope:** Backend driver operational workflow (no Flutter UI)

---

## Implemented Workflow

### State machine

```
ASSIGNED
  → ACCEPTED            (POST /accept)
  → READY               (POST /reject, clears assignment)

ACCEPTED
  → ARRIVED_PICKUP      (POST /arrive-pickup)

ARRIVED_PICKUP
  → LOADING             (POST /start-loading)

LOADING
  → LOADED              (POST /complete-loading, all pickups done)
  → ACCEPTED            (POST /complete-loading, more pickups remain)

LOADED
  → IN_TRANSIT          (POST /start-transit)

IN_TRANSIT
  → ARRIVED_DELIVERY    (POST /arrive-delivery)

ARRIVED_DELIVERY
  → DELIVERING          (POST /start-delivery)

DELIVERING
  → COMPLETED           (POST /complete-delivery, all deliveries done)
  → IN_TRANSIT          (POST /complete-delivery, more deliveries remain)

Any non-terminal status → CANCELLED (POST /cancel, managers only)
```

### Stop progress

Each stop tracks `progress_status`:

| Status | Meaning |
|--------|---------|
| PENDING | Not yet visited |
| ARRIVED | Driver arrived (`arrival_time` set) |
| LOADING | Loading or unloading in progress |
| COMPLETED | Stop finished (`departure_time` set) |

Multi-stop orders repeat pickup or delivery cycles until all stops of that type are completed.

---

## Module Structure

| Module | Role |
|--------|------|
| `app/workflow/` | State machine, stop progress, timeline, audit, notifications |
| `app/orders/routes.py` | Workflow HTTP endpoints (delegate to workflow service) |
| `app/drivers/routes.py` | `GET /drivers/me/current-order` |

---

## API Endpoints

| Method | Path | Actor |
|--------|------|-------|
| POST | `/api/v1/orders/{id}/accept` | Assigned driver or manager |
| POST | `/api/v1/orders/{id}/reject` | Assigned driver or manager |
| POST | `/api/v1/orders/{id}/arrive-pickup` | Assigned driver or manager |
| POST | `/api/v1/orders/{id}/start-loading` | Assigned driver or manager |
| POST | `/api/v1/orders/{id}/complete-loading` | Assigned driver or manager |
| POST | `/api/v1/orders/{id}/start-transit` | Assigned driver or manager |
| POST | `/api/v1/orders/{id}/arrive-delivery` | Assigned driver or manager |
| POST | `/api/v1/orders/{id}/start-delivery` | Assigned driver or manager |
| POST | `/api/v1/orders/{id}/complete-delivery` | Assigned driver or manager |
| POST | `/api/v1/orders/{id}/cancel` | Manager only |
| GET | `/api/v1/drivers/me/current-order` | Driver |

---

## Transition Rules

- Invalid order transitions → `422 INVALID_ORDER_STATUS`
- Invalid stop progress → `422 INVALID_STOP_PROGRESS`
- Wrong stop type for action → `422 INVALID_STOP_TYPE`
- Non-assigned driver → `403 FORBIDDEN`
- Cross-company access → `404 ORDER_NOT_FOUND`
- Completed/cancelled orders → `422 ORDER_NOT_EDITABLE`

Admins and dispatchers may override workflow actions on behalf of drivers.

---

## Timeline & Audit

Each workflow action records:

- A specific event (`DRIVER_ACCEPTED`, `ARRIVED_PICKUP`, `LOADING_STARTED`, etc.)
- A `STATUS_CHANGED` entry when the order status changes
- An audit log with `old_value`, `new_value`, action, user, and timestamp

---

## Notifications (in-app only)

| Event | Type |
|-------|------|
| Order accepted | `ORDER_ACCEPTED` |
| Order rejected | `ORDER_REJECTED` |
| Pickup arrived | `PICKUP_ARRIVED` |
| Loading completed | `LOADING_COMPLETED` |
| Delivery arrived | `DELIVERY_ARRIVED` |
| Order completed | `ORDER_COMPLETED` |

Push delivery is deferred.

---

## Database Changes

Migration `010_stop_progress_schema`:

- Added `order_stops.progress_status` (default `PENDING`)

New order statuses: `ARRIVED_PICKUP`, `LOADED`, `ARRIVED_DELIVERY`

---

## Tests

- `backend/tests/test_workflow_sprint5.py` — integration tests (12 cases)
- `backend/app/workflow/tests/test_validators.py` — unit tests
- Updated `test_driver_app.py` and `test_orders_sprint4.py` for new workflow steps

Run locally:

```bash
cd backend
pytest tests/test_workflow_sprint5.py app/workflow/tests --cov=app/workflow --cov-fail-under=90
ruff check app tests
mypy app
docker compose up --build
alembic upgrade head
```

---

## Known Limitations

- No Flutter UI yet — API only
- No push notifications (records created only)
- No photo uploads or VIN scanning in this sprint
- No CMR generation
- Reject reason not captured (future enhancement)
- Generic PUT status updates still exist but workflow POST endpoints are preferred

---

## Recommendations for Sprint 6

1. **Flutter driver app** — Wire home screen to `/drivers/me/current-order` and workflow buttons
2. **Photo capture** — Required photos before complete-loading / complete-delivery
3. **VIN verification** — Scan/confirm flow at pickup
4. **CMR generation** — Trigger after loading complete
5. **Push notifications** — Deliver workflow events via FCM
6. **Reject reason** — Capture and notify dispatchers with context

---

## Definition of Done

| Item | Status |
|------|--------|
| State machine implemented | ✅ |
| Transition rules enforced | ✅ |
| Driver restrictions | ✅ |
| Timeline automatic | ✅ |
| Notification records | ✅ |
| Tests | ✅ (verify locally) |
| Documentation | ✅ |
