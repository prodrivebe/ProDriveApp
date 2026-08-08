# 006 — Customers Module

**Status:** Implemented (Sprint 001)

## Feature Name

Customer management — contacts, search, order history.

## Business Goal

Dispatchers maintain customer records and view transport history without leaving the platform.

## Acceptance Criteria

- [x] Customer CRUD with contacts
- [x] Search/filter customers
- [x] `GET /customers/{id}/history` returns order summaries

## Database Changes

`004_customers_schema` — `customers`, `customer_contacts`

## API Endpoints

`/customers` CRUD, `/customers/{id}/contacts`, `/customers/{id}/history`

## Permissions

Admin + Dispatcher (`require_order_manager` / customer permissions)

## Tests Required

`tests/test_customers.py`

## Definition of Done

- [x] Implemented and tested
