import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/connectivity/connectivity_service.dart';
import '../../../core/network/api_exception.dart';
import '../../../shared/widgets/common_widgets.dart';
import '../../orders/domain/workflow_actions.dart';
import '../../orders/providers/orders_providers.dart';
import '../../sync/providers/sync_providers.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final homeAsync = ref.watch(driverHomeProvider);
    final currentAsync = ref.watch(currentOrderProvider);
    final pendingAsync = ref.watch(pendingQueueCountProvider);
    final online = ref.watch(isOnlineProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Home'),
        actions: [
          pendingAsync.when(
            data: (count) => count > 0
                ? Padding(
                    padding: const EdgeInsets.only(right: 12),
                    child: Chip(
                      avatar: const Icon(Icons.sync, size: 18),
                      label: Text('$count pending'),
                    ),
                  )
                : const SizedBox.shrink(),
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
          ),
        ],
      ),
      body: Column(
        children: [
          const OfflineBanner(),
          Expanded(
            child: RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(driverHomeProvider);
                ref.invalidate(currentOrderProvider);
                if (online) {
                  await ref.read(syncControllerProvider).syncIfOnline();
                }
              },
              child: AsyncValueWidget(
                value: homeAsync,
                onRetry: () => ref.invalidate(driverHomeProvider),
                data: (home) {
                  final current = currentAsync.valueOrNull;
                  final order = home.currentOrder;
                  final status = order?.status ?? current?.order?.status;
                  final action = status == null ? null : primaryWorkflowAction(status);

                  return ListView(
                    padding: const EdgeInsets.all(20),
                    children: [
                      Text('Hello, ${home.userName}', style: Theme.of(context).textTheme.headlineSmall),
                      const SizedBox(height: 8),
                      Text('Truck: ${home.truckLabel ?? '—'}'),
                      Text('Trailer: ${home.trailerLabel ?? '—'}'),
                      const SizedBox(height: 20),
                      SectionCard(
                        title: 'Next action',
                        child: Text(home.nextAction, style: Theme.of(context).textTheme.titleLarge),
                      ),
                      if (order != null) ...[
                        const SizedBox(height: 16),
                        SectionCard(
                          title: 'Current order',
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(order.orderNumber, style: Theme.of(context).textTheme.titleMedium),
                              const SizedBox(height: 8),
                              StatusChip(status: order.status),
                              if (current != null) ...[
                                const SizedBox(height: 12),
                                Text('Vehicles: ${current.vehicles.length}'),
                                if (current.currentStop != null)
                                  Text('Current stop: ${current.currentStop!.label}'),
                              ],
                              const SizedBox(height: 12),
                              OutlinedButton(
                                onPressed: () => context.push('/orders/${order.id}'),
                                child: const Text('Open order'),
                              ),
                            ],
                          ),
                        ),
                      ],
                      if (action != null && order != null) ...[
                        const SizedBox(height: 24),
                        FilledButton(
                          onPressed: () => _runWorkflow(context, ref, order.id, status!, online),
                          child: Text(action.label),
                        ),
                      ],
                      if (status == 'ASSIGNED' && order != null) ...[
                        const SizedBox(height: 12),
                        OutlinedButton(
                          onPressed: () => _reject(context, ref, order.id, online),
                          child: const Text('Reject order'),
                        ),
                      ],
                    ],
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _runWorkflow(
    BuildContext context,
    WidgetRef ref,
    String orderId,
    String status,
    bool online,
  ) async {
    try {
      await ref.read(workflowControllerProvider).execute(orderId, status, online: online);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(online ? 'Action completed' : 'Queued for sync')),
        );
      }
    } on ApiException catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.userMessage)));
      }
    }
  }

  Future<void> _reject(BuildContext context, WidgetRef ref, String orderId, bool online) async {
    try {
      await ref.read(workflowControllerProvider).reject(orderId, online: online);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(online ? 'Order rejected' : 'Reject queued for sync')),
        );
      }
    } on ApiException catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.userMessage)));
      }
    }
  }
}
