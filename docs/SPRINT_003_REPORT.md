# Sprint 003 Report — Fleet Management

## Summary

Sprint 3 delivered the operational fleet foundation: drivers, trucks, trailers, and standing fleet assignments with multi-tenant isolation, role-based permissions, audit logging, and comprehensive tests. Stabilization review verified all backend checks pass.

---

## Implemented Features

### Drivers
- Full CRUD including soft delete (`DELETE /api/v1/drivers/{id}`)
- Search by phone, license, notes, and linked user name
- Filter by active/inactive
- Driver self-service: `/drivers/me`, `/drivers/me/orders`, `/drivers/me/home`
- Audit events: `DRIVER_CREATED`, `DRIVER_UPDATED`, `DRIVER_DELETED`

### Trucks
- Full CRUD with registration uniqueness per company
- `GET /api/v1/trucks/{id}` endpoint
- Audit events: `TRUCK_CREATED`, `TRUCK_UPDATED`, `TRUCK_DELETED`

### Trailers
- Full CRUD with registration uniqueness per company
- `GET /api/v1/trailers/{id}` endpoint
- Capacity validation via allowed enum values (2, 3, 5, 8, 10)
- Audit events: `TRAILER_CREATED`, `TRAILER_UPDATED`, `TRAILER_DELETED`

### Fleet Assignments
- Standing driver + truck + trailer assignments (separate from order-level assignment)
- `GET /api/v1/fleet/assignments` — list assignments (admin/dispatcher)
- `GET /api/v1/fleet/assignments/me` — driver reads own active assignment
- `POST /api/v1/fleet/assignments` — create assignment with validation
- `DELETE /api/v1/fleet/assignments/{id}` — deactivate assignment
- One active assignment per driver, truck, and trailer within a company
- Audit events: `ASSIGNMENT_CREATED`, `ASSIGNMENT_REMOVED`

### Permissions
| Role | Access |
|------|--------|
| Admin | Full fleet access |
| Dispatcher | Full fleet access |
| Driver | Read own profile (`/drivers/me`), read own assignment (`/fleet/assignments/me`) |

---

## Database Changes

### Migration `009_fleet_assignments_schema`

New table: `fleet_assignments`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| company_id | UUID | FK → companies |
| driver_id | UUID | FK → drivers |
| truck_id | UUID | FK → trucks |
| trailer_id | UUID | FK → trailers |
| assigned_at | timestamptz | Assignment start |
| unassigned_at | timestamptz | Nullable; set on removal |
| active | boolean | Only one active row per driver/truck/trailer |

Partial unique indexes enforce one active assignment per driver, truck, and trailer within a company.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/drivers` | List drivers |
| POST | `/api/v1/drivers` | Create driver |
| GET | `/api/v1/drivers/{id}` | Get driver |
| PUT | `/api/v1/drivers/{id}` | Update driver |
| DELETE | `/api/v1/drivers/{id}` | Soft delete driver |
| GET | `/api/v1/drivers/me` | Current driver profile |
| GET | `/api/v1/drivers/me/orders` | Current driver orders |
| GET | `/api/v1/drivers/me/home` | Driver home screen |
| GET | `/api/v1/trucks` | List trucks |
| POST | `/api/v1/trucks` | Create truck |
| GET | `/api/v1/trucks/{id}` | Get truck |
| PUT | `/api/v1/trucks/{id}` | Update truck |
| DELETE | `/api/v1/trucks/{id}` | Soft delete truck |
| GET | `/api/v1/trailers` | List trailers |
| POST | `/api/v1/trailers` | Create trailer |
| GET | `/api/v1/trailers/{id}` | Get trailer |
| PUT | `/api/v1/trailers/{id}` | Update trailer |
| DELETE | `/api/v1/trailers/{id}` | Soft delete trailer |
| GET | `/api/v1/fleet/overview` | Fleet counts |
| GET | `/api/v1/fleet/assignments` | List assignments |
| GET | `/api/v1/fleet/assignments/me` | Driver's active assignment |
| POST | `/api/v1/fleet/assignments` | Create assignment |
| DELETE | `/api/v1/fleet/assignments/{id}` | Remove assignment |

---

## Tests

Expanded `backend/tests/test_fleet.py` (20 tests) covering:

- Driver, truck, and trailer CRUD
- Driver soft delete and name search
- Duplicate registration validation
- Assignment creation and removal
- Duplicate assignment prevention
- Cross-company isolation (404)
- Permission checks (driver cannot create assignments)
- Driver read own assignment
- Audit log creation for all fleet mutations

**Full backend suite: 72 tests passing.**

---

## Stabilization Review

Full project verification completed for Sprints 2 and 3:

| Check | Result |
|-------|--------|
| Authentication | Login, JWT, refresh, logout, password reset tested |
| Multi-tenant isolation | Cross-company access returns 404 |
| Role-based permissions | Admin/dispatcher full access; driver read-only |
| Fleet modules | Drivers, trucks, trailers, assignments operational |
| API registration | All routes registered in `main.py` |
| Migrations | `001`–`009` including `fleet_assignments` |
| Docker | `docker compose up --build` verified |
| Tests | 72 passed |
| Ruff lint | All checks passed |
| Mypy | Success (136 source files) |
| Documentation | API, DATABASE, TASKS updated |

### Code quality fixes applied during stabilization
- TYPE_CHECKING imports for SQLAlchemy relationship forward refs
- Mypy return types on order timeline, assigned driver, photo vehicle helpers
- Report/search repository tuple typing
- Trailer Decimal-to-float casting
- Ruff E501 delegated to Black (standard dual-tool setup)
- CI workflow extended with ruff and mypy jobs

---

## Known Limitations

1. **`drivers.user_id` is NOT NULL** — Operational drivers require a linked user account.
2. **Trailer capacity enum** — `maximum_vehicle_count` restricted to `{2, 3, 5, 8, 10}`.
3. **Standing vs order assignment** — Fleet assignments and order-level assignment coexist separately.
4. **SQLite test DB** — Partial unique indexes are PostgreSQL-specific; service-level checks supplement tests.
5. **Dispatcher dashboard** — Does not yet expose standing fleet assignment UI.

---

## Future Improvements

- Surface standing fleet assignment on driver home screen and dispatcher fleet page
- Assignment history view with pagination
- Block assignment removal when driver has active orders
- Fleet availability dashboard (unassigned drivers/trucks/trailers)

---

## Definition of Done Checklist

- [x] Migration `009_fleet_assignments_schema` added
- [x] Fleet assignment module implemented
- [x] Audit logging wired for all fleet mutations
- [x] Multi-tenant isolation verified
- [x] Assignment conflict rules enforced
- [x] Permission checks implemented
- [x] Tests expanded (72 total passing)
- [x] Ruff and mypy clean
- [x] Docker starts successfully
- [x] `docs/API.md` updated
- [x] `docs/DATABASE.md` updated
- [x] `docs/TASKS.md` updated
