# ProDrive

Drive smarter. Deliver better.

## Overview

ProDrive is a professional SaaS platform built for vehicle transport companies.

The platform includes:

* FastAPI Backend
* React Dispatcher Dashboard
* Flutter Android Driver App
* AI Assistant
* PostgreSQL Database

---

## Repository Structure

```text
backend/
frontend/
driver_app/
dispatcher-dashboard/   (legacy prototype, superseded by frontend/)
docs/
specs/
design/
deployment/
```

---

## Technology

Backend

* Python
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic

Frontend

* React
* TypeScript

Mobile

* Flutter

Infrastructure

* Docker

---

## Development Philosophy

* Small commits
* Feature branches
* Clean architecture
* Test every feature
* Keep business logic on the backend
* AI assists but never makes business decisions

---

## Current Status

Version: 0.1 Alpha

Sprints 1–6 backend complete. Sprint 7 dispatcher web application (`frontend/`) connects to the operational API.

Backend: execution workflow, orders, fleet, customers, documents, notifications.

---

## Local Development

### Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

Services:

| Service  | URL                         |
|----------|-----------------------------|
| API      | http://localhost:8000       |
| Health   | http://localhost:8000/api/v1/health |
| Swagger  | http://localhost:8000/docs  |
| Postgres | localhost:5432              |
| Redis    | localhost:6379              |

### Dispatcher web application (Sprint 7)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 (requires backend at http://localhost:8000).

See [frontend/README.md](frontend/README.md).

The legacy `dispatcher-dashboard/` prototype remains for reference.

### Backend without Docker

See [backend/README.md](backend/README.md) for Python setup, migrations, tests, and linting.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

Ensure PostgreSQL and Redis are running and configured in `.env`.

---

## Development Workflow

1. Read the relevant spec in `specs/`
2. Select or update a task in `docs/TASKS.md`
3. Implement against acceptance criteria in the spec
4. Run tests
5. Update spec status and Definition of Done
6. Commit changes
7. Open a pull request (if applicable)

---

## Coding Standards

* Type hints everywhere
* Clear naming
* Small functions
* No duplicated logic
* Comprehensive logging
* Audit important actions

---

## Project Goal

Build a production-ready logistics platform specifically for auto transport companies.

Every feature should make the dispatcher faster or the driver's job easier.
