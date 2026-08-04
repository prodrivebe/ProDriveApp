# ProDrive Driver App

Flutter Android client for ProDrive drivers.

## Features (v1)

- Email/password login
- Home screen with next action
- Assigned orders list and detail
- Workflow actions (accept, arrive, complete loading/delivery)
- VIN scan entry, photo upload, signed CMR upload
- Offline queue stub (sync when online)
- In-app notifications list

## Setup

```bash
cd driver_app
flutter pub get
flutter run
```

Configure API base URL in `lib/config/api_config.dart` (default: `http://10.0.2.2:8000/api/v1` for Android emulator).

## Dev credentials

Use a driver user created in the backend (e.g. via admin panel or seed).
