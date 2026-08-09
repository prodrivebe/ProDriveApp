# Sprint 4 Report — Order Management

**Date:** 2026-08-03  
**Branch:** main  
**Scope:** Complete Order Management domain (orders, order_stops, order_vehicles, order_timeline)

---

## Implemented Features

### Module structure

| Module | Responsibility |
|--------|----------------|
| `app/orders/` | Order header CRUD, workflow, wizard create, delegation |
| `app/order_stops/` | Stop CRUD, sequence validation, timeline + audit |
| `app/order_vehicles/` | Vehicle CRUD, stop link validation, timeline + audit |
| `app/order_timeline/` | Read-only listing and internal event recording |

Each module includes `models.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py`, `permissions.py`, and `tests/`.

### Order header

- Full CRUD with soft delete
- Company-scoped unique order numbers (`ORD-000001` pattern)
- Status workflow validation (DRAFT → READY → ASSIGNED → … → COMPLETED / CANCELLED)
- Multi-tenant isolation (cross-company access returns 404)

### Stops

- Unlimited stops per order
- PICKUP / DELIVERY types
- Unique `sequence` per order enforced on create and update
- Soft delete

### Vehicles

- Multiple vehicles per order
- Optional pickup/delivery stop references (must belong to same order and match types)
- No duplicated address data on vehicles
- Soft delete
- VIN scan/update endpoints retained on `/vehicles/{id}/scan-vin` and `/update-vin`

### Timeline (automatic, read-only)

Recorded events:

- `ORDER_CREATED`, `ORDER_UPDATED`
- `STATUS_CHANGED`
- `DRIVER_ASSIGNED`
- `STOP_ADDED`, `STOP_REMOVED`
- `VEHICLE_ADDED`, `VEHICLE_REMOVED`

Wizard create records stop/vehicle events in addition to order created.

### Audit

New audit actions:

- `ORDER_STATUS_CHANGED`
- `ORDER_STOP_ADDED`, `ORDER_STOP_UPDATED`, `ORDER_STOP_REMOVED`
- `ORDER_VEHICLE_ADDED`, `ORDER_VEHICLE_UPDATED`, `ORDER_VEHICLE_REMOVED`

---

## Database Changes

No new migrations required. Sprint 4 uses existing tables:

- `orders`
- `order_stops`
- `order_vehicles`
- `order_timeline`

See [DATABASE.md](./DATABASE.md) for field definitions and timeline event catalog.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/orders` | List orders |
| POST | `/api/v1/orders` | Create order (wizard payload supported) |
| GET | `/api/v1/orders/{id}` | Get order with stops and vehicles |
| PUT | `/api/v1/orders/{id}` | Update order header |
| DELETE | `/api/v1/orders/{id}` | Soft delete order |
| GET | `/api/v1/orders/{id}/stops` | List stops |
| POST | `/api/v1/orders/{id}/stops` | Add stop |
| PUT | `/api/v1/stops/{id}` | Update stop |
| DELETE | `/api/v1/stops/{id}` | Soft delete stop |
| GET | `/api/v1/orders/{id}/vehicles` | List vehicles |
| POST | `/api/v1/orders/{id}/vehicles` | Add vehicle |
| PUT | `/api/v1/vehicles/{id}` | Update vehicle |
| DELETE | `/api/v1/vehicles/{id}` | Soft delete vehicle |
| GET | `/api/v1/orders/{id}/timeline` | List timeline (read-only) |

Workflow endpoints (assign, accept, pickup, delivery, cancel) remain on `/orders/{id}/…`.

---

## Tests

Added `backend/tests/test_orders_sprint4.py` covering:

- Order CRUD (list, get, update, soft delete)
- Multi-stop orders and duplicate sequence rejection
- Multi-vehicle orders and invalid stop link rejection
- Timeline event generation
- Stop/vehicle audit logging
- Cross-company 404 isolation
- Driver permission denial on order create
- Invalid status transition rejection
- Completed order edit protection

Existing `backend/tests/test_orders.py` retained for wizard, assignment, VIN, and AI parse smoke tests.

**Verification note:** Python and Docker were unavailable in the CI agent environment on Windows. Run locally:

```bash
cd backend
pytest tests/test_orders.py tests/test_orders_sprint4.py --cov=app/orders --cov=app/order_stops --cov=app/order_vehicles --cov=app/order_timeline --cov-fail-under=90
ruff check app tests
mypy app
docker compose up --build
```

---

## Known Limitations

- Order number generation uses count + 1 (not a database sequence); concurrent creates could theoretically collide under heavy load.
- Generic PUT status updates are supported but workflow POST endpoints are preferred for driver actions.
- Stop/vehicle update timeline uses `ORDER_UPDATED` (not separate update event types) per Sprint 4 event catalog.
- AI, CMR, photo upload, and driver mobile workflow were intentionally out of scope.

---

## Recommendations for Sprint 5

1. **Driver mobile workflow** — Wire Flutter app to workflow endpoints with offline queue.
2. **CMR generation** — Trigger on loading complete; link timeline events.
3. **Photo uploads** — Associate inspection photos with stops/vehicles.
4. **Order number sequence** — Use per-company DB sequence or advisory lock for concurrency safety.
5. **Dispatcher UI** — Surface timeline and multi-stop route editor in order detail view.
6. **Integration tests** — Add Docker-based CI job running full pytest + coverage gate.

---

## Definition of Done Checklist

| Item | Status |
|------|--------|
| Migrations run | ✅ No new migrations |
| docker compose up | ⚠️ Verify locally |
| All tests pass | ⚠️ Verify locally |
| Lint / type check | ⚠️ Verify locally |
| API docs updated | ✅ |
| Timeline automatic | ✅ |
| Multi-stop / multi-vehicle | ✅ |
| Documentation updated | ✅ |
