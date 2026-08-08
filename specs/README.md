# ProDrive Engineering Specifications

This folder is the **source of truth for feature requirements**. Cursor (and all developers) implement specifications — not vague prompts.

## How to use

1. **Before coding** — Read the relevant spec file(s) and `docs/PROJECT.md`.
2. **New feature** — Copy `docs/FEATURE_SPEC_TEMPLATE.md` → `specs/NNN-feature-name.md`, fill every section, get review, then implement.
3. **After shipping** — Update spec status to `Implemented` and check off Definition of Done.

## Numbering

| Range | Domain |
|-------|--------|
| 001 | Foundation (Docker, DB, CI) |
| 002–004 | Identity & multi-tenancy (Auth, Companies, Users) |
| 005–007 | Core operations (Fleet, Customers, Orders) |
| 008 | Driver mobile app |
| 009–012 | Documents, AI, Notifications, Reports |
| 013+ | Frontends and extensions |

## Status values

| Status | Meaning |
|--------|---------|
| **Proposed** | Spec written, not yet approved |
| **Approved** | Ready for implementation |
| **In Progress** | Active development |
| **Implemented** | Shipped and tested |
| **Partial** | Core done; gaps documented in spec |

## Sprint mapping

| Sprint | Focus | Specs |
|--------|-------|-------|
| Sprint 001 | Backend foundation + all API modules | 001–012 |
| Sprint 002 | Dispatcher dashboard (React) | 013 |
| Sprint 003+ | Driver app polish, FCM, production hardening | TBD |

> **Note:** Identity & multi-tenancy (002–004) was delivered in Sprint 001 backend work. Those specs document what exists; they are not pending re-implementation.

## Spec template sections

Every spec must include:

- Feature Name
- Business Goal
- User Stories
- Acceptance Criteria
- Database Changes
- API Endpoints
- Permissions
- Validation Rules
- Edge Cases
- Tests Required
- Definition of Done

See `docs/FEATURE_SPEC_TEMPLATE.md` for the blank template.
