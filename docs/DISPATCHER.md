# DISPATCHER.md

# ProDrive Dispatcher Dashboard

Version 1.0

---

# 1. Purpose

The Dispatcher Dashboard is the operational center of ProDrive.

Its purpose is to:

* Create transport orders
* Assign drivers
* Monitor fleet activity
* Communicate with drivers
* Manage customers
* Resolve operational issues

The dashboard should allow one dispatcher to efficiently manage a large fleet with minimal clicks.

---

# 2. Design Philosophy

The dashboard must be:

* Fast
* Clear
* Professional
* Information-rich
* Easy to scan
* Keyboard-friendly

The dispatcher should rarely need more than a few clicks to perform common actions.

---

# 3. Main Layout

```
Top Navigation

↓

Global Search

↓

Dashboard

↓

Left Navigation

↓

Content Area

↓

Right Information Panel (Contextual)
```

---

# 4. Left Navigation

Modules

Dashboard

Orders

Drivers

Fleet

Customers

Documents

Notifications

Reports

Settings

The menu should remain simple.

Additional features belong inside modules, not in the main navigation.

---

# 5. Dashboard Overview

The home dashboard shows today's operation.

Widgets

Active Orders

Drivers Online

Drivers Offline

Orders Waiting Assignment

Delayed Orders

Completed Today

AI Recommendations

Unread Notifications

The dispatcher immediately understands the company's current state.

---

# 6. Global Search

One search box.

Search everything.

Supported:

Order Number

VIN

Driver

Truck Registration

Trailer Registration

Customer

Company Name

City

Phone Number

Example

Typing

BMW

returns

Orders

Vehicles

Customers

Timeline entries

No module switching required.

---

# 7. Orders Module

Primary workspace.

Columns

Order Number

Customer

Pickup

Delivery

Driver

Status

Priority

Vehicle Count

Planned Pickup

Planned Delivery

Color-coded status.

Fast filtering.

Saved views.

---

# 8. Order Wizard

Creating an order should feel like a guided process.

Step 1

Customer

↓

Step 2

Paste customer message (optional)

↓

AI extracts:

Stops

Vehicles

VINs

Dates

↓

Dispatcher reviews

↓

Step 3

Assign Driver

↓

Step 4

Review

↓

Create Order

AI never creates an order automatically.

Dispatcher confirms every step.

---

# 9. Multi-Stop Support

One order may include:

Multiple pickup locations.

Multiple delivery locations.

The UI clearly groups vehicles under their pickup and delivery stops.

No duplicated addresses.

---

# 10. Vehicle Management

Each vehicle displays:

VIN

Make

Model

Color

Pickup Stop

Delivery Stop

Trailer Position

Photo Count

Damage Indicator

Status

Quick actions

View

Edit

Photos

Timeline

---

# 11. Driver Assignment

Dispatcher selects:

Driver

Truck

Trailer

Immediately display:

Current workload

Today's hours

Current location

Trailer capacity

Open conflicts

AI may recommend drivers based on proximity and availability.

Dispatcher always confirms.

---

# 12. Fleet Module

Manage

Drivers

Trucks

Trailers

Current assignments

Availability

Maintenance status

Future versions include GPS integration.

---

# 13. Driver Detail

Driver page shows:

Current Order

Today's Route

Truck

Trailer

Average Loading Time

Completed Orders

Recent Activity

Documents

Performance metrics are informative, not punitive.

---

# 14. Live Order Timeline

Every order displays a chronological timeline.

Examples

Order Created

Driver Assigned

Driver Accepted

Arrived Pickup

VIN Updated

Photos Uploaded

Loading Completed

Arrived Delivery

CMR Uploaded

Order Completed

Timeline is read-only.

Automatically generated.

---

# 15. Notifications

Receive alerts for:

Driver Accepted

Driver Rejected

Delayed Arrival

VIN Changed

Missing Photos

CMR Uploaded

Offline Driver

AI Recommendation

Notifications should support quick action where appropriate.

---

# 16. AI Assistant

AI may:

Extract order details

Suggest drivers

Suggest routes

Suggest loading plans

Detect missing information

Warn about conflicts

AI may not:

Assign drivers

Modify orders

Delete records

Complete workflows

All recommendations require dispatcher approval.

---

# 17. Smart Assignment

The dispatcher should see a recommendation panel.

Example

Suggested Driver

Distance to Pickup

Estimated Arrival

Current Workload

Trailer Compatibility

Recommendation Score

Dispatcher remains in control.

---

# 18. Loading Preview

Display a graphical trailer layout.

Upper Deck

Lower Deck

Vehicle positions

Loading order

Unloading order

Estimated transport height

Dispatcher may accept or edit.

---

# 19. Map View

Interactive map showing:

Drivers

Pickup Stops

Delivery Stops

Current Routes

Order Status

Filters

Driver

Region

Customer

Priority

Future:

Traffic

Weather

Road restrictions

---

# 20. Customer Module

Customer profile

Contacts

History

Orders

Documents

Preferred instructions

Average transport volume

Searchable.

---

# 21. Documents

Manage:

CMRs

Delivery Notes

Photos

Invoices (future)

Every document linked to its order.

---

# 22. Reports

Version 1

Completed Orders

Driver Activity

Fleet Utilization

Customer Activity

Future

Revenue

Profitability

Fuel

KPIs

---

# 23. Performance

Dashboard loads quickly.

Search responds almost instantly.

Pagination for large datasets.

Virtual scrolling for long tables.

Heavy reports generated asynchronously.

---

# 24. Keyboard Support

Common actions should be keyboard accessible.

Search

Esc

Close dialogs

Enter

Confirm

Arrow Keys

Navigate lists

Power users should work efficiently.

---

# 25. Permissions

Dispatcher

Orders

Drivers

Fleet

Customers

No company settings.

Admin

Full access.

Driver

No dashboard access.

---

# 26. Audit

Every important action records:

User

Timestamp

Action

Old Value

New Value

Reason (when applicable)

Audit history is searchable.

---

# 27. Future Modules

Planning Board

Calendar View

Customer Portal

Financial Dashboard

Maintenance

Fuel

OCR

Damage Detection

Business Intelligence

---

# 28. Definition of Success

A dispatcher should be able to:

Create an order

Assign a driver

Monitor progress

Resolve issues

Complete the transport

without opening another application.

---

# 29. Final Principle

The Dispatcher Dashboard should reduce cognitive load.

The software should present the right information at the right time.

The dispatcher should spend time making decisions, not searching for information.
