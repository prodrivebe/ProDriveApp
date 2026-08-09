import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/sync_service.dart';
import '../../../core/network/dio_provider.dart';

final offlineQueueProvider = Provider<OfflineQueueRepository>((ref) {
  return OfflineQueueRepository();
});

final syncServiceProvider = Provider<SyncService>((ref) {
  return SyncService(ref.watch(dioProvider), ref.watch(offlineQueueProvider));
});

final syncTickProvider = StateProvider<int>((ref) => 0);

final pendingQueueCountProvider = FutureProvider<int>((ref) async {
  ref.watch(syncTickProvider);
  final pending = await ref.read(offlineQueueProvider).pending();
  return pending.length;
});

final syncControllerProvider = Provider<SyncController>((ref) => SyncController(ref));

class SyncController {
  SyncController(this._ref);

  final Ref _ref;

  Future<int> syncIfOnline() async {
    final synced = await _ref.read(syncServiceProvider).syncPending();
    _ref.read(syncTickProvider.notifier).state++;
    return synced;
  }
}
