# PROJECT.md

# ProDrive Project Specification

**Project Name:** ProDrive

**Version:** 1.0 (In Development)

**Slogan:** Drive smarter. Deliver better.

---

# 1. Executive Summary

ProDrive is a commercial SaaS platform built specifically for professional vehicle transport companies (auto transporters).

The platform replaces fragmented workflows based on spreadsheets, WhatsApp, phone calls and handwritten paperwork with a modern cloud-based platform.

The first release focuses on Android drivers, dispatchers and AI-assisted order management.

The long-term vision is to become the leading vehicle transport management platform in Europe.

---

# 2. Mission

Build the fastest, simplest and most reliable platform for managing vehicle transportation.

Every feature must satisfy at least one of these goals:

* Reduce dispatcher workload.
* Reduce driver mistakes.
* Reduce empty kilometers.
* Improve communication.
* Reduce paperwork.
* Improve transport visibility.
* Save time.

If a feature does not provide measurable value, it should not be implemented.

---

# 3. Product Vision

The application must allow a transport company to complete an entire transport job digitally.

Workflow:

Customer

↓

Dispatcher

↓

Driver

↓

Pickup

↓

Transport

↓

Delivery

↓

Completed

No paper should be required except where legally necessary.

---

# 4. Target Users

## Company Administrator

Responsibilities

* Company settings
* User management
* Subscription
* Branding
* Reports
* Security
* Fleet overview

---

## Dispatcher

Responsibilities

* Receive customer requests
* Create orders
* Review AI extraction
* Assign drivers
* Monitor transport
* Manage customers
* Solve operational issues

Dispatcher always has final authority.

---

## Driver

Responsibilities

* Accept assigned order
* Navigate to pickup
* Verify vehicles
* Scan VIN
* Capture required photos
* Print CMR
* Deliver vehicles
* Upload delivery proof

Drivers should never be required to manage business administration.

---

# 5. Product Philosophy

ProDrive is not a generic logistics platform.

It is purpose-built for vehicle transport companies.

Every workflow should match real transport operations.

The system should reduce complexity instead of adding it.

---

# 6. Core Principles

## Simplicity

Drivers should always know the next action.

Maximum three taps for common operations.

No unnecessary menus.

No hidden functionality.

---

## Performance

Application launch

Target:

Less than two seconds.

Screen transitions

Target:

Less than 300 milliseconds.

Photo uploads must happen in the background.

Offline actions must execute instantly.

---

## Reliability

No user action should ever disappear.

Every important action is stored.

Every important change is auditable.

---

## Safety

Nothing important is permanently deleted.

Soft delete only.

Every critical operation requires confirmation.

---

# 7. AI Philosophy

Artificial Intelligence is an assistant.

It never replaces operational decisions.

AI may:

* Read customer messages.
* Extract structured information.
* Suggest drivers.
* Suggest routes.
* Suggest trailer loading.
* Detect missing information.
* Detect inconsistencies.
* Recommend improvements.

AI may never:

* Assign drivers automatically.
* Delete data.
* Modify business records without approval.
* Complete an order.
* Change VIN numbers automatically.
* Send customer communications automatically.

Every important AI suggestion requires dispatcher approval.

---

# 8. Driver Experience

The driver application must remain intentionally simple.

The driver always sees one primary action.

Example workflow:

Login

↓

Today's Job

↓

Navigate

↓

Arrived

↓

Scan VIN

↓

Take Photos

↓

Finish Loading

↓

Print CMR

↓

Navigate

↓

Arrived

↓

Upload Signed CMR

↓

Finish Order

The driver should never need to search through menus.

---

# 9. Dispatcher Experience

Dispatcher workflow:

Receive customer request

↓

Paste email or message

↓

AI extraction

↓

Review

↓

Assign driver

↓

Create order

↓

Monitor progress

↓

Receive completion notification

Dispatcher always maintains full control.

---

# 10. Orders

Every order consists of:

Order

↓

Pickup Stops

↓

Delivery Stops

↓

Vehicles

Version 1 supports:

Maximum 10 vehicles.

Unlimited pickup stops.

Unlimited delivery stops.

Vehicles reference pickup and delivery stops instead of duplicating address information.

---

# 11. Vehicle Information

Each vehicle stores:

* VIN
* Make
* Model
* Year
* Colour
* Running status
* Lot number
* Stock number
* Pickup stop
* Delivery stop
* Trailer position
* Notes
* Photos

VIN changes are permitted only by the driver during pickup.

Every VIN change is permanently recorded.

---

# 12. Fleet

Entities:

Driver

Truck

Trailer

Drivers are dynamically assigned to trucks and trailers.

Trailer capacities:

* 2 vehicles
* 3 vehicles
* 5 vehicles
* 8 vehicles
* 10 vehicles

Future versions may support custom trailer configurations.

---

# 13. Smart Loading

AI calculates recommended loading positions using:

* Pickup sequence
* Delivery sequence
* Vehicle dimensions
* Estimated vehicle weight
* Trailer capacity
* Legal transport height

Primary goals:

* Minimize unnecessary unloading.
* Keep total transport height below legal limits.
* Maintain balanced trailer loading.

Recommendations may always be overridden by the driver or dispatcher.

---

# 14. CMR

CMR documents are generated automatically.

Information included:

* Company details
* Customer
* Pickup addresses
* Delivery addresses
* Driver
* Truck
* Trailer
* Vehicle list
* VIN list

Driver prints rather than handwriting.

---

# 15. Offline Operation

Driver application must remain fully usable without internet.

Offline capabilities include:

* Order viewing
* VIN verification
* Photo capture
* Status updates
* Delivery confirmation

Synchronization occurs automatically when connectivity returns.

No user action should ever be lost.

---

# 16. Security

Authentication:

JWT

Authorization:

Role-based

Multi-tenancy:

Every business entity belongs to exactly one company.

No company may access another company's information.

Every important operation is audited.

Passwords are never stored in plain text.

---

# 17. User Interface

Design language:

* Modern
* Minimal
* Professional
* Mercedes-inspired
* Soft colours
* Rounded corners
* Large buttons
* High readability

Animations should be subtle and fast.

---

# 18. Future Roadmap

Planned future modules:

* Customer Portal
* Live Customer Tracking
* OCR
* Automatic Invoice Generation
* Damage Detection
* Fleet Maintenance
* Fuel Management
* Driver Hours
* Financial Analytics
* Profitability Analysis
* AI Operations Dashboard
* Multi-language Support

These modules are not part of Version 1.

---

# 19. Definition of Success

Version 1 is successful when a transport company can complete an entire transport job using only ProDrive.

Success criteria:

* Dispatcher creates an order.
* Driver receives the order.
* Driver completes pickup.
* Driver prints the CMR.
* Driver completes delivery.
* Dispatcher receives completion notification.
* All documents are stored digitally.
* No paper workflow is required during daily operations.

---

# 20. Guiding Principle

Every design decision should answer one question:

**Does this make the dispatcher's work faster or the driver's work simpler?**

If the answer is no, the feature should be reconsidered.
