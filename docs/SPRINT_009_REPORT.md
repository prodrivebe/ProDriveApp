# Sprint 9 Report — Real-Time Operations and Dispatch Visibility

Date: 2026-08-09

## Summary

Sprint 9 adds authenticated WebSocket infrastructure with Redis pub/sub, live Operations Board updates for dispatchers, real-time notification delivery, timeline streaming, and driver app synchronization.

## WebSocket architecture

```text
Business Service
      │ publish domain event
      ▼
EventService (batch + Redis publish)
      ▼
Redis channel prodrive:events:{company_id}
      ▼
RedisEventBridge subscriber thread
      ▼
ConnectionManager → WebSocket clients
```

Modules under `backend/app/realtime/`:

| Module | Responsibility |
|--------|----------------|
| `connection_manager.py` | Authenticated connections, channel subscriptions, heartbeat cleanup |
| `event_service.py` | Event batching, lifecycle, in-memory fallback for tests |
| `redis_events.py` | Redis pub/sub bridge |
| `publisher.py` | Domain event helpers (business services call these only) |
| `presence.py` | Online user tracking in Redis |
| `websocket_routes.py` | `/api/v1/ws` endpoint |
| `routes.py` | `GET /api/v1/realtime/presence` |

## Event model

Logical channels: `company`, `dispatcher`, `driver`, `order`, `notifications`.

Event types include order workflow transitions, execution events (VIN, photos, damage, CMR/documents), timeline entries, notifications, and presence updates.

Payloads include `order_id`, `order_number`, `status`, and type-specific metadata.

## Connection strategy

* JWT access token passed as `?token=` query parameter
* Default subscriptions based on role (company + notifications; dispatcher/admin also dispatcher channel; drivers also driver channel)
* Clients may subscribe to `order:{id}` dynamically
* Ping/pong heartbeat every 25–30 seconds
* Stale connections cleaned after 90 seconds
* Automatic reconnect with exponential backoff (React + Flutter)

## Frontend integration

* `RealtimeClient` + `RealtimeProvider` in `frontend/`
* TanStack Query cache invalidation on events
* Live Operations Board kanban columns on dashboard
* Connection status chip in main layout
* Order detail auto-subscribes to order channel
* Notification bell updates in real time

## Flutter integration

* `RealtimeClient` using `web_socket_channel`
* Riverpod controller connects after authentication
* Invalidates home/current order/detail/timeline/checklist providers on workflow events

## Performance considerations

* 50ms event batching before Redis publish
* Company-scoped Redis channels for isolation
* Max 5 websocket connections per user
* Background stale connection cleanup every 60 seconds

## Security

* JWT authentication on connect
* Company isolation enforced on delivery
* Role-based default channel subscriptions
* Connection count limiting

## Test results

Backend: `backend/tests/test_realtime_sprint9.py`

* WebSocket authentication
* Event delivery to connected client
* Company isolation
* Presence endpoint
* Event service initialization

Frontend: `frontend/src/services/realtimeClient.test.ts`

Flutter: `driver_app/test/realtime_client_test.ts`

Run locally:

```bash
cd backend && pytest tests/test_realtime_sprint9.py
cd frontend && npm test
cd driver_app && flutter test
docker compose up --build
```

## Known limitations

* No GPS/live map tracking (deferred)
* No AI/route optimization events
* Single-region Redis pub/sub (no cross-region fan-out)
* Notification payloads do not yet persist `order_id` in DB (client uses event payload when available)
* Batch websocket frames use simple JSON envelope (not binary)

## Recommendations for Sprint 10

1. Persist `order_id` on notifications for deep linking
2. Add SSE fallback for restrictive networks
3. Metrics dashboard for connection counts and event throughput
4. GPS location events when tracking sprint begins
5. Push notification bridge from realtime events to FCM/APNs

## Definition of Done

- [x] WebSocket authentication
- [x] Dispatcher live Operations Board
- [x] Driver live updates (Flutter)
- [x] Real-time notifications and timeline invalidation
- [x] Company isolation
- [x] Reconnect logic (React + Flutter)
- [x] Tests authored
- [x] Documentation updated
- [ ] Full test suite verified in local environment with Redis running
