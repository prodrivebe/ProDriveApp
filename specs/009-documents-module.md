# 009 — Documents Module

**Status:** Partial

## Feature Name

Photos, CMR generation, signed CMR upload.

## Business Goal

Replace paper CMR and damage photos with digital storage linked to orders and vehicles.

## Acceptance Criteria

- [x] Vehicle photo upload/list/delete (local storage)
- [x] Auto-generate CMR HTML per order
- [x] Upload signed CMR copy
- [ ] Bluetooth printing (client-side)
- [ ] PDF generation server-side

## Database Changes

`006_documents_schema` — `vehicle_photos`, `documents`

## API Endpoints

`/vehicles/{id}/photos`, `/orders/{id}/cmr/*`

## Tests Required

`tests/test_documents.py`

## Definition of Done

- [x] Backend complete
- [ ] Driver app upload UX complete
