# API.md

# ProDrive REST API Specification

Version 1.0

---

# 1. API Philosophy

The API is the only interface to the backend.

Clients never access the database directly.

All business rules are enforced by the backend.

The API is:

* RESTful
* Versioned
* Stateless
* JSON-based
* Secure
* Predictable

---

# 2. Base URL

Development

```
http://localhost:8000/api/v1
```

Production

```
https://api.prodrive.eu/api/v1
```

All future breaking changes require a new version.

Example:

```
/api/v2
```

---

# 3. Authentication

Authentication uses JWT.

Workflow

Login

↓

Access Token

↓

Refresh Token

↓

Authenticated Requests

Authorization Header

```
Authorization: Bearer <access_token>
```

Tokens are never stored in URLs.

---

# 4. Standard Response Format

Successful response

```json
{
  "success": true,
  "data": {},
  "meta": {}
}
```

Error response

```json
{
  "success": false,
  "error": {
    "code": "INVALID_VIN",
    "message": "VIN format is invalid."
  }
}
```

Every endpoint follows the same structure.

---

# 5. Pagination

Collections return:

```json
{
  "success": true,
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total": 310,
    "pages": 13
  }
}
```

Default page size:

25

Maximum:

100

---

# 6. Filtering

Supported query parameters:

```
?page=1

&page_size=25

&search=

&status=

&driver_id=

&customer_id=

&sort=

&direction=
```

---

# 7. Authentication Endpoints

POST

```
/auth/login
```

POST

```
/auth/refresh
```

POST

```
/auth/logout
```

GET

```
/auth/me
```

---

# 8. Company Endpoints

GET

```
/companies/me
```

PUT

```
/companies/me
```

GET

```
/companies/settings
```

PUT

```
/companies/settings
```

---

# 9. User Endpoints

GET

```
/users
```

POST

```
/users
```

GET

```
/users/{id}
```

PUT

```
/users/{id}
```

DELETE

```
/users/{id}
```

---

# 10. Driver Endpoints

GET

```
/drivers
```

POST

```
/drivers
```

GET

```
/drivers/{id}
```

PUT

```
/drivers/{id}
```

DELETE

```
/drivers/{id}
```

GET

```
/drivers/{id}/orders
```

GET

```
/drivers/me
```

GET

```
/drivers/me/orders
```

GET

```
/drivers/me/home
```

GET

```
/drivers/me/current-order
```

Returns the active order, current stop, remaining stops, vehicles, next required action, and workflow status for the driver home screen.

---

# 11. Truck Endpoints

GET

```
/trucks
```

POST

```
/trucks
```

GET

```
/trucks/{id}
```

PUT

```
/trucks/{id}
```

DELETE

```
/trucks/{id}
```

---

# 12. Trailer Endpoints

GET

```
/trailers
```

POST

```
/trailers
```

GET

```
/trailers/{id}
```

PUT

```
/trailers/{id}
```

DELETE

```
/trailers/{id}
```

---

# 13. Fleet Assignment Endpoints

GET

```
/fleet/overview
```

GET

```
/fleet/assignments
```

GET

```
/fleet/assignments/me
```

POST

```
/fleet/assignments
```

DELETE

```
/fleet/assignments/{id}
```

---

# 14. Customer Endpoints

GET

```
/customers
```

POST

```
/customers
```

GET

```
/customers/{id}
```

PUT

```
/customers/{id}
```

DELETE

```
/customers/{id}
```

---

# 15. Order Endpoints

Create order

POST

```
/orders
```

Update order

PUT

```
/orders/{id}
```

View order

GET

```
/orders/{id}
```

List orders

GET

```
/orders
```

Delete order

DELETE

```
/orders/{id}
```

Soft delete only.

---

# 16. Order Workflow Endpoints

Implemented in `app/workflow/`. Only the assigned driver may execute workflow actions unless the user is an admin or dispatcher.

Assign Driver

POST

```
/orders/{id}/assign-driver
```

Driver Accept

POST

```
/orders/{id}/accept
```

Driver Reject

POST

```
/orders/{id}/reject
```

Arrive Pickup

POST

```
/orders/{id}/arrive-pickup
```

Start Loading

POST

```
/orders/{id}/start-loading
```

Complete Loading

POST

```
/orders/{id}/complete-loading
```

Start Transit

POST

```
/orders/{id}/start-transit
```

Arrive Delivery

POST

```
/orders/{id}/arrive-delivery
```

Start Delivery

POST

```
/orders/{id}/start-delivery
```

Complete Delivery

POST

```
/orders/{id}/complete-delivery
```

Cancel

POST

```
/orders/{id}/cancel
```

Workflow state machine:

ASSIGNED → ACCEPTED → ARRIVED_PICKUP → LOADING → LOADED → IN_TRANSIT → ARRIVED_DELIVERY → DELIVERING → COMPLETED

Invalid transitions return `422 INVALID_ORDER_STATUS`. Unauthorized drivers receive `403 FORBIDDEN`.

Each action creates timeline entries and audit records with previous and new status values.

---

# 17. Stop Endpoints

GET

```
/orders/{id}/stops
```

POST

```
/orders/{id}/stops
```

PUT

```
/stops/{id}
```

DELETE

```
/stops/{id}
```

Soft delete only.

Stop sequence values must be unique within an order. Pickup and delivery stop types are validated on vehicle linking.

Implemented in `app/order_stops/`.

---

# 18. Vehicle Endpoints

GET

```
/orders/{id}/vehicles
```

POST

```
/orders/{id}/vehicles
```

PUT

```
/vehicles/{id}
```

DELETE

```
/vehicles/{id}
```

Soft delete only.

Vehicle pickup and delivery stop references must belong to the same order and match stop types.

CRUD implemented in `app/order_vehicles/`. Legacy manager VIN scan endpoints remain under `/vehicles`.

Sprint 6 adds order-scoped VIN verification in `app/vin_verification/`.

---

# 19. VIN Endpoints

## Order-scoped verification (Sprint 6)

Verify VIN

POST

```
/orders/{orderId}/vehicles/{vehicleId}/verify-vin
```

Body

```json
{
  "vin": "1HGBH41JXMN109186"
}
```

Update verified VIN

PUT

```
/orders/{orderId}/vehicles/{vehicleId}/vin
```

VIN history (immutable)

GET

```
/orders/{orderId}/vehicles/{vehicleId}/vin-history
```

Driver, dispatcher, and admin roles may verify VIN on assigned orders. History entries are append-only.

## Legacy manager scan endpoints

Scan VIN

POST

```
/vehicles/{id}/scan-vin
```

Update VIN

POST

```
/vehicles/{id}/update-vin
```

VIN changes are always audited.

---

# 20. Photo Endpoints

## Order-scoped uploads (Sprint 6)

Upload

POST

```
/orders/{orderId}/vehicles/{vehicleId}/photos
```

List

GET

```
/orders/{orderId}/vehicles/{vehicleId}/photos
```

Delete

DELETE

```
/photos/{photoId}
```

Multipart fields: `file`, `photo_type`, optional `gps_latitude`, `gps_longitude`.

Photo types: `FRONT`, `REAR`, `LEFT`, `RIGHT`, `DAMAGE`, `INTERIOR`, `DOCUMENT`, `OTHER`.

## Legacy vehicle-scoped uploads

Upload

POST

```
/vehicles/{id}/photos
```

List

GET

```
/vehicles/{id}/photos
```

Uploads use multipart/form-data.

---

# 21. CMR and Order Documents

## Versioned order documents (Sprint 6)

Upload

POST

```
/orders/{orderId}/documents
```

List

GET

```
/orders/{orderId}/documents
```

Get by id

GET

```
/documents/{documentId}
```

Delete

DELETE

```
/documents/{documentId}
```

Uploading a new `CMR` creates a new version. Previous versions are retained.

Document types: `CMR`, `DELIVERY_NOTE`, `INSPECTION`, `CUSTOM`.

## Legacy CMR generation

Generate

POST

```
/orders/{id}/cmr/generate
```

Download

GET

```
/orders/{id}/cmr
```

Upload Signed Copy

POST

```
/orders/{id}/cmr/upload
```

---

# 21a. Vehicle Damage

Report damage

POST

```
/orders/{orderId}/vehicles/{vehicleId}/damage
```

List damage

GET

```
/orders/{orderId}/vehicles/{vehicleId}/damage
```

Update

PUT

```
/damage/{damageId}
```

Delete

DELETE

```
/damage/{damageId}
```

Damage reports may reference uploaded vehicle photo ids.

---

# 21b. Completion Checklist

Get checklist

GET

```
/orders/{orderId}/completion-checklist
```

Validate completion

POST

```
/orders/{orderId}/validate-completion
```

Returns completed items, missing items, completion percentage, and `can_complete`.

Order completion (`POST /orders/{id}/complete-delivery`) enforces checklist validation when the order would reach `COMPLETED`.

---

# 22. Timeline Endpoints

GET

```
/orders/{id}/timeline
```

Read-only.

Timeline entries are generated automatically by `app/order_timeline/` when orders, stops, vehicles, assignments, or statuses change.

Core event types:

* `ORDER_CREATED`
* `ORDER_UPDATED`
* `STATUS_CHANGED`
* `DRIVER_ASSIGNED`
* `STOP_ADDED`
* `STOP_REMOVED`
* `VEHICLE_ADDED`
* `VEHICLE_REMOVED`
* `DRIVER_ACCEPTED`
* `DRIVER_REJECTED`
* `ARRIVED_PICKUP`
* `LOADING_STARTED`
* `LOADING_COMPLETE`
* `TRANSIT_STARTED`
* `ARRIVED_DELIVERY`
* `DELIVERY_STARTED`
* `DELIVERY_COMPLETE`

---

# 23. AI Endpoints

Parse Customer Request

POST

```
/ai/parse-order
```

Suggest Driver

POST

```
/ai/suggest-driver
```

Suggest Loading

POST

```
/ai/suggest-loading
```

Suggest Route

POST

```
/ai/suggest-route
```

AI endpoints never modify business data.

---

# 24. Notification Endpoints

GET

```
/notifications
```

POST

```
/notifications/{id}/read
```

POST

```
/notifications/read-all
```

---

# 25. Search Endpoint

Global search

GET

```
/search
```

Searches:

* Orders
* Customers
* Drivers
* VIN
* Registration
* Order Number

One endpoint.

One search bar.

---

# 26. HTTP Status Codes

200

Success

201

Created

204

No Content

400

Bad Request

401

Unauthorized

403

Forbidden

404

Not Found

409

Conflict

422

Validation Error

500

Internal Server Error

---

# 27. Validation

Every request is validated.

Never trust client input.

Validation errors return structured responses.

---

# 28. Permissions

Every endpoint declares required roles.

Example

```
Admin

Dispatcher

Driver
```

Permission checks occur in the backend only.

---

# 29. API Documentation

Swagger

```
/docs
```

OpenAPI JSON

```
/openapi.json
```

Documentation is generated automatically from the code.

---

# 31a. Dispatcher Web Application

Sprint 7 frontend (`frontend/`) consumes this API via JWT.

Base URL in development: `http://localhost:5173` with Vite proxy to `/api/v1`.

Authentication flow:

1. `POST /auth/login`
2. Store access + refresh tokens
3. Attach `Authorization: Bearer` header
4. Refresh via `POST /auth/refresh` on 401

Driver role accounts are rejected by the dispatcher UI.

Primary screens:

* Operations board dashboard
* Orders list, detail, and creation
* Drivers and fleet management
* Customers and documents
* Notifications and admin settings

---

# 31b. Driver Mobile Application

Sprint 8 Flutter app (`driver_app/`) consumes this API via JWT for **driver role only**.

Base URL in development (Android emulator): `http://10.0.2.2:8000/api/v1`

Override at build time: `--dart-define=API_BASE_URL=https://your-host/api/v1`

Authentication flow:

1. `POST /auth/login`
2. Store access + refresh tokens in Flutter Secure Storage
3. Attach `Authorization: Bearer` header (Dio interceptor)
4. Refresh via `POST /auth/refresh` on 401; clear session if refresh fails

Primary driver endpoints:

* `GET /drivers/me/home` — dashboard payload
* `GET /drivers/me/current-order` — active execution context
* `GET /drivers/me/orders` — assigned orders
* Workflow POST actions under `/orders/{id}/…`
* Sprint 6 execution: VIN, photos, damage, documents, completion checklist

Offline behavior:

* Hive cache for home, current order, and orders list
* Hive queue for workflow, uploads, and damage submissions
* Automatic sync when connectivity returns

Dispatcher/admin accounts should use the web app; the mobile app is workflow-focused for assigned drivers.

---

# 32. Real-Time WebSocket API

Sprint 9 adds authenticated WebSocket connections for live operational visibility.

## Connect

```
WS /api/v1/ws?token={access_token}
```

Authentication uses the same JWT access token as REST.

## Client messages

```json
{"action":"ping"}
{"action":"subscribe","channel":"order","order_id":"..."}
{"action":"presence","status":"in_transit","active_order_id":"..."}
```

## Server events

JSON envelope:

```json
{
  "id": "uuid",
  "type": "ORDER_ASSIGNED",
  "company_id": "uuid",
  "channel": "dispatcher:uuid",
  "payload": { "order_id": "...", "order_number": "ORD-000001", "status": "ASSIGNED" },
  "severity": "info",
  "created_at": "2026-08-09T12:00:00+00:00"
}
```

Event types include workflow transitions, execution events (VIN, photos, damage, CMR/documents), `TIMELINE_ENTRY`, `NOTIFICATION_CREATED`, and presence updates.

Batched delivery:

```json
{"type":"BATCH","events":[...]}
```

## Channels

| Channel | Audience |
|---------|----------|
| `company:{company_id}` | All company users |
| `dispatcher:{company_id}` | Admin + dispatcher |
| `driver:{user_id}` | Assigned driver user |
| `order:{order_id}` | Order subscribers |
| `notifications:{user_id}` | Notification recipient |

## Presence REST

```
GET /api/v1/realtime/presence
```

Returns online users for the authenticated company (role, status, last seen, active order).

## Infrastructure

Events are published by domain services through `app.realtime.publisher` and distributed via Redis pub/sub (`prodrive:events:{company_id}`).

---

# 30. Versioning Rules

Breaking changes require:

New API version.

Non-breaking additions remain in the current version.

Deprecated endpoints remain available during migration periods.

---

# 31. Final Principle

The API represents business operations, not database tables.

Clients ask the backend to perform business actions.

The backend decides whether those actions are valid.
