# Sprint 8 Report — Flutter Driver Application

Date: 2026-08-09

## Summary

Sprint 8 delivers the operational Flutter driver application in `driver_app/`, connected to the backend implemented in Sprints 1–7. The app is offline-first, workflow-driven, and aligned with `docs/DRIVER_APP.md`.

## Implemented screens

| Screen | Route | Description |
|--------|-------|-------------|
| Login | `/login` | Email/password authentication |
| Home | `/home` | Current order, next action, truck/trailer, primary workflow CTA |
| Orders | `/orders` | Active and historical assigned orders |
| Order detail | `/orders/:orderId` | Stops, vehicles, timeline, checklist, workflow + CMR entry |
| Vehicle detail | `/orders/:orderId/vehicles/:vehicleId` | VIN status, photo/damage counts, execution shortcuts |
| VIN verification | `.../vin` | Manual VIN confirm/edit + history |
| Photo capture | `.../photos` | Camera/gallery, type selection, upload queue |
| Damage report | `.../damage` | Severity, location, description |
| CMR upload | `/orders/:orderId/documents/cmr` | Capture/select CMR image |
| Notifications | `/notifications` | In-app alerts, mark read |
| Profile | `/profile` | User/driver info, sync now, logout |

Bottom navigation: Home, Orders, Alerts, Profile.

## Backend integration

| Area | Endpoints |
|------|-----------|
| Auth | `POST /auth/login`, `/auth/refresh`, `/auth/logout`, `GET /auth/me` |
| Driver | `GET /drivers/me`, `/drivers/me/home`, `/drivers/me/current-order`, `/drivers/me/orders` |
| Orders | `GET /orders/{id}`, `/orders/{id}/timeline`, `/orders/{id}/completion-checklist` |
| Workflow | `POST /orders/{id}/accept`, `reject`, `arrive-pickup`, `start-loading`, `complete-loading`, `start-transit`, `arrive-delivery`, `start-delivery`, `complete-delivery` |
| Execution | VIN verify/update/history, vehicle photos, damage, order documents (CMR) |
| Notifications | `GET /notifications`, `POST /notifications/{id}/read` |

Dio interceptor attaches JWT, refreshes on 401, clears session if refresh fails.

## Offline architecture

**Hive boxes**

- `operational_cache` — home, current order, orders list
- `offline_queue` — pending mutations

**Cached when online**

- Driver home payload
- Current order context (stops, vehicles, next action)
- Assigned orders list

**Queued when offline**

- Workflow POST actions
- Photo uploads (multipart)
- CMR/document uploads
- Damage reports (JSON body)
- VIN verify/update

## Synchronization strategy

1. `ConnectivityService` exposes `isOnlineProvider`.
2. Workflow/upload controllers enqueue to Hive when offline.
3. `SyncService.syncPending()` replays queue FIFO via Dio.
4. On connectivity restore, `BootstrapApp` triggers sync and bumps `syncTickProvider` to refresh UI providers.
5. Profile screen offers manual **Sync now**.

Failed sync leaves items in queue for retry; network errors surface user-friendly `ApiException` messages.

## State management (Riverpod)

| Provider domain | Responsibility |
|-----------------|----------------|
| `authControllerProvider` | Login/logout/session bootstrap |
| `driverHomeProvider` / `currentOrderProvider` | Operational dashboard |
| `workflowControllerProvider` | Workflow + offline queue |
| `uploadControllerProvider` | Photos, documents, VIN, damage |
| `syncControllerProvider` | Queue replay |
| `isOnlineProvider` | Connectivity |

## Test results

Test suite under `driver_app/test/`:

- `workflow_actions_test.dart`
- `offline_queue_test.dart`
- `sync_service_test.dart`
- `upload_controller_test.dart`
- `auth_repository_test.dart` (auth models/tokens)
- `api_exception_test.dart`
- `navigation_test.dart` (login UI)

**Note:** Flutter SDK was not available in the CI/agent environment during implementation. Run locally:

```bash
cd driver_app && flutter pub get && flutter test && flutter build apk
```

## Known limitations

- No OCR/VIN camera scanning (manual entry only, per sprint scope)
- No GPS tracking or turn-by-turn navigation integration
- No AI-assisted actions
- Photo upload progress is binary (no chunked progress events from Dio stub)
- Order detail is not cached offline (home/current order/orders list are)
- Freezed/codegen listed in stack; models are hand-written immutable classes for Sprint 8 velocity (Json Serializable/Freezed can be adopted incrementally)

## Recommendations for Sprint 9

1. Add push notifications (FCM) with device registration endpoint
2. Cache order detail + checklist for full offline read
3. Ordered composite queue entries (photo batch → damage with photo IDs)
4. Biometric unlock for returning drivers
5. Bluetooth CMR printing
6. Widget/integration tests with mocked Dio adapter
7. Generate Freezed models from OpenAPI or shared schema

## Definition of Done checklist

- [x] Login + secure token storage + refresh handling
- [x] Assigned orders + workflow actions
- [x] VIN verification (manual)
- [x] Photo capture + upload queue
- [x] Damage reporting
- [x] CMR upload
- [x] Offline queue + sync on reconnect
- [x] Tests authored
- [x] Documentation updated
- [ ] `flutter test` / `flutter build apk` verified locally (requires Flutter SDK on developer machine)
