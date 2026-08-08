# ProDrive Backend

FastAPI backend for the ProDrive vehicle transport platform.

## Prerequisites

- Python 3.13
- Docker and Docker Compose
- PostgreSQL 16+ (when running locally without Docker)
- Redis 7+ (when running locally without Docker)

## Quick Start with Docker

From the repository root:

```bash
cp .env.example .env
docker compose up --build
```

The API is available at:

- API base: http://localhost:8000/api/v1
- Health: http://localhost:8000/api/v1/health
- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## Local Development without Docker

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -e ".[dev]"
pre-commit install
cp ../.env.example ../.env
```

Ensure PostgreSQL and Redis are running, then start the API:

```bash
uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

## Authentication

Development seed user (created automatically in `APP_ENV=development`):

| Email | Password |
|-------|----------|
| admin@example.com | Admin123! |

Endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Login with email and password |
| POST | `/api/v1/auth/refresh` | Rotate refresh token |
| POST | `/api/v1/auth/logout` | Revoke refresh token (requires access token) |
| GET | `/api/v1/auth/me` | Current user profile |
| POST | `/api/v1/auth/password-reset/request` | Request password reset |
| POST | `/api/v1/auth/password-reset/confirm` | Confirm password reset |

All auth endpoints (except login, refresh, and password reset) require:

```text
Authorization: Bearer <access_token>
```

---

## Companies

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/v1/companies/me` | Admin, Dispatcher | Read company profile |
| PUT | `/api/v1/companies/me` | Admin | Update company profile |
| POST | `/api/v1/companies/me/logo` | Admin | Upload company logo |
| GET | `/api/v1/companies/settings` | Admin, Dispatcher | Read settings and branding |
| PUT | `/api/v1/companies/settings` | Admin | Update settings and branding |

Logo files are stored on disk under `uploads/` and served from `/uploads/...`.

Every company endpoint is scoped to the authenticated user's `company_id`. Cross-company access is blocked.

---

## Users

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/v1/users` | Admin | List company users |
| POST | `/api/v1/users` | Admin | Create user |
| GET | `/api/v1/users/me` | Authenticated | Read own profile |
| PUT | `/api/v1/users/me` | Authenticated | Update own profile |
| PUT | `/api/v1/users/me/password` | Authenticated | Change own password |
| GET | `/api/v1/users/{id}` | Admin or self | Read user |
| PUT | `/api/v1/users/{id}` | Admin | Update user |
| DELETE | `/api/v1/users/{id}` | Admin | Soft delete user |

Supported roles: `ADMIN`, `DISPATCHER`, `DRIVER`.

---

## Fleet

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/v1/drivers` | Admin, Dispatcher | List drivers |
| POST | `/api/v1/drivers` | Admin, Dispatcher | Create driver profile |
| GET | `/api/v1/drivers/{id}` | Admin, Dispatcher | Read driver profile |
| PUT | `/api/v1/drivers/{id}` | Admin, Dispatcher | Update driver profile |
| DELETE | `/api/v1/drivers/{id}` | Admin, Dispatcher | Soft delete driver profile |
| GET | `/api/v1/drivers/me` | Driver | Read own driver profile |
| GET | `/api/v1/drivers/me/orders` | Driver | List own assigned orders |
| GET | `/api/v1/drivers/me/home` | Driver | Driver home screen payload |
| GET | `/api/v1/drivers/{id}/orders` | Admin, Dispatcher | List driver orders |
| GET | `/api/v1/trucks` | Admin, Dispatcher | List trucks |
| POST | `/api/v1/trucks` | Admin, Dispatcher | Create truck |
| GET | `/api/v1/trucks/{id}` | Admin, Dispatcher | Read truck |
| PUT | `/api/v1/trucks/{id}` | Admin, Dispatcher | Update truck |
| DELETE | `/api/v1/trucks/{id}` | Admin, Dispatcher | Soft delete truck |
| GET | `/api/v1/trailers` | Admin, Dispatcher | List trailers |
| POST | `/api/v1/trailers` | Admin, Dispatcher | Create trailer |
| GET | `/api/v1/trailers/{id}` | Admin, Dispatcher | Read trailer |
| PUT | `/api/v1/trailers/{id}` | Admin, Dispatcher | Update trailer |
| DELETE | `/api/v1/trailers/{id}` | Admin, Dispatcher | Soft delete trailer |
| GET | `/api/v1/fleet/overview` | Admin, Dispatcher | Fleet counts summary |
| GET | `/api/v1/fleet/assignments` | Admin, Dispatcher | List standing fleet assignments |
| GET | `/api/v1/fleet/assignments/me` | Driver | Read own active assignment |
| POST | `/api/v1/fleet/assignments` | Admin, Dispatcher | Create standing assignment |
| DELETE | `/api/v1/fleet/assignments/{id}` | Admin, Dispatcher | Deactivate assignment |

Driver profiles link to users with the `DRIVER` role. Trailer capacity must be one of `2`, `3`, `5`, `8`, or `10`.

---

## Customers

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/v1/customers` | Admin, Dispatcher | List customers (`search` supported) |
| POST | `/api/v1/customers` | Admin, Dispatcher | Create customer |
| GET | `/api/v1/customers/{id}` | Admin, Dispatcher | Read customer |
| PUT | `/api/v1/customers/{id}` | Admin, Dispatcher | Update customer |
| DELETE | `/api/v1/customers/{id}` | Admin, Dispatcher | Soft delete customer |
| GET | `/api/v1/customers/{id}/contacts` | Admin, Dispatcher | List customer contacts |
| POST | `/api/v1/customers/{id}/contacts` | Admin, Dispatcher | Create customer contact |
| PUT | `/api/v1/customers/{id}/contacts/{contact_id}` | Admin, Dispatcher | Update customer contact |
| DELETE | `/api/v1/customers/{id}/contacts/{contact_id}` | Admin, Dispatcher | Soft delete customer contact |
| GET | `/api/v1/customers/{id}/history` | Admin, Dispatcher | Customer order history |

---

## Orders

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/v1/orders` | Admin, Dispatcher | List orders |
| POST | `/api/v1/orders` | Admin, Dispatcher | Create order (wizard supports nested stops/vehicles) |
| GET | `/api/v1/orders/{id}` | Admin, Dispatcher | Read order with stops and vehicles |
| PUT | `/api/v1/orders/{id}` | Admin, Dispatcher | Update order |
| DELETE | `/api/v1/orders/{id}` | Admin, Dispatcher | Soft delete order |
| GET | `/api/v1/orders/{id}/stops` | Admin, Dispatcher | List stops |
| POST | `/api/v1/orders/{id}/stops` | Admin, Dispatcher | Create stop |
| PUT | `/api/v1/stops/{id}` | Admin, Dispatcher | Update stop |
| DELETE | `/api/v1/stops/{id}` | Admin, Dispatcher | Soft delete stop |
| GET | `/api/v1/orders/{id}/vehicles` | Admin, Dispatcher | List vehicles |
| POST | `/api/v1/orders/{id}/vehicles` | Admin, Dispatcher | Create vehicle |
| PUT | `/api/v1/vehicles/{id}` | Admin, Dispatcher | Update vehicle |
| DELETE | `/api/v1/vehicles/{id}` | Admin, Dispatcher | Soft delete vehicle |
| POST | `/api/v1/vehicles/{id}/scan-vin` | Admin, Dispatcher | Scan VIN |
| POST | `/api/v1/vehicles/{id}/update-vin` | Admin, Dispatcher | Update VIN (audited) |
| POST | `/api/v1/orders/{id}/assign-driver` | Admin, Dispatcher | Assign driver and fleet |
| POST | `/api/v1/orders/{id}/accept` | Admin, Dispatcher, Driver | Accept assignment |
| POST | `/api/v1/orders/{id}/reject` | Admin, Dispatcher, Driver | Reject assignment |
| POST | `/api/v1/orders/{id}/arrive-pickup` | Admin, Dispatcher, Driver | Arrive at pickup |
| POST | `/api/v1/orders/{id}/complete-loading` | Admin, Dispatcher, Driver | Complete loading |
| POST | `/api/v1/orders/{id}/arrive-delivery` | Admin, Dispatcher, Driver | Arrive at delivery |
| POST | `/api/v1/orders/{id}/complete-delivery` | Admin, Dispatcher, Driver | Complete delivery |
| POST | `/api/v1/orders/{id}/cancel` | Admin, Dispatcher | Cancel order |
| GET | `/api/v1/orders/{id}/timeline` | Admin, Dispatcher | Read order timeline |
| POST | `/api/v1/ai/parse-order` | Admin, Dispatcher | Parse customer message into draft order |
| POST | `/api/v1/ai/suggest-driver` | Admin, Dispatcher | Suggest driver for an order |
| POST | `/api/v1/ai/suggest-route` | Admin, Dispatcher | Suggest route stop order |
| POST | `/api/v1/ai/suggest-loading` | Admin, Dispatcher | Suggest trailer loading positions |
| POST | `/api/v1/ai/score-order` | Admin, Dispatcher | Score order completeness |

---

## Reports

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/v1/reports/orders` | Admin, Dispatcher | Order activity by status |
| GET | `/api/v1/reports/drivers` | Admin, Dispatcher | Driver activity report |
| GET | `/api/v1/reports/customers` | Admin, Dispatcher | Customer activity report |
| GET | `/api/v1/reports/fleet` | Admin, Dispatcher | Fleet utilization report |
| GET | `/api/v1/reports/kpi` | Admin, Dispatcher | KPI dashboard summary |

---

## Search

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/v1/search?q=` | Admin, Dispatcher | Global search across orders, customers, drivers, VINs, registrations |

---

## Documents & Photos

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| POST | `/api/v1/vehicles/{id}/photos` | Admin, Dispatcher, Driver | Upload vehicle photo |
| GET | `/api/v1/vehicles/{id}/photos` | Admin, Dispatcher | List vehicle photos |
| DELETE | `/api/v1/photos/{id}` | Admin, Dispatcher | Delete vehicle photo |
| POST | `/api/v1/orders/{id}/cmr/generate` | Admin, Dispatcher | Generate printable CMR HTML |
| GET | `/api/v1/orders/{id}/cmr` | Admin, Dispatcher | Fetch latest generated CMR |
| POST | `/api/v1/orders/{id}/cmr/upload` | Admin, Dispatcher, Driver | Upload signed CMR copy |

Photo types: `FRONT`, `REAR`, `LEFT`, `RIGHT`, `INTERIOR`, `DAMAGE`, `DOCUMENT`, `CUSTOM`.

Generated CMR files are stored under `uploads/` and served from `/uploads/...`.

---

## Notifications

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/api/v1/notifications` | Authenticated | List notifications (`unread_only` supported) |
| POST | `/api/v1/notifications/{id}/read` | Authenticated | Mark notification read |
| POST | `/api/v1/notifications/read-all` | Authenticated | Mark all notifications read |

Push delivery is not wired yet; notifications are stored in-app and created on key events such as driver assignment.

---

## Database Migrations

Alembic is configured and ready for future schema changes:

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Testing

```bash
cd backend
pytest
```

## Code Quality

```bash
cd backend
ruff check .
black --check .
mypy app
pre-commit run --all-files
```

## Project Layout

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
  alembic/
  tests/
```

Each business module will follow the same structure:

```text
module/
  models.py
  schemas.py
  service.py
  repository.py
  routes.py
  permissions.py
  validators.py
  events.py
```
