# ProDrive Driver App

Flutter Android client for ProDrive drivers (Sprint 8).

## Stack

- Flutter / Material 3
- Riverpod (state management)
- Dio (HTTP + token refresh interceptor)
- GoRouter (navigation)
- Hive (operational cache + offline queue)
- Flutter Secure Storage (JWT tokens)
- Image Picker / Camera (photo capture)
- Connectivity Plus (online/offline detection)

## Features

- Email/password login with secure token storage and automatic refresh
- Home screen: current order, next action, truck/trailer, primary workflow button
- Assigned orders list, order detail, stops, vehicles, timeline, completion checklist
- Full driver workflow: accept/reject, pickup, loading, transit, delivery
- Vehicle execution: manual VIN verification, photo capture, damage reporting, CMR upload
- Offline-first: cache home/current order/orders; queue workflow, photos, documents, damage, VIN
- Auto-sync when connectivity returns
- Profile and in-app notifications

## Project layout

```text
lib/
  core/          config, network, storage, router, theme, connectivity
  features/      auth, home, orders, vehicles, photos, documents, profile, notifications, sync
  shared/        models, widgets
```

## Setup

```bash
cd driver_app
flutter pub get
flutter test
flutter run
```

### API base URL

Default (Android emulator → host machine):

```dart
// lib/core/config/api_config.dart
http://10.0.2.2:8000/api/v1
```

Override at build time:

```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000/api/v1
```

## Dev credentials

Use a driver account from the backend seed or admin panel. Dispatcher/admin roles are intended for the web app only.

## Tests

```bash
flutter test
```

Covers workflow mapping, offline queue, synchronization, upload queueing, auth models, API error messages, and login UI.

## Out of scope (Sprint 8)

- AI features
- OCR / VIN camera scanning
- GPS tracking

See `docs/SPRINT_008_REPORT.md` for implementation details.
