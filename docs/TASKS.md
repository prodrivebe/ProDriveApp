# ProDrive Development Tasks

## Milestone 1 — Foundation

* [x] Create FastAPI project
* [x] Configure Docker
* [x] Configure PostgreSQL
* [x] Configure Alembic
* [x] Configure environment variables
* [x] Health endpoint
* [x] CI setup

---

## Milestone 2 — Authentication

* [x] Login
* [x] JWT
* [x] Refresh token
* [x] Password hashing
* [x] Role authorization
* [x] Password reset
* [x] Audit login events

---

## Milestone 3 — Companies

* [x] Company model
* [x] Company settings
* [x] Logo upload
* [x] Branding
* [x] Multi-company isolation

---

## Milestone 4 — Users

* [x] Admin
* [x] Dispatcher
* [x] Driver
* [x] User management
* [x] Permissions
* [x] Profile editing

---

## Milestone 5 — Fleet

* [x] Drivers
* [x] Trucks
* [x] Trailers
* [x] Trailer capacities
* [x] Fleet overview
* [x] Fleet assignments
* [x] Fleet audit logging
* [x] Driver soft delete
* [x] Driver name search

---

## Sprint 2 — Dispatcher Dashboard

* [x] React + TypeScript + MUI scaffold
* [x] Auth (login, JWT, role guard)
* [x] Dashboard KPI widgets
* [x] Orders list and detail
* [x] Create order wizard
* [x] Driver/truck/trailer assignment on orders
* [x] Global search
* [x] Customers, fleet, notifications, reports pages
* [x] Backend CORS for local dev
* [x] Dispatcher seed user
* [ ] Customer create/edit UI (deferred)
* [ ] Map view (deferred)
* [ ] Frontend tests / CI build (deferred)

---

## Sprint 3 — Fleet Management

* [x] Drivers CRUD with audit
* [x] Trucks CRUD with audit
* [x] Trailers CRUD with audit
* [x] Fleet assignments (create, list, remove)
* [x] Assignment conflict rules
* [x] Multi-tenant isolation
* [x] Permission checks
* [x] Fleet module tests
* [x] API and database documentation
* [x] Lint and type-check clean

---

## Sprint 4 — Order Management

* [x] Extract `order_stops`, `order_vehicles`, `order_timeline` modules
* [x] Order CRUD with company-scoped order numbers
* [x] Multi-stop orders with unique sequence validation
* [x] Multi-vehicle orders with stop link validation
* [x] Automatic read-only timeline generation
* [x] Status transition validation
* [x] Audit logging for order, stop, and vehicle mutations
* [x] Cross-company isolation (404)
* [x] Soft delete for orders, stops, and vehicles
* [x] Permission checks (manager vs driver)
* [x] Order domain tests
* [x] API and database documentation

---

## Sprint 5 — Driver Workflow

* [x] Operational workflow state machine (`app/workflow/`)
* [x] Workflow endpoints (accept through complete-delivery)
* [x] Assigned-driver restrictions with dispatcher override
* [x] Stop progress tracking (`progress_status`, arrival/departure timestamps)
* [x] `GET /drivers/me/current-order`
* [x] Timeline integration for all workflow actions
* [x] In-app notification records for workflow milestones
* [x] Workflow audit with previous/new status
* [x] Workflow tests (90%+ service coverage target)
* [x] API and database documentation

---

## Sprint 6 — Vehicle Execution and Evidence

* [x] VIN verification with immutable history (`app/vin_verification/`)
* [x] Order-scoped vehicle photos (`app/vehicle_photos/`)
* [x] Vehicle damage reporting with photo attachments (`app/vehicle_damage/`)
* [x] Versioned order documents and CMR uploads (`app/order_documents/`)
* [x] Completion checklist and enforced order completion (`app/completion_checklist/`)
* [x] Timeline integration for all evidence actions
* [x] Notification records for VIN changed, damage reported, CMR uploaded, order ready
* [x] Local file storage abstraction (`app/common/storage/`)
* [x] Execution tests and documentation

---

## Milestone 6 — Customers

* [x] Customer management
* [x] Contacts
* [x] Search
* [x] Customer history

---

## Milestone 7 — Orders

* [x] Order Wizard
* [x] AI extraction
* [x] Pickup stops
* [x] Delivery stops
* [x] Vehicle management
* [x] VIN management
* [x] Driver assignment
* [x] Order timeline

---

## Milestone 8 — Driver App

* [x] Login
* [x] Home screen
* [x] Order details
* [x] Truck navigation launch
* [x] Arrival confirmation
* [ ] VIN scanner (camera OCR — manual entry in v1)
* [x] Photo capture (API wired; UI stub in Flutter)
* [x] Loading complete
* [x] Delivery workflow
* [x] CMR upload (API wired)
* [x] Offline synchronization (queue stub)

---

## Milestone 9 — Documents

* [x] Automatic CMR generation
* [ ] Bluetooth printing (client-side Driver App)
* [x] Digital signatures (signed CMR upload)
* [x] Photo storage

---

## Milestone 10 — AI

* [x] Customer message parser
* [x] Driver recommendation
* [x] Route optimization
* [x] Trailer loading suggestions
* [x] Order quality score
* [x] Empty kilometer recommendations

---

## Milestone 11 — Notifications

* [x] Push notifications (device registration stub; FCM send deferred)
* [x] Dispatcher notification center (in-app API)
* [x] Driver alerts

---

## Milestone 12 — Reports

* [x] Orders
* [x] Drivers
* [x] Customers
* [x] Fleet
* [x] KPI dashboard

---

# Definition of Done

A task is complete only when:

* Code implemented
* Tests pass
* No critical bugs
* Reviewed
* Committed to Git
* Documentation updated
