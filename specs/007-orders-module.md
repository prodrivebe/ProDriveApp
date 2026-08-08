# 007 — Orders Module

**Status:** Implemented (Sprint 001)

## Feature Name

Order wizard, stops, vehicles, VIN, driver assignment, workflow, timeline.

## Business Goal

End-to-end digital transport orders from creation through driver workflow to completion.

## Acceptance Criteria

- [x] Create order with stops and vehicles (wizard payload)
- [x] Assign driver/truck/trailer
- [x] Workflow actions: accept, reject, arrive, loading, transit, delivery, complete
- [x] VIN scan/update with audit + timeline
- [x] Status transitions enforced server-side
- [x] Timeline auto-generated

## Database Changes

`005_orders_schema` — `orders`, `order_stops`, `order_vehicles`, `order_timeline_entries`

## API Endpoints

See `docs/API.md` — `/orders/*`, `/vehicles/*`, `/stops/*`

## Permissions

- Managers: create/edit/list
- Actors (incl. driver): workflow + read assigned orders only

## Validation Rules

`WORKFLOW_TRANSITIONS`, VIN format, stop sequence uniqueness

## Edge Cases

Driver cannot view unassigned orders; terminal statuses block edits

## Tests Required

`tests/test_orders.py`, `tests/test_driver_app.py`

## Definition of Done

- [x] Implemented and tested
