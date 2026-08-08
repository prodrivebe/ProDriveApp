# 011 — Notifications Module

**Status:** Partial

## Feature Name

In-app notifications and device token registration.

## Business Goal

Alert dispatchers and drivers about assignments, completions, and operational events.

## Acceptance Criteria

- [x] In-app notifications list, mark read, mark all read
- [x] Auto-notify on order assign and complete
- [x] Device token registration endpoint
- [ ] FCM/APNs push delivery
- [ ] Dispatcher notification center UI (see spec 013)

## Database Changes

`007_notifications_schema`, `008_device_tokens_schema`

## API Endpoints

`/notifications`, `/notifications/register-device`

## Tests Required

`tests/test_notifications.py`

## Definition of Done

- [x] In-app backend complete
- [ ] Push delivery spec TBD
