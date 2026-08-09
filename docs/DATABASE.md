# DATABASE.md

# ProDrive Database Design

Version 1.0

---

# 1. Database Philosophy

The database is the single source of truth.

Business logic belongs in the backend.

The database stores facts, not business rules.

---

# 2. Database Engine

Version 1

PostgreSQL 16+

Character Encoding

UTF-8

Timezone

UTC

UUID Support

Required

---

# 3. Naming Convention

Tables

snake_case

Columns

snake_case

Primary Keys

id

Foreign Keys

entity_id

Examples

company_id

driver_id

order_id

vehicle_id

---

# 4. Common Columns

Every business table includes:

```sql
id UUID PRIMARY KEY

company_id UUID NOT NULL

created_at TIMESTAMPTZ

updated_at TIMESTAMPTZ

created_by UUID

updated_by UUID

deleted_at TIMESTAMPTZ NULL
```

No hard deletes.

Soft delete only.

---

# 5. Multi-Tenant Rule

Every business entity belongs to exactly one company.

Every query MUST filter by:

company_id

No exceptions.

---

# 6. Core Tables

## companies

Stores tenant information.

Fields

* id
* name
* vat_number
* address
* country
* phone
* email
* logo_url
* subscription_plan
* created_at
* updated_at

---

## users

Application users.

Fields

* id
* company_id
* first_name
* last_name
* email
* password_hash
* role
* is_active
* last_login
* created_at

Roles

ADMIN

DISPATCHER

DRIVER

---

## drivers

Driver profile.

Separate from authentication.

Fields

* id
* company_id
* user_id
* phone
* driving_license
* adr_certificate
* notes
* active
* created_at
* updated_at
* deleted_at

---

## trucks

Fields

* id
* company_id
* registration_number
* brand
* model
* vin
* capacity
* active
* created_at
* updated_at
* deleted_at

---

## trailers

Fields

* id
* company_id
* registration_number
* manufacturer
* model
* trailer_type
* maximum_height
* maximum_weight
* maximum_vehicle_count
* active
* created_at
* updated_at
* deleted_at

---

## fleet_assignments

Standing assignment linking a driver, truck, and trailer.

Fields

* id
* company_id
* driver_id
* truck_id
* trailer_id
* assigned_at
* unassigned_at
* active

Constraints

* Only one active assignment per driver within a company
* Only one active assignment per truck within a company
* Only one active assignment per trailer within a company

---

## customers

Fields

* id
* company_id
* company_name
* vat_number
* address
* city
* country
* email
* phone
* notes

---

# 7. Orders

orders

Contains transport order header.

Fields

* id
* company_id
* customer_id
* order_number
* status
* assigned_driver_id
* assigned_truck_id
* assigned_trailer_id
* planned_pickup_date
* planned_delivery_date
* notes

Status

DRAFT

READY

ASSIGNED

ACCEPTED

LOADING

IN_TRANSIT

DELIVERING

COMPLETED

CANCELLED

---

# 8. Stops

order_stops

Purpose

Stores every pickup and delivery stop.

Fields

* id
* order_id
* stop_type
* sequence
* company_name
* contact_name
* phone
* address
* city
* postal_code
* country
* latitude
* longitude
* arrival_time
* departure_time

stop_type

PICKUP

DELIVERY

The sequence field determines route order.

---

# 9. Vehicles

order_vehicles

One record per transported vehicle.

Fields

* id
* order_id
* pickup_stop_id
* delivery_stop_id
* vin
* make
* model
* generation
* body_type
* color
* year
* fuel_type
* transmission
* running
* estimated_weight
* estimated_height
* notes

One order

↓

Many vehicles

---

# 10. Vehicle Photos

vehicle_photos

Fields

* id
* vehicle_id
* file_path
* photo_type
* uploaded_by
* uploaded_at
* gps_latitude
* gps_longitude

photo_type

FRONT

REAR

LEFT

RIGHT

INTERIOR

DAMAGE

DOCUMENT

CUSTOM

---

# 11. Trailer Loading

loading_positions

Purpose

Stores suggested and actual trailer positions.

Fields

* id
* vehicle_id
* trailer_position
* upper_deck
* loading_order
* unloading_order
* ai_generated
* confirmed_by_dispatcher

Allows AI optimization while preserving manual overrides.

---

# 12. Documents

documents

Fields

* id
* company_id
* order_id
* document_type
* file_path
* generated_at
* generated_by

document_type

CMR

INVOICE

DELIVERY_NOTE

PHOTO_ARCHIVE

---

# 13. Notifications

notifications

Fields

* id
* company_id
* user_id
* title
* message
* type
* read_at
* created_at

---

# 14. Audit Log

audit_logs

One of the most important tables.

Fields

* id
* company_id
* user_id
* entity
* entity_id
* action
* old_value
* new_value
* ip_address
* created_at

Nothing important happens without audit.

---

# 15. AI Suggestions

ai_suggestions

Purpose

Store AI recommendations.

Fields

* id
* order_id
* suggestion_type
* input
* output
* approved
* approved_by
* approved_at

Never execute automatically.

---

# 16. Timeline

order_timeline

Every important order event.

Examples

* Order Created (`ORDER_CREATED`)
* Order Updated (`ORDER_UPDATED`)
* Status Changed (`STATUS_CHANGED`)
* Driver Assigned (`DRIVER_ASSIGNED`)
* Stop Added (`STOP_ADDED`)
* Stop Removed (`STOP_REMOVED`)
* Vehicle Added (`VEHICLE_ADDED`)
* Vehicle Removed (`VEHICLE_REMOVED`)

Additional workflow events (driver accept, pickup, delivery, VIN, photos, CMR) are recorded by their respective modules.

Timeline logic lives in `app/order_timeline/`. Stop and vehicle mutations are handled in `app/order_stops/` and `app/order_vehicles/`.

This timeline powers the dispatcher view.

---

# 17. Relationships

Company

↓

Users

↓

Drivers

↓

Orders

↓

Stops

↓

Vehicles

↓

Photos

Simple hierarchy.

---

# 18. Index Strategy

Indexes on:

company_id

status

order_number

vin

registration_number

customer_id

driver_id

created_at

Avoid full table scans.

---

# 19. Constraints

VIN unique per active vehicle record where appropriate.

Order numbers unique within company.

Registration numbers unique within company.

Email unique within company.

---

# 20. Migrations

All schema changes use Alembic.

Never modify production tables manually.

Every schema change must be reversible.

---

# 21. Backup Strategy

Daily backups.

Point-in-time recovery enabled.

Retain backups for at least 30 days.

Backups encrypted.

---

# 22. Future Tables

Reserved for Version 2+

fuel_logs

maintenance

expenses

invoices

payments

customer_portal_users

gps_tracking

damage_reports

ocr_jobs

analytics_events

Keeping these separate avoids breaking Version 1.

---

# 23. Database Rules

Never duplicate addresses unnecessarily.

Never duplicate customer information.

Normalize until there is a measurable performance reason not to.

Business logic belongs in services, not triggers.

Triggers should be used sparingly.

---

# 24. Definition of a Good Schema

A good schema is:

Consistent.

Normalized.

Easy to query.

Easy to extend.

Safe for multi-tenant SaaS.

Designed for millions of records.

Readable by future developers.
