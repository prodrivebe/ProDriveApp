# 002 — Authentication

**Status:** Implemented (Sprint 001)  
**Epic:** Sprint 2 — Identity & Multi-Tenancy (delivered in backend v0.1)

## Feature Name

JWT authentication — login, refresh, logout, password reset, `/me`.

## Business Goal

Secure, stateless API access for admins, dispatchers, and drivers with auditable login events and role-based authorization.

## User Stories

| ID | Role | Story | Priority |
|----|------|-------|----------|
| US-1 | As a **user**, I want to log in with email/password so that I receive an access token. | Must |
| US-2 | As a **user**, I want refresh tokens so that I stay signed in without re-entering password. | Must |
| US-3 | As a **user**, I want to log out so that refresh tokens are revoked. | Must |
| US-4 | As a **user**, I want password reset so that I can recover access. | Must |
| US-5 | As a **client**, I want `/auth/me` so that I can show the current profile. | Must |

## Acceptance Criteria

- [x] AC-1: Login returns access + refresh JWT pair.
- [x] AC-2: Protected routes reject missing/invalid tokens with `401`.
- [x] AC-3: Refresh rotates tokens.
- [x] AC-4: Logout revokes refresh token.
- [x] AC-5: Passwords stored with bcrypt; never returned in API.
- [x] AC-6: Login events written to audit log.
- [x] AC-7: `GET /auth/me` returns current user profile.

## Database Changes

| Change | Type | Migration |
|--------|------|-----------|
| `users` | Table | `001_initial_auth_schema` |
| `refresh_tokens` | Table | `001_initial_auth_schema` |
| `password_reset_tokens` | Table | `001_initial_auth_schema` |
| `audit_logs` | Table | `001_initial_auth_schema` |

## API Endpoints

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| POST | `/auth/login` | Public | Login |
| POST | `/auth/refresh` | Public | Rotate tokens |
| POST | `/auth/logout` | Authenticated | Revoke refresh |
| GET | `/auth/me` | Authenticated | Current user |
| POST | `/auth/password-reset/request` | Public | Request reset |
| POST | `/auth/password-reset/confirm` | Public | Confirm reset |

## Permissions

| Action | Public | Authenticated |
|--------|--------|---------------|
| Login / refresh / reset | ✓ | — |
| Logout / me | — | ✓ |

Role enforcement via `require_roles()` on downstream modules.

## Validation Rules

| Rule | Error code |
|------|------------|
| Invalid credentials | `INVALID_CREDENTIALS` |
| Inactive user | `USER_INACTIVE` |
| Expired refresh token | `INVALID_TOKEN` |
| Password min 8 chars | `VALIDATION_ERROR` |

## Edge Cases

| Scenario | Expected behaviour |
|----------|-------------------|
| Duplicate login | New refresh token; old sessions policy per refresh rotation |
| Wrong company isolation | Auth is email-scoped per company on login lookup |

## Tests Required

| File | Cases |
|------|-------|
| `tests/test_auth.py` | Login, refresh, logout, me, password reset, audit |

## Definition of Done

- [x] All acceptance criteria met
- [x] Tests pass
- [x] Documented in `backend/README.md` and `docs/API.md`

## Future enhancements (not in v0.1)

- MFA / SSO
- Session listing and revoke-all
- Rate limiting on login
