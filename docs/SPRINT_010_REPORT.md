# Sprint 10 Report — AI-Assisted Dispatching and Order Intelligence

Date: 2026-08-09

## Summary

Sprint 10 introduces production AI-assisted dispatching with mandatory human approval. AI agents parse customer messages and recommend drivers, but never modify business data directly. Dispatchers review suggestions, edit extracted fields, and explicitly approve or reject before any order is created or decision is recorded.

## AI architecture

```text
Customer message / Order context
        │
        ▼
   AI Agent (heuristic v1)
        │
        ▼
  AISuggestion (PENDING)
        │
        ▼
 Dispatcher UI review
        │
   ┌────┴────┐
   ▼         ▼
Approve    Reject
   │         │
   ▼         ▼
OrderService  Audit log
(create)      (REJECTED)
```

Business services (`OrderService`, assignment APIs) remain deterministic. AI is isolated under `backend/app/ai/`.

## Implemented agents

| Agent | Module | Model version |
|-------|--------|---------------|
| Order Parser | `agents/order_parser.py` | `prodrive-heuristic-parser-1.0` |
| Driver Recommendation | `agents/driver_recommendation.py` | `prodrive-heuristic-driver-1.0` |

### Order Parser

Extracts: customer name, pickup/delivery stops, vehicles, VINs, planned dates, notes.

Returns per-field confidence (e.g. customer 0.98, pickup 0.94, VIN 0.61). Low-confidence fields are highlighted in the dispatcher UI.

### Driver Recommendation

Evaluates active drivers using availability, conflicting assignments, trailer compatibility, and distance stub. Returns recommended driver, alternatives, reasoning bullets, and confidence score.

Does **not** call `assign_driver`.

## Prompt strategy

Prompt templates live in `backend/app/ai/prompts/` (`order_parser.md`, `driver_recommendation.md`) and document expected JSON shapes for future LLM integration.

Production v1 executes deterministic heuristics with the same output schema, keeping behaviour predictable per ADR-007.

## Approval workflow

1. `POST /ai/parse-order` or `POST /ai/recommend-driver` creates a `PENDING` suggestion.
2. Dispatcher reviews output in the UI, optionally edits fields.
3. `POST /ai/suggestions/{id}/approve`:
   - **ORDER_PARSE**: requires `customer_id`; creates order via existing `OrderService.create_order`.
   - **DRIVER_RECOMMENDATION**: records approval only; dispatcher assigns manually.
4. `POST /ai/suggestions/{id}/reject` marks suggestion rejected and logs reason.

Statuses: `PENDING`, `APPROVED`, `REJECTED`, `EXPIRED` (enum ready; expiry job deferred).

## Audit model

`ai_audit_logs` records:

| Field | Purpose |
|-------|---------|
| `event_type` | REQUEST, RESPONSE, APPROVED, REJECTED |
| `prompt_version` / `model_version` | Traceability |
| `input_text` / `output_json` | Full AI interaction |
| `confidence` | Agent score |
| `dispatcher_decision` | APPROVED / REJECTED |
| `user_id`, `created_at` | Who and when |

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/ai/parse-order` | Create order parse suggestion |
| POST | `/ai/recommend-driver` | Create driver recommendation |
| GET | `/ai/suggestions` | List company suggestions |
| GET | `/ai/suggestions/{id}` | Get suggestion detail |
| POST | `/ai/suggestions/{id}/approve` | Approve (creates order for parse) |
| POST | `/ai/suggestions/{id}/reject` | Reject suggestion |

Legacy advisory endpoints (`/ai/suggest-route`, `/ai/suggest-loading`, `/ai/score-order`, `/ai/suggest-empty-km`) remain read-only.

## Dispatcher UI

* **Create order page** — `AiOrderPanel`: paste message, parse, confidence chips, editable fields, approve/reject.
* **Order detail page** — `AiDriverPanel`: get recommendation, view reasoning, accept/reject (pre-selects driver; manual Assign required).

## Test results

| Area | Tests |
|------|-------|
| Order parsing + confidence | `backend/app/ai/tests/test_order_parser.py` |
| Suggestion lifecycle | `backend/tests/test_ai_sprint10.py` |
| Parse endpoint contract | `backend/tests/test_orders.py` |
| Frontend types | `frontend/src/services/aiService.test.ts` |

Run:

```bash
cd backend && pytest tests/test_ai_sprint10.py app/ai/tests/ -q
cd frontend && npm test -- aiService
```

## Known limitations

* Heuristic parser — not a full NLP/LLM; complex multi-stop messages may need manual edits.
* Distance scoring uses stub values until GPS/routing integration.
* `EXPIRED` status defined but no scheduled expiry job yet.
* Driver recommendation approve does not assign driver (by design).
* External LLM providers not wired — heuristics only.

## Recommendations for Sprint 11

1. Add optional OpenAI/Anthropic provider behind feature flag with redacted inputs.
2. Implement suggestion expiry job (`PENDING` → `EXPIRED` after N hours).
3. Wire real distance/travel-time from routing service into driver agent.
4. Show AI suggestion history on order detail and dashboard.
5. Use approved/rejected suggestions as labeled examples for model fine-tuning.
6. FCM push when new AI suggestion awaits review (if dispatchers opt in).

## Definition of Done

- [x] Order parsing works
- [x] Driver recommendations work
- [x] Confidence scores returned
- [x] Suggestions require approval
- [x] Approved order suggestions create real orders
- [x] Rejected suggestions tracked
- [x] AI audit logging works
- [x] Tests implemented
- [x] Documentation updated
