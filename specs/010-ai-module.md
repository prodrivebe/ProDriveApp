# 010 — AI Module

**Status:** Partial (stubs)

## Feature Name

AI-assisted parsing and recommendations — advisory only.

## Business Goal

Speed up order creation and dispatch decisions without AI making business decisions (ADR-007).

## Acceptance Criteria

- [x] Parse customer message → draft order structure
- [x] Suggest driver, route, loading, order quality score, empty km
- [ ] Real LLM integration with human confirmation UI
- [ ] `ai_suggestions` persistence table

## API Endpoints

`/ai/parse-order`, `/ai/suggest-*`, `/ai/score-order`, `/ai/suggest-empty-km`

## Permissions

Admin + Dispatcher only

## Validation Rules

AI endpoints never mutate orders directly

## Tests Required

Covered in `tests/test_orders.py` (parse), manual for others

## Definition of Done

- [x] v1 stubs shipped
- [ ] LLM integration spec required before v2
