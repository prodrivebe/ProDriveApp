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
