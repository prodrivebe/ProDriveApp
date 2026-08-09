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

Complete Loading

POST

```
/orders/{id}/complete-loading
```

Arrive Delivery

POST

```
/orders/{id}/arrive-delivery
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

Workflow actions are preferred over generic status updates.

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

CRUD implemented in `app/order_vehicles/`. VIN endpoints remain under the same `/vehicles` prefix.

---

# 19. VIN Endpoints

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

Delete

DELETE

```
/photos/{id}
```

Uploads use multipart/form-data.

---

# 21. CMR Endpoints

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
