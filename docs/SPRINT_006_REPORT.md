# Sprint 6 Report — Vehicle Execution and Evidence

**Date:** 2026-08-09  
**Scope:** Backend vehicle execution, VIN verification, photos, damage, documents, completion checklist (no Flutter UI, no AI, no OCR)

---

## Implemented Features

### VIN verification (`app/vin_verification/`)

* Order-scoped verify, update, and history endpoints
* VIN format validation via shared `normalize_vin`
* Immutable append-only `vin_verification_history`
* Original and verified VIN stored on `order_vehicles`
* Timeline, audit, and staff notifications on VIN change

### Vehicle photos (`app/vehicle_photos/`)

* Order-scoped upload and list endpoints
* Global delete by photo id
* File type and size validation
* Unique filenames via UUID
* Metadata, file name, size, and content type persisted
* Timeline and audit on upload/delete
* Local storage via `LocalFileStorage.save_vehicle_photo()`

### Vehicle damage (`app/vehicle_damage/`)

* Create, list, update, and soft-delete damage reports
* Photo attachment through `vehicle_damage_photos`
* Timeline, audit, and staff notifications on report

### Order documents (`app/order_documents/`)

* Versioned uploads per document type
* CMR uploads create new versions without deleting prior versions
* File type and size validation on upload
* Timeline, audit, and CMR upload notifications

### Completion checklist (`app/completion_checklist/`)

* Dynamic checklist computation from stops, vehicles, photos, documents, and damage
* Persisted snapshot in `order_completion_checklist`
* Validation endpoint with completed/missing items and percentage
* `complete-delivery` enforces checklist when order reaches `COMPLETED`

---

## Database Changes

Migration: `011_sprint6_execution_schema`

| Change | Details |
|--------|---------|
| `order_vehicles` | Added `original_vin`, `verified_vin`, `vin_verified_at`, `vin_verified_by` |
| `vehicle_photos` | Added `order_id`, `file_name`, `file_size`, `content_type`, `metadata` |
| `vin_verification_history` | New append-only table |
| `vehicle_damage` | New table with soft delete |
| `vehicle_damage_photos` | Junction table for damage photo links |
| `order_documents` | New versioned document table |
| `order_completion_checklist` | New persisted checklist table |

---

## API Endpoints

| Method | Path | Actor |
|--------|------|-------|
| POST | `/api/v1/orders/{orderId}/vehicles/{vehicleId}/verify-vin` | Driver (assigned), dispatcher, admin |
| PUT | `/api/v1/orders/{orderId}/vehicles/{vehicleId}/vin` | Driver (assigned), dispatcher, admin |
| GET | `/api/v1/orders/{orderId}/vehicles/{vehicleId}/vin-history` | Driver (assigned), dispatcher, admin |
| POST | `/api/v1/orders/{orderId}/vehicles/{vehicleId}/photos` | Driver (assigned), dispatcher, admin |
| GET | `/api/v1/orders/{orderId}/vehicles/{vehicleId}/photos` | Driver (assigned), dispatcher, admin |
| DELETE | `/api/v1/photos/{photoId}` | Dispatcher, admin |
| POST | `/api/v1/orders/{orderId}/vehicles/{vehicleId}/damage` | Driver (assigned), dispatcher, admin |
| GET | `/api/v1/orders/{orderId}/vehicles/{vehicleId}/damage` | Driver (assigned), dispatcher, admin |
| PUT | `/api/v1/damage/{damageId}` | Dispatcher, admin |
| DELETE | `/api/v1/damage/{damageId}` | Dispatcher, admin |
| POST | `/api/v1/orders/{orderId}/documents` | Driver (assigned), dispatcher, admin |
| GET | `/api/v1/orders/{orderId}/documents` | Driver (assigned), dispatcher, admin |
| GET | `/api/v1/documents/{documentId}` | Driver (assigned), dispatcher, admin |
| DELETE | `/api/v1/documents/{documentId}` | Dispatcher, admin |
| GET | `/api/v1/orders/{orderId}/completion-checklist` | Driver (assigned), dispatcher, admin |
| POST | `/api/v1/orders/{orderId}/validate-completion` | Driver (assigned), dispatcher, admin |

Legacy `/vehicles/{id}/photos` and `/orders/{id}/cmr/*` endpoints remain for backward compatibility.

---

## Test Results

Test suite: `backend/tests/test_execution_sprint6.py`

Coverage targets:

* VIN verification and immutable history
* Invalid VIN rejection
* Photo upload validation and delete
* Damage CRUD with photo attachment
* CMR document versioning
* Completion checklist and enforced order completion
* Permission checks for unassigned drivers
* Cross-company isolation (404)

**Note:** Python and Docker were unavailable in the CI agent environment during this session. Run locally:

```bash
cd backend
alembic upgrade head
pytest tests/test_execution_sprint6.py tests/test_workflow_sprint5.py -q
ruff check app tests
mypy app
docker compose up --build
```

---

## Storage Architecture

* `app/common/storage/protocol.py` defines a `FileStorage` protocol for future S3 replacement
* `app/common/storage/local.py` implements local filesystem storage under `upload_root_dir`
* Vehicle photos: `companies/{companyId}/orders/{orderId}/vehicles/{vehicleId}/{uuid}.{ext}`
* Order documents: `companies/{companyId}/orders/{orderId}/{filename}`
* Files served via `/uploads` static mount

---

## Known Limitations

* Cloud object storage (S3) not implemented; local paths only
* Legacy CMR module (`app/cmr/`) still uses the older `documents` table alongside new `order_documents`
* Legacy vehicle-scoped photo routes do not populate all Sprint 6 metadata fields
* OCR and AI VIN scanning remain out of scope
* Checklist photo requirements depend on `company_settings.require_vehicle_photos` (default: true)

---

## Recommendations for Sprint 7

1. Add S3-backed storage implementing `FileStorage`
2. Consolidate legacy CMR and photo routes into order-scoped modules
3. Add driver Flutter UI for VIN entry, photo capture, damage reporting, and CMR upload
4. Wire push notification delivery (FCM) for execution events
5. Add OCR-assisted VIN capture as optional enhancement behind feature flag
6. Extend completion checklist rules per customer or order type templates
