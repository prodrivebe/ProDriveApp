# 003 — Company Module

**Status:** Implemented (Sprint 001)  
**Epic:** Sprint 2 — Identity & Multi-Tenancy

## Feature Name

Company profile, settings, branding, logo upload, multi-tenant isolation.

## Business Goal

Each transport company operates in an isolated tenant with configurable branding and operational settings (order numbering, etc.).

## User Stories

| ID | Role | Story | Priority |
|----|------|-------|----------|
| US-1 | As an **admin**, I want to manage company settings so that order numbers and defaults match our business. | Must |
| US-2 | As an **admin**, I want to upload a logo so that documents and UI show our brand. | Must |
| US-3 | As the **platform**, I want `company_id` on all records so that tenants never see each other's data. | Must |

## Acceptance Criteria

- [x] AC-1: Company and settings CRUD for admin.
- [x] AC-2: Logo upload with size limit enforced.
- [x] AC-3: All business queries filter by `current_user.company_id`.
- [x] AC-4: Cross-tenant access returns `403` or `404`.

## Database Changes

| Change | Type | Migration |
|--------|------|-----------|
| `companies` | Table | `001_initial_auth_schema` |
| `company_settings` | Table | `002_company_settings` |

## API Endpoints

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/companies/me` | Admin | Company profile |
| PUT | `/companies/me` | Admin | Update company |
| GET | `/companies/me/settings` | Admin | Settings |
| PUT | `/companies/me/settings` | Admin | Update settings |
| POST | `/companies/me/logo` | Admin | Upload logo |

## Permissions

| Action | ADMIN | DISPATCHER | DRIVER |
|--------|-------|------------|--------|
| Read company | ✓ | ✗ | ✗ |
| Update / logo | ✓ | ✗ | ✗ |

Dispatchers manage operations, not company settings (per `docs/DISPATCHER.md`).

## Validation Rules

| Rule | Error code |
|------|------------|
| Logo max size (`MAX_LOGO_SIZE_MB`) | `FILE_TOO_LARGE` |
| Invalid image type | `INVALID_FILE_TYPE` |

## Edge Cases

| Scenario | Expected behaviour |
|----------|-------------------|
| Access other company's ID in URL | `404` / `403` via tenant check |
| Soft-deleted company | Not exposed |

## Tests Required

| File | Cases |
|------|-------|
| `tests/test_companies.py` | CRUD, logo, tenant isolation |

## Definition of Done

- [x] Implemented and tested
- [x] Tenant helper `ensure_same_company()` used across services
