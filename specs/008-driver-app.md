# 008 — Driver App

**Status:** Partial

## Feature Name

Flutter Android driver application — offline-first mobile client.

## Business Goal

Drivers complete transport jobs with minimal taps; backend enforces all business rules.

## Acceptance Criteria

- [x] Login, home, orders list, order detail, workflow buttons
- [x] Backend `/drivers/me/*` endpoints
- [ ] VIN camera OCR
- [ ] Photo capture UI wired to API
- [ ] Full offline sync (queue stub only)
- [ ] FCM push notifications

## Database Changes

None (client + existing backend)

## API Endpoints

Uses auth, `/drivers/me/*`, `/orders/{id}/*` workflow, photos, CMR upload

## Permissions

Driver role only; assigned orders only

## Tests Required

Backend: `tests/test_driver_app.py`  
Flutter: widget/integration tests (TBD)

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Play Store internal test build

## Gaps

See `docs/DRIVER_APP.md` for full vision vs v0.1 scaffold in `driver_app/`.
