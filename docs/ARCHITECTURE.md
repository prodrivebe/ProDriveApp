# ARCHITECTURE.md

# ProDrive Technical Architecture

Version 1.0

---

# 1. Purpose

This document defines the architecture used throughout the ProDrive platform.

Every module, service and feature must follow these principles.

Architecture decisions should prioritize:

* Maintainability
* Scalability
* Reliability
* Readability
* Testability

Never optimize for writing fewer lines of code.

Always optimize for long-term maintainability.

---

# 2. System Overview

ProDrive consists of four independent applications.

```text
                   Internet
                        │
                        ▼
              Reverse Proxy (Nginx)
                        │
                        ▼
                FastAPI Backend API
                        │
       ┌────────────────┼────────────────┐
       │                │                │
       ▼                ▼                ▼
 PostgreSQL         Redis Cache      File Storage
       │
       ▼
 Business Data
```

Connected Clients

```text
Dispatcher Dashboard (React)

↓

FastAPI

↓

Database

-----------------------

Driver App (Flutter)

↓

FastAPI

↓

Database

-----------------------

Future Customer Portal

↓

FastAPI
```

All clients communicate only through the backend.

No client communicates directly with another client.

---

# 3. High-Level Architecture

We use a layered architecture.

```text
Presentation Layer

↓

Application Layer

↓

Domain Layer

↓

Infrastructure Layer
```

---

## Presentation Layer

Responsible for:

* REST endpoints
* Flutter UI
* React UI
* Input validation
* Authentication

No business logic.

---

## Application Layer

Responsible for:

* Use cases
* Workflow orchestration
* Transactions
* Permission checks

Business processes belong here.

---

## Domain Layer

Contains:

* Business entities
* Domain rules
* Validation
* Domain services

This layer must remain independent.

---

## Infrastructure Layer

Responsible for:

* Database
* File Storage
* Email
* Redis
* External APIs
* Truck Navigation
* Real-time WebSocket + Redis pub/sub (`app/realtime/`)

---

# 3a. Real-Time Layer (Sprint 9)

Live operational updates use a dedicated realtime module isolated from business services.

```text
Domain Service → publisher.py → EventService → Redis → WebSocket clients
```

Business services must not manage websocket connections directly. They publish domain events after successful commits.

Connected clients:

* Dispatcher dashboard (`frontend/`) — Operations Board, notifications, order detail
* Driver app (`driver_app/`) — current order, workflow, timeline refresh

---

# 4. Folder Structure

```text
backend/

app/

auth/

companies/

users/

drivers/

trucks/

trailers/

customers/

orders/

vehicles/

photos/

cmr/

notifications/

audit/

ai/

common/

config/

database/

tests/
```

Every module follows the same structure.

Example

```text
orders/

models.py

schemas.py

service.py

repository.py

routes.py

permissions.py

validators.py

events.py
```

Never mix responsibilities.

---

# 5. Design Principles

Use:

SOLID

DRY

KISS

YAGNI

Clean Architecture

Repository Pattern

Dependency Injection

Service Layer

Never build "God classes".

---

# 6. Dependency Direction

Always

```text
Routes

↓

Services

↓

Repositories

↓

Database
```

Never:

Database

↓

Routes

No shortcuts.

---

# 7. Business Logic

Business logic exists ONLY in backend.

Flutter

React

Never contain business rules.

Frontend only displays information.

---

# 8. Database Access

Never access SQL directly from routes.

Always

Route

↓

Service

↓

Repository

↓

SQLAlchemy

This allows:

Testing

Maintenance

Caching

Refactoring

---

# 9. Repository Pattern

Repositories perform:

Create

Read

Update

Delete

Search

Nothing else.

Repositories never contain business decisions.

---

# 10. Services

Services contain workflows.

Example

Assign Driver

↓

Check Driver

↓

Check Trailer

↓

Check Company

↓

Assign

↓

Audit

↓

Notify

Everything happens inside service layer.

---

# 11. Event System

Future versions use domain events.

Example

Order Created

↓

Generate Notification

↓

Generate Timeline

↓

Generate Audit

↓

AI Analysis

Routes should never trigger multiple systems.

Services publish events.

---

# 12. Authentication

JWT

Refresh Tokens

Role Based

Multi Company

Every request knows:

User ID

Company ID

Role

Permissions checked in backend.

---

# 13. Multi Tenant Architecture

Every business table contains

company_id

Every repository filters automatically.

Cross-company access is forbidden.

---

# 14. API Design

REST only.

Versioned.

```text
/api/v1/
```

Future

```text
/api/v2/
```

Breaking changes require new version.

---

# 15. Naming

Variables

snake_case

Python Classes

PascalCase

React Components

PascalCase

Flutter Widgets

PascalCase

Database

snake_case

API

kebab-case URLs

Consistency is mandatory.

---

# 16. Error Handling

Never expose stack traces.

Always return structured errors.

Example

```json
{
    "success": false,
    "error": {
        "code": "INVALID_VIN",
        "message": "VIN format is invalid."
    }
}
```

Errors must be understandable.

---

# 17. Logging

Structured logging.

Never

print()

Always use logger.

Log:

Authentication

Assignments

VIN changes

CMR generation

Uploads

Failures

Never log passwords.

Never log tokens.

---

# 18. Audit

Audit records:

Who

When

What

Old Value

New Value

Reason

Nothing important happens without audit.

---

# 19. Offline Strategy

Flutter stores:

Orders

Photos

Queue

Status

When online:

Automatic synchronization.

Conflict resolution always happens in backend.

Backend is the source of truth.

---

# 20. File Storage

Files never stored inside database.

Database stores references only.

Future providers:

Local

S3

Azure Blob

Google Cloud Storage

Storage implementation remains interchangeable.

---

# 21. AI Architecture

AI is a separate module.

AI never directly changes database.

Workflow

AI

↓

Suggestion

↓

Dispatcher

↓

Approval

↓

Backend

↓

Database

AI remains isolated.

---

# 22. Security

Passwords

bcrypt

JWT

HTTPS

CORS

Rate Limiting

Input Validation

Parameterized Queries

SQL Injection protection

CSRF where required

Security is mandatory.

---

# 23. Testing

Every module includes:

Unit Tests

Integration Tests

Repository Tests

API Tests

Business logic should be testable independently.

---

# 24. Performance

Backend target

<200ms

Common queries indexed.

Pagination everywhere.

Lazy loading where appropriate.

No N+1 queries.

Optimize only after measuring.

---

# 25. Scalability

Application must support:

100 companies

10,000 active orders

100 concurrent users

Millions of audit records

Architecture should not require redesign.

---

# 26. Documentation

Every module contains:

Purpose

Dependencies

API

Examples

Known limitations

Documentation evolves with implementation.

---

# 27. Development Workflow

Task

↓

Implementation

↓

Tests

↓

Review

↓

Commit

↓

Push

↓

Next Task

Never skip testing.

---

# 28. Definition of Good Code

Good code is:

Readable

Predictable

Small

Explicit

Well Tested

Documented

Easy to Modify

Not Clever

Future developers should understand code without explanation.

---

# 29. Final Rule

If an implementation choice is unclear:

Choose the solution that makes future maintenance easier.

Maintainability always wins over short-term speed.
