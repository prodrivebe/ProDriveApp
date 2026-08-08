# 001 — Backend Foundation

**Status:** Implemented (Sprint 001)  
**Version:** 0.1.0

## Feature Name

ProDrive API foundation — FastAPI, Docker, PostgreSQL, Redis, Alembic, CI.

## Business Goal

Provide a reproducible, production-oriented backend shell so all business modules share one deployment, database, and engineering standards.

## User Stories

| ID | Role | Story | Priority |
|----|------|-------|----------|
| US-1 | As a **developer**, I want Docker Compose so that I can run the full stack locally with one command. | Must |
| US-2 | As a **developer**, I want Alembic migrations so that schema changes are versioned. | Must |
| US-3 | As an **operator**, I want a health endpoint so that I can monitor uptime. | Must |
| US-4 | As a **team**, I want CI running pytest so that regressions are caught on push. | Must |

## Acceptance Criteria

- [x] AC-1: `docker compose up --build` starts Postgres, Redis, and API healthy.
- [x] AC-2: `GET /api/v1/health` returns service status JSON.
- [x] AC-3: Alembic migrations apply cleanly on container start.
- [x] AC-4: GitHub Actions runs pytest on `main`.
- [x] AC-5: Environment variables documented in `.env.example`.

## Database Changes

| Change | Type | Details |
|--------|------|---------|
| N/A (infrastructure) | — | Schema owned by feature specs 002+ |

## API Endpoints

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/v1/health` | Public | Liveness check |

## Permissions

N/A — health is public.

## Validation Rules

N/A

## Edge Cases

| Scenario | Expected behaviour |
|----------|-------------------|
| DB unavailable on start | Container fails health check; logs show connection error |
| Missing `.env` | Docker Compose uses defaults from compose file |

## Tests Required

| File | Cases |
|------|-------|
| `tests/test_health.py` | Health returns 200 and expected fields |

## Definition of Done

- [x] Code implemented
- [x] Tests pass (61 total suite)
- [x] Docker verified from clean volumes
- [x] Documented in README
- [x] Committed to Git (`bcce68e`, `69138f6`)
