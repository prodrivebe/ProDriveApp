# Sprint 7 Report — Dispatcher Operations Board

**Date:** 2026-08-09  
**Scope:** React dispatcher web application connected to Sprints 1–6 backend

---

## Implemented Screens

| Screen | Route | Description |
|--------|-------|-------------|
| Login | `/login` | JWT authentication, driver role blocked |
| Operations Board | `/` | Live KPI widgets, order/driver panels, notifications |
| Orders | `/orders` | Paginated table with search, status, and date filters |
| Order detail | `/orders/:id` | Tabs: Overview, Vehicles, Timeline, Photos, Documents, Damage |
| Create order | `/orders/new` | Multi-stop, multi-vehicle form with assignment |
| Drivers | `/drivers` | Driver table with availability and active order |
| Driver detail | `/drivers/:id` | Contact info, current assignment, history |
| Fleet | `/fleet` | Truck/trailer tables and fleet overview |
| Customers | `/customers` | Searchable customer list |
| Customer detail | `/customers/:id` | Profile, contacts, order history |
| Documents | `/documents` | Cross-order document index with preview links |
| Notifications | `/notifications` | In-app notification center |
| Settings | `/settings` | Admin-only company settings (read-only) |

---

## API Integration

Typed service modules:

* `authService` — login, logout, current user
* `ordersService` — orders, timeline, checklist, photos, damage, documents
* `driversService` — driver list and detail
* `fleetService` — overview, trucks, trailers
* `customersService` — customers and contacts
* `notificationsService` — list, mark read
* `dashboardService` — KPI, order reports, global search

Axios client features:

* JWT bearer injection
* Automatic refresh on 401
* Standardized error extraction
* Paginated list helper

---

## Routing

React Router 7 with:

* Public login route
* Protected layout wrapper
* Nested routes under `MainLayout`
* Admin-only settings redirect

---

## State Management

TanStack Query for:

* Server state caching (30s stale time)
* Automatic refetch on window focus
* Mutation invalidation after assignments and uploads
* Dashboard parallel queries

Local UI state for tabs, filters, and form steps.

---

## Layout

* Top navigation with global search and notification bell
* Left sidebar (responsive drawer on mobile)
* Content area for module pages
* Role-based sidebar items (Settings admin-only)

---

## Tests

Vitest + Testing Library:

* Login form validation and submit
* Protected route redirect and access
* Dashboard widget rendering (mocked API)
* Orders table rendering (mocked API)
* Order form Zod schema validation
* Permission hook role checks

Run locally:

```bash
cd frontend
npm install
npm run test
npm run build
```

---

## Known Limitations

* No AI order parsing or driver suggestions (explicitly out of scope)
* No drag-and-drop planning board
* No WebSockets / real-time push (polling/refetch only)
* Settings page is read-only
* Order list enriches pickup/delivery via secondary detail fetches
* Priority filter not available (backend has no order priority field)
* Legacy `dispatcher-dashboard/` folder superseded by `frontend/`

---

## Recommendations for Sprint 8

1. Add WebSocket or SSE for live order/driver updates
2. Implement editable company settings for admins
3. Add map view for active routes (when GPS backend exists)
4. Consolidate or remove legacy `dispatcher-dashboard/`
5. Add E2E tests (Playwright) against docker-compose stack
6. Optimize order list with backend join fields for customer and stop summaries
