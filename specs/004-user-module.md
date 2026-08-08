# 004 — User Module

**Status:** Implemented (Sprint 001)  
**Epic:** Sprint 2 — Identity & Multi-Tenancy

## Feature Name

User management — Admin, Dispatcher, Driver roles, permissions, profile editing.

## Business Goal

Companies manage their staff with clear role boundaries: admins configure the company, dispatchers run operations, drivers use the mobile app only.

## User Stories

| ID | Role | Story | Priority |
|----|------|-------|----------|
| US-1 | As an **admin**, I want to create users with roles so that staff can access the system. | Must |
| US-2 | As an **admin**, I want to deactivate users so that leavers lose access. | Must |
| US-3 | As a **user**, I want to edit my profile (name, email) so that my details stay current. | Must |
| US-4 | As the **system**, I want role checks on every sensitive endpoint. | Must |

## Acceptance Criteria

- [x] AC-1: Admin can CRUD users within their company.
- [x] AC-2: Roles: `ADMIN`, `DISPATCHER`, `DRIVER`.
- [x] AC-3: Users can update own profile via `/users/me`.
- [x] AC-4: Drivers cannot access dispatcher-only endpoints (`403`).
- [x] AC-5: Soft delete preserves audit history.

## Database Changes

| Change | Type | Migration |
|--------|------|-----------|
| `users` | Table (role, company_id, soft delete) | `001_initial_auth_schema` |

## API Endpoints

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/users` | Admin | List users |
| POST | `/users` | Admin | Create user |
| GET | `/users/{id}` | Admin | Get user |
| PUT | `/users/{id}` | Admin | Update user |
| DELETE | `/users/{id}` | Admin | Soft delete |
| GET | `/users/me` | Authenticated | Own profile |
| PUT | `/users/me` | Authenticated | Update own profile |

## Permissions

| Action | ADMIN | DISPATCHER | DRIVER |
|--------|-------|------------|--------|
| Manage users | ✓ | ✗ | ✗ |
| Edit own profile | ✓ | ✓ | ✓ |
| Dispatcher dashboard | ✓ | ✓ | ✗ |

## Validation Rules

| Rule | Error code |
|------|------------|
| Email unique per company | `EMAIL_ALREADY_EXISTS` |
| Cannot delete last admin | `LAST_ADMIN` |
| Valid role enum | `VALIDATION_ERROR` |

## Edge Cases

| Scenario | Expected behaviour |
|----------|-------------------|
| Driver logs into dispatcher UI | Blocked client-side + API role checks |
| Admin demotes self if last admin | Rejected |

## Tests Required

| File | Cases |
|------|-------|
| `tests/test_users.py` | CRUD, roles, profile, permissions |

## Definition of Done

- [x] Implemented and tested
- [x] Dev seed: admin + dispatcher users

## Dev credentials

| Email | Password | Role |
|-------|----------|------|
| admin@example.com | Admin123! | ADMIN |
| dispatcher@example.com | Dispatch123! | DISPATCHER |
