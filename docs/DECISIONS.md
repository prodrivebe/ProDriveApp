# DECISIONS.md

# ProDrive Architecture Decisions

Version 1.0

---

# Purpose

This document records important architectural and product decisions made during the development of ProDrive.

Its goals are:

* Preserve architectural reasoning.
* Avoid repeating discussions.
* Help new developers understand why decisions were made.
* Provide historical context.
* Keep AI coding assistants aligned with previous decisions.

Every significant decision should be recorded here.

---

# Decision Format

Every decision follows this structure.

---

## Decision ID

Unique identifier.

Example

ADR-001

---

## Date

Date decision was accepted.

---

## Status

Possible values

Accepted

Proposed

Deprecated

Superseded

Rejected

---

## Decision

Short description.

---

## Context

What problem were we solving?

---

## Alternatives Considered

List alternative approaches.

Explain advantages and disadvantages.

---

## Decision

Explain the chosen solution.

---

## Consequences

Positive consequences.

Negative consequences.

Future implications.

---

# ADR-001

## Title

FastAPI chosen as backend framework.

Status

Accepted

---

### Context

The backend must:

* Support REST APIs.
* Be fast.
* Be easy to test.
* Work well with AI-generated code.
* Scale to commercial SaaS.

---

### Alternatives

Django

Pros

* Mature
* Batteries included

Cons

* Heavy
* More opinionated
* Larger learning curve
* More difficult to maintain modular architecture

Node.js

Pros

* Huge ecosystem

Cons

* We prefer Python because future AI features will also be implemented in Python.

---

### Decision

Use FastAPI.

---

### Reasoning

FastAPI provides:

* Excellent performance
* Automatic OpenAPI documentation
* Modern Python typing
* Great developer experience
* Excellent testing support
* Perfect integration with Pydantic

---

### Consequences

Backend remains lightweight.

Easy future AI integration.

Simple REST development.

---

# ADR-002

## Title

Flutter selected for Driver App.

Status

Accepted

---

### Context

Drivers need:

Fast

Reliable

Offline-first

Simple UI

---

### Alternatives

React Native

Native Android

---

### Decision

Flutter.

---

### Reasoning

Excellent performance.

Single codebase.

Strong offline support.

Excellent UI consistency.

---

### Consequences

Future iOS support becomes easier.

Development speed increases.

---

# ADR-003

## Title

React selected for Dispatcher Dashboard.

Status

Accepted

---

### Decision

React + TypeScript + Material UI.

---

### Reasoning

Large ecosystem.

Easy hiring.

Strong component model.

Excellent enterprise support.

---

# ADR-004

## Title

PostgreSQL selected as primary database.

Status

Accepted

---

### Alternatives

MySQL

SQL Server

MongoDB

---

### Decision

PostgreSQL.

---

### Reasoning

Excellent reliability.

Powerful indexing.

JSON support.

Extensions.

Strong SQL compliance.

Ideal for SaaS.

---

# ADR-005

## Title

Architecture Style

Status

Accepted

---

### Decision

Modular Monolith.

---

### Context

Microservices introduce unnecessary complexity during early development.

---

### Reasoning

One deployment.

Simple debugging.

Clear module boundaries.

Future extraction possible.

---

### Consequences

Lower operational complexity.

Better developer productivity.

Easy scaling later.

---

# ADR-006

## Title

Business Logic Location

Status

Accepted

---

### Decision

Business logic exists only inside the backend.

---

### Reasoning

Flutter.

React.

AI.

All become thin clients.

Single source of truth.

---

### Consequences

No duplicated logic.

Lower bug risk.

Consistent behaviour.

---

# ADR-007

## Title

AI Decision Policy

Status

Accepted

---

### Decision

AI never makes business decisions.

---

### AI may

Suggest.

Recommend.

Explain.

Summarize.

---

### AI may not

Assign drivers.

Modify orders.

Delete records.

Complete workflows.

Communicate with customers.

---

### Reasoning

Transport companies require trust and accountability.

Operational responsibility remains with humans.

---

# ADR-008

## Title

Offline First Driver Application

Status

Accepted

---

### Decision

Driver App functions without internet.

---

### Reasoning

Transport frequently occurs in areas with poor connectivity.

Drivers must never be blocked by network availability.

---

### Consequences

Local queue.

Automatic synchronization.

Conflict resolution handled by backend.

---

# ADR-009

## Title

Soft Delete Strategy

Status

Accepted

---

### Decision

Business entities are never permanently deleted.

---

### Reasoning

Transport operations require historical traceability.

Customers may request records months or years later.

Audit requirements.

---

# ADR-010

## Title

Workflow-Based API

Status

Accepted

---

### Decision

REST endpoints represent business actions.

Examples

Accept Order

Complete Loading

Upload CMR

Instead of

Update Status

---

### Reasoning

Business language is easier to understand.

Lower risk of invalid state transitions.

Cleaner permissions.

---

# ADR-011

## Title

AI Vehicle Knowledge Base

Status

Accepted

---

### Decision

Maintain an internal catalogue of vehicle specifications instead of querying external services at runtime.

---

### Purpose

Store:

Make

Model

Generation

Weight

Height

Width

Length

Wheelbase

Future:

VIN decoding

---

### Benefits

Supports:

Loading optimization.

Height calculation.

Weight balancing.

Future AI features.

Lower API costs.

---

# ADR-012

## Title

Focus Mode for Drivers

Status

Accepted

---

### Decision

During active transport, the Driver App hides unnecessary navigation and settings.

---

### Purpose

Reduce distraction.

Reduce mistakes.

Guide drivers through one clear workflow.

---

# ADR-013

## Title

Operations Board as Dispatcher Home

Status

Accepted

---

### Decision

The dashboard opens to an Operations Board instead of a simple orders table.

---

### Displays

Orders requiring attention.

Available drivers.

Delayed transports.

AI recommendations.

Operational alerts.

---

### Reasoning

Dispatchers think in operations, not database records.

This provides better situational awareness.

---

# Future Decisions

This document evolves with the project.

Every significant technical or product decision should be recorded before implementation.

No architectural change should be introduced without updating this file.

---

# Final Principle

A good architecture is not the result of perfect decisions.

It is the result of recording decisions, learning from them, and improving them over time.
