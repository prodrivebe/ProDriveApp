# 012 — Reports Module

**Status:** Implemented (Sprint 001)

## Feature Name

Operational reports and KPI dashboard API.

## Business Goal

Give dispatchers and admins visibility into orders, fleet, drivers, and customers.

## Acceptance Criteria

- [x] Reports: orders, drivers, customers, fleet
- [x] KPI dashboard aggregate endpoint

## API Endpoints

`/reports/orders`, `/drivers`, `/customers`, `/fleet`, `/kpi`

## Permissions

Admin + Dispatcher (`require_report_reader`)

## Tests Required

`tests/test_reports.py`

## Definition of Done

- [x] Implemented and tested
- [ ] Rich charts UI in dispatcher (spec 013)
