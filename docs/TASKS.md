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

## Sprint 7 — Dispatcher Operations Board

* [x] React + TypeScript dispatcher web app (`frontend/`)
* [x] JWT authentication with refresh token handling
* [x] Protected routes and role-based UI
* [x] Operations board dashboard with live backend data
* [x] Orders list, detail tabs, and creation form
* [x] Drivers, fleet, customers, documents, notifications pages
* [x] Timeline, photo gallery, document upload/preview
* [x] TanStack Query data layer and typed API services
* [x] React Hook Form + Zod validation
* [x] Frontend tests and documentation

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

* [x] Flutter scaffold with Riverpod, Dio, GoRouter, Hive, secure storage
* [x] Login, logout, token refresh, session persistence
* [x] Home screen (current order, next action, truck/trailer, workflow CTA)
* [x] Orders list, order detail, stops, vehicles, timeline, checklist
* [x] Full driver workflow actions (accept through complete delivery)
* [x] Manual VIN verification and history
* [x] Photo capture (camera/gallery) with offline upload queue
* [x] Damage reporting
* [x] CMR document upload
* [x] Offline cache + synchronization
* [x] Profile and notifications
* [x] Driver app tests (unit/widget)
* [ ] VIN scanner (camera OCR — out of Sprint 8 scope)
* [ ] GPS tracking (deferred)
* [ ] Push notifications FCM (deferred to Sprint 10)

---

## Sprint 9 — Real-Time Operations

* [x] WebSocket infrastructure with JWT authentication
* [x] Redis pub/sub event service
* [x] Company-isolated channels (company, dispatcher, driver, order, notifications)
* [x] Domain event publishing from workflow and execution services
* [x] Presence tracking (`GET /realtime/presence`)
* [x] Dispatcher Operations Board live kanban columns
* [x] React WebSocket client with reconnect + TanStack Query invalidation
* [x] Flutter WebSocket client with Riverpod invalidation
* [x] Real-time notifications and timeline streaming
* [x] Backend/frontend/driver tests
* [ ] GPS tracking (deferred)
* [ ] Route optimization (deferred)
* [ ] AI live recommendations (deferred)

---

## Sprint 10 — AI-Assisted Dispatching

* [x] Dedicated AI module (`backend/app/ai/`)
* [x] Order Parser Agent with per-field confidence scores
* [x] Driver Recommendation Agent with reasoning
* [x] `ai_suggestions` and `ai_audit_logs` tables
* [x] Suggestion approval workflow (approve creates order via `OrderService`)
* [x] Rejection tracking and audit logging
* [x] AI API routes (`/ai/parse-order`, `/ai/recommend-driver`, `/ai/suggestions/*`)
* [x] Dispatcher AI panel on create order page
* [x] Driver recommendation panel on order detail page
* [x] Backend and frontend tests (mocked/heuristic providers)
* [x] API and AI documentation
* [ ] External LLM provider integration (deferred to Sprint 12)
* [ ] Push notifications FCM (deferred)

---

## Sprint 11 — Planning Board and Loading Optimization

* [x] Planning module (`backend/app/planning/`)
* [x] Planning board API with kanban columns and filters
* [x] Assignment board with availability and conflict indicators
* [x] Loading optimizer with deck-aware positions
* [x] Capacity, height, and weight validation
* [x] Route sequence planning with travel estimate
* [x] `loading_plans` and `loading_positions` persistence
* [x] AI loading optimization suggestions with mandatory approval
* [x] Planning board and loading board UI
* [x] Trailer visualization with drag-and-drop positions
* [x] Real-time planning board invalidation
* [x] Backend tests and documentation

---

## Sprint 12 — Beta Readiness

* [x] Readiness health probe (`/health/ready`) with DB + Redis checks
* [x] Request logging middleware with correlation IDs
* [x] Global unhandled exception handler
* [x] Production JWT secret validation
* [x] Performance index migration (`014_beta_performance_indexes`)
* [x] Beta seed script (`SEED_BETA=true`)
* [x] End-to-end, security, and multi-tenant integration tests
* [x] Backup and restore scripts
* [x] Production Docker Compose (`docker-compose.prod.yml`)
* [x] CI frontend build and test job
* [x] Beta checklist, test plan, deployment guide
* [x] Beta smoke test toolkit
* [x] Sprint 12 report with prioritized issue register

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
