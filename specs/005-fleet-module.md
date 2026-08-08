# 005 — Fleet Module

**Status:** Implemented (Sprint 001)

## Feature Name

Fleet management — drivers, trucks, trailers, capacities, fleet overview.

## Business Goal

Dispatchers maintain accurate fleet records and assign drivers, trucks, and trailers to transport orders.

## User Stories

| ID | Role | Story | Priority |
|----|------|-------|----------|
| US-1 | As a **dispatcher**, I want to manage drivers linked to user accounts. | Must |
| US-2 | As a **dispatcher**, I want trucks and trailers with registration numbers. | Must |
| US-3 | As a **dispatcher**, I want a fleet overview dashboard API. | Must |

## Acceptance Criteria

- [x] AC-1: CRUD drivers, trucks, trailers (soft delete, active flag).
- [x] AC-2: Driver profile linked 1:1 to user with role DRIVER.
- [x] AC-3: Fleet overview returns active/total counts.
- [x] AC-4: Unique registration per company.

## Database Changes

| Migration | Tables |
|-----------|--------|
| `003_fleet_schema` | `drivers`, `trucks`, `trailers` |

## API Endpoints

| Method | Path | Roles |
|--------|------|-------|
| CRUD | `/drivers`, `/trucks`, `/trailers` | Admin, Dispatcher |
| GET | `/fleet/overview` | Admin, Dispatcher |
| GET | `/drivers/me`, `/drivers/me/orders`, `/drivers/me/home` | Driver |

## Permissions

`require_fleet_manager` = Admin + Dispatcher. Driver endpoints use `require_driver`.

## Validation Rules

Driver must reference valid DRIVER user in same company; duplicate driver profile rejected.

## Edge Cases

Inactive truck/trailer cannot be assigned to orders.

## Tests Required

`tests/test_fleet.py`, `tests/test_driver_app.py`

## Definition of Done

- [x] Implemented and tested
