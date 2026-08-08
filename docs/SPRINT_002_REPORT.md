# Sprint 002 Report — Dispatcher Dashboard

## Summary

Sprint 2 delivered the React dispatcher web application: authentication, operations dashboard, order management, fleet visibility, global search, and supporting pages. The dashboard consumes the existing FastAPI backend with JWT authentication and role-based access.

---

## Implemented Features

### Application scaffold
- Vite + React 18 + TypeScript + Material UI
- Auth context with JWT storage and refresh handling
- Protected routes (dispatcher/admin only; drivers rejected)
- App layout with navigation, global search, and logout

### Pages
| Page | Description |
|------|-------------|
| Login | Email/password login against `/api/v1/auth/login` |
| Dashboard | KPI widgets from `/reports/kpi` |
| Orders | Paginated list with status filter |
| Order detail | Full order view, timeline, assign driver/truck/trailer |
| Create order | Wizard: customer → details → review → submit |
| Customers | Read-only customer list |
| Fleet | Drivers, trucks, trailers overview |
| Notifications | In-app notification center |
| Reports | Orders, drivers, customers, fleet reports |

### Backend support
- CORS configured for `http://localhost:5173` and `http://127.0.0.1:5173`
- Development seed user: `dispatcher@example.com` / `Dispatch123!`

---

## API Endpoints Consumed

| Screen | Endpoints |
|--------|-----------|
| Auth | `/auth/login`, `/auth/me`, `/auth/logout` |
| Dashboard | `/reports/kpi`, `/reports/orders`, `/notifications` |
| Orders | `/orders`, `/orders/{id}`, `/orders/{id}/timeline`, `/orders/{id}/assign-driver` |
| Create | `/customers`, `/ai/parse-order`, `/orders` POST |
| Fleet | `/fleet/overview`, `/drivers`, `/trucks`, `/trailers` |
| Search | `/search?q=` |

---

## Tests

| Layer | Status |
|-------|--------|
| Backend integration | 72 tests passing (includes auth, tenant isolation, permissions) |
| Frontend unit tests | Not started |
| E2E tests | Not started |
| Production build | Verified via `npm run build` in Node Docker |

---

## Known Limitations

1. **Customer create/edit UI** — Read-only list; mutations via API only.
2. **Map view** — Deferred to a future sprint.
3. **No Docker service** — Dashboard runs via `npm run dev` locally, not in `docker-compose.yml`.
4. **No CI frontend job** — Build not yet in GitHub Actions.
5. **Standing fleet assignments** — Dashboard shows fleet entities but not Sprint 3 standing assignments (order-level assignment only).

---

## Future Improvements

- Customer create/edit forms
- Map view for stops
- Standing fleet assignment UI (Sprint 3 backend ready)
- Docker/CI integration for frontend build
- Component and E2E tests

---

## Stabilization Review (Sprint 2 + 3)

Verified as part of project stabilization:

- [x] Authentication (login, JWT, refresh, logout, role guard)
- [x] CORS allows dispatcher dev origin
- [x] Dispatcher seed user in development
- [x] Dashboard build succeeds
- [x] All consumed API endpoints registered and documented

---

## Definition of Done Checklist

- [x] React app scaffolded
- [x] Auth and protected routes
- [x] Core pages implemented
- [x] Backend CORS configured
- [x] Build verified
- [x] Spec `013-dispatcher-dashboard.md` updated
- [x] Documentation updated
