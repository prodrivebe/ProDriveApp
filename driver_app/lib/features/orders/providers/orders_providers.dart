import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/connectivity/connectivity_service.dart';
import '../../../core/network/dio_provider.dart';
import '../../../shared/models/order_models.dart';
import '../../sync/data/sync_service.dart';
import '../../sync/providers/sync_providers.dart';
import '../data/orders_repository.dart';
import '../domain/workflow_actions.dart';

final cacheRepositoryProvider = Provider<CacheRepository>((ref) => CacheRepository());

final driverApiRepositoryProvider = Provider<DriverApiRepository>((ref) {
  return DriverApiRepository(ref.watch(dioProvider), ref.watch(cacheRepositoryProvider));
});

final driverHomeProvider = FutureProvider<DriverHome>((ref) async {
  ref.watch(syncTickProvider);
  return ref.read(driverApiRepositoryProvider).fetchHome();
});

final currentOrderProvider = FutureProvider<DriverCurrentOrder>((ref) async {
  ref.watch(syncTickProvider);
  return ref.read(driverApiRepositoryProvider).fetchCurrentOrder();
});

final driverOrdersProvider = FutureProvider<List<OrderSummary>>((ref) async {
  ref.watch(syncTickProvider);
  return ref.read(driverApiRepositoryProvider).fetchOrders();
});

final orderDetailProvider = FutureProvider.family<OrderDetail, String>((ref, orderId) async {
  return ref.read(driverApiRepositoryProvider).fetchOrder(orderId);
});

final orderTimelineProvider =
    FutureProvider.family<List<TimelineEntry>, String>((ref, orderId) async {
  return ref.read(driverApiRepositoryProvider).fetchTimeline(orderId);
});

final orderChecklistProvider =
    FutureProvider.family<CompletionChecklist, String>((ref, orderId) async {
  return ref.read(driverApiRepositoryProvider).fetchChecklist(orderId);
});

final workflowControllerProvider =
    Provider<WorkflowController>((ref) => WorkflowController(ref));

class WorkflowController {
  WorkflowController(this._ref);

  final Ref _ref;

  Future<void> execute(String orderId, String status, {required bool online}) async {
    final action = primaryWorkflowAction(status);
    if (action == null) return;

    if (!online) {
      await _ref.read(offlineQueueProvider).enqueue(
            QueuedOperation(
              id: '$orderId-${action.endpoint}-${DateTime.now().millisecondsSinceEpoch}',
              type: 'workflow',
              path: '/orders/$orderId/${action.endpoint}',
            ),
          );
      _ref.invalidate(syncTickProvider);
      return;
    }

    try {
      await _ref.read(driverApiRepositoryProvider).workflowAction(orderId, action.endpoint);
      _ref.invalidate(driverHomeProvider);
      _ref.invalidate(currentOrderProvider);
      _ref.invalidate(driverOrdersProvider);
      _ref.invalidate(orderDetailProvider(orderId));
    } on ApiException {
      rethrow;
    }
  }

  Future<void> reject(String orderId, {required bool online}) async {
    if (!online) {
      await _ref.read(offlineQueueProvider).enqueue(
            QueuedOperation(
              id: '$orderId-reject-${DateTime.now().millisecondsSinceEpoch}',
              type: 'workflow',
              path: '/orders/$orderId/reject',
            ),
          );
      return;
    }
    await _ref.read(driverApiRepositoryProvider).workflowAction(orderId, 'reject');
    _ref.invalidate(driverHomeProvider);
    _ref.invalidate(driverOrdersProvider);
    _ref.read(syncTickProvider.notifier).state++;
  }
}
