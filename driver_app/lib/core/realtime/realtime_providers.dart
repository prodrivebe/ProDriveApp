import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/notifications/providers/notifications_providers.dart';
import '../../features/orders/providers/orders_providers.dart';
import '../../features/sync/providers/sync_providers.dart';
import '../network/dio_provider.dart';
import '../storage/secure_token_storage.dart';
import 'realtime_client.dart';

final realtimeClientProvider = Provider<RealtimeClient>((ref) {
  final storage = ref.watch(secureTokenStorageProvider);
  return RealtimeClient(storage);
});

final realtimeBootstrapProvider = Provider<void>((ref) {
  final client = ref.watch(realtimeClientProvider);

  client.addListener((event) {
    final type = event['type'] as String? ?? '';
    if (type.startsWith('ORDER_') ||
        type.contains('LOADING') ||
        type.contains('TRANSIT') ||
        type.contains('DELIVERY') ||
        type == 'TIMELINE_ENTRY') {
      ref.invalidate(driverHomeProvider);
      ref.invalidate(currentOrderProvider);
      ref.invalidate(driverOrdersProvider);
      ref.read(syncTickProvider.notifier).state++;
      final payload = event['payload'];
      final orderId = payload is Map ? payload['order_id'] as String? : null;
      if (orderId != null) {
        ref.invalidate(orderDetailProvider(orderId));
        ref.invalidate(orderTimelineProvider(orderId));
        ref.invalidate(orderChecklistProvider(orderId));
      }
    }
    if (type == 'NOTIFICATION_CREATED') {
      ref.invalidate(notificationsProvider);
    }
  });

  ref.onDispose(() {
    client.disconnect();
  });
});

final realtimeControllerProvider = Provider<RealtimeController>((ref) {
  ref.watch(realtimeBootstrapProvider);
  return RealtimeController(ref);
});

class RealtimeController {
  RealtimeController(this._ref);

  final Ref _ref;

  Future<void> connect() async {
    await _ref.read(realtimeClientProvider).connect();
  }

  Future<void> disconnect() async {
    await _ref.read(realtimeClientProvider).disconnect();
  }
}
