# AI.md

# ProDrive AI Architecture

Version 1.0

---

# 1. Purpose

Artificial Intelligence exists to assist dispatchers.

Its job is to reduce repetitive work while ensuring humans remain in control of operational decisions.

The AI never replaces dispatchers.

It makes them faster.

---

# 2. Fundamental Principle

AI suggests.

Humans decide.

No exception.

No automatic business decisions.

---

# 3. AI Architecture

Instead of one large AI model, ProDrive uses multiple specialized AI agents.

```text
Customer Message
        │
        ▼
 Order Parser Agent
        │
        ▼
 Structured Order
        │
 ┌──────┼─────────┐
 ▼      ▼         ▼
Driver  Route   Loading
Agent   Agent    Agent
 │       │         │
 └───────┴─────────┘
         │
         ▼
 Dispatcher Review
         │
         ▼
 Approved Changes
```

Each agent performs exactly one job.

---

# 4. AI Rules

AI may:

Read emails.

Read copied messages.

Extract VINs.

Extract addresses.

Extract customer names.

Suggest routes.

Suggest drivers.

Suggest trailer loading.

Detect conflicts.

Detect missing information.

Predict delays.

AI may NOT:

Assign drivers.

Delete records.

Change customers.

Modify completed orders.

Complete workflows.

Send customer emails.

Change VINs automatically.

Nothing reaches production without dispatcher approval.

---

# 5. Order Parser Agent

Purpose

Convert unstructured customer requests into structured transport orders.

Example Input

```text
Pick up:

BMW X5

Mercedes GLC

Amsterdam

Deliver:

Brussels
```

Output

Structured JSON

Pickup Stops

Delivery Stops

Vehicles

VINs

Missing Fields

Confidence Score

Dispatcher reviews before creating the order.

---

# 6. Driver Recommendation Agent

Purpose

Suggest the most appropriate driver.

Evaluation criteria

Distance to pickup

Current workload

Working hours

Trailer compatibility

Vehicle capacity

Previous assignments

Customer requirements

Output

Recommended Driver

Alternative Drivers

Reasoning

Dispatcher confirms.

---

# 7. Route Agent

Purpose

Determine the most efficient order of stops.

Considers

Pickup sequence

Delivery sequence

Distance

Road restrictions

Estimated travel time

Driver schedule

Future

Traffic

Weather

Low emission zones

---

# 8. Loading Agent

Purpose

Suggest trailer loading positions.

Inputs

Vehicle dimensions

Vehicle weight

Pickup order

Delivery order

Trailer configuration

Legal transport height

Outputs

Loading diagram

Loading order

Unloading order

Estimated transport height

Risk warnings

Dispatcher confirms.

Driver may override.

---

# 9. VIN Agent

Purpose

Validate VINs.

Responsibilities

Format validation

Duplicate detection

Manufacturer lookup

Model lookup

Future

Automatic VIN decoding

VIN history

VIN confidence score

---

# 10. Photo Quality Agent (Future)

Purpose

Review uploaded photos.

Detect

Blur

Darkness

Duplicates

Missing angles

Unreadable documents

Driver receives suggestions only.

---

# 11. Delay Prediction Agent (Future)

Purpose

Predict transport delays.

Inputs

Driver location

Distance

Historical travel times

Traffic

Loading duration

Outputs

Delay probability

Estimated arrival

Dispatcher notification

---

# 12. Document Agent

Purpose

Generate documents.

Supports

CMR

Delivery Reports

Vehicle Lists

Future

Invoices

Certificates

Custom templates

Generated documents always remain editable before finalization.

---

# 13. Knowledge Base

AI maintains an internal knowledge base.

Includes

Vehicle dimensions

Vehicle weights

Trailer specifications

Country regulations

Customer preferences

Company rules

Knowledge is versioned and updateable.

---

# 14. Confidence Scores

Every AI output includes a confidence score.

Example

98%

VIN detected

94%

Pickup Address

61%

Delivery Date

Low confidence items require additional review.

---

# 15. Human Approval Workflow

Every AI suggestion follows the same lifecycle.

```text
Generated

↓

Displayed

↓

Reviewed

↓

Approved / Rejected

↓

Applied
```

AI never skips the approval stage.

---

# 16. Learning

AI does not automatically retrain itself.

Instead:

Approved suggestions become examples.

Rejected suggestions become improvement signals.

Future model improvements use these examples.

Production behaviour remains predictable.

---

# 17. Explainability

Every recommendation should answer:

Why?

Example

Recommended Driver:

John Smith

Reason:

12 km from pickup

Trailer compatible

Currently available

No conflicting assignments

Dispatchers should understand recommendations without guessing.

---

# 18. AI Safety

Never fabricate information.

Never guess VINs.

Never invent addresses.

When uncertain:

Return

"I don't know."

Asking for clarification is better than inventing data.

---

# 19. Security

Customer information must never be exposed outside approved AI providers.

Sensitive data should be minimized before sending to external services where possible.

Every AI interaction is logged.

---

# 20. Cost Awareness

AI should be efficient.

Simple deterministic code should be preferred over AI when it solves the problem reliably.

Examples

VIN validation

Address formatting

Duplicate detection

These should not require an LLM.

Reserve LLM usage for language understanding and reasoning.

---

# 21. AI Audit

Every suggestion stores

Input

Output

Model Version

Prompt Version

Confidence

Dispatcher Decision

Timestamp

This allows future debugging and improvement.

---

# 22. AI Failure Handling

If AI is unavailable

The application continues functioning normally.

AI is an enhancement.

Never a dependency.

Business operations must continue without AI.

---

# 23. Future AI Modules

OCR

Damage Detection

Customer Communication Drafting

Invoice Extraction

Maintenance Prediction

Fuel Optimization

Driver Coaching

Operations Forecasting

Business Analytics

Voice Assistant

---

# 24. Final Principle

The best AI is the one that quietly saves time without taking control.

Dispatchers should feel more confident because of AI, never less.

Trust is more valuable than automation.

---

# 25. Sprint 10 Implementation (Production v1)

Sprint 10 delivers the first production AI-assisted dispatching workflow with mandatory human approval.

## Module layout

```text
backend/app/ai/
  agents/
    order_parser.py
    driver_recommendation.py
  services/
    ai_service.py          # advisory helpers (route, loading, score, empty-km)
    suggestion_service.py  # suggestion lifecycle + approval
  prompts/
    order_parser.md
    driver_recommendation.md
  models/
    ai_suggestion.py       # AISuggestion + AIAuditLog
  routes/
    ai_routes.py
  tests/
```

## Agents

| Agent | Input | Output | Mutates data? |
|-------|-------|--------|---------------|
| Order Parser | Email / WhatsApp / pasted text | Structured JSON + per-field confidence | No — creates `PENDING` suggestion |
| Driver Recommendation | Order + fleet context | Recommended driver, alternatives, reasons | No — creates `PENDING` suggestion |

Production v1 uses deterministic heuristics (`prodrive-heuristic-parser-1.0`, `prodrive-heuristic-driver-1.0`) aligned with ADR-007. External LLM integration is deferred.

## Approval workflow

```text
Input text
    ↓
AI suggestion (PENDING)
    ↓
Dispatcher review + optional edits
    ↓
Approve / Reject
    ↓
ORDER_PARSE approve → OrderService.create_order
DRIVER_RECOMMENDATION approve → audit only
```

## Audit model

`ai_audit_logs` stores:

* `event_type`: REQUEST, RESPONSE, APPROVED, REJECTED
* prompt and model version
* input/output JSON
* confidence
* dispatcher decision
* timestamp

## Dispatcher UI

* **Create order page** — AI panel to paste messages, review confidence, edit fields, approve/reject
* **Order detail page** — AI driver recommendation panel with reasoning; manual Assign still required

## Security

* Company-scoped suggestions and audit logs
* Minimal data sent to agents (message text or order ID only)
* All requests, responses, and decisions logged
