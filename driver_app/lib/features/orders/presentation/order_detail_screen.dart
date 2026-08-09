import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/connectivity/connectivity_service.dart';
import '../../../core/network/api_exception.dart';
import '../../../shared/widgets/common_widgets.dart';
import '../domain/workflow_actions.dart';
import '../providers/orders_providers.dart';

class OrderDetailScreen extends ConsumerWidget {
  const OrderDetailScreen({super.key, required this.orderId});

  final String orderId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final orderAsync = ref.watch(orderDetailProvider(orderId));
    final timelineAsync = ref.watch(orderTimelineProvider(orderId));
    final checklistAsync = ref.watch(orderChecklistProvider(orderId));
    final online = ref.watch(isOnlineProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Order detail')),
      body: Column(
        children: [
          const OfflineBanner(),
          Expanded(
            child: AsyncValueWidget(
              value: orderAsync,
              onRetry: () => ref.invalidate(orderDetailProvider(orderId)),
              data: (order) {
                final action = primaryWorkflowAction(order.status);
                return RefreshIndicator(
                  onRefresh: () async {
                    ref.invalidate(orderDetailProvider(orderId));
                    ref.invalidate(orderTimelineProvider(orderId));
                    ref.invalidate(orderChecklistProvider(orderId));
                  },
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      Text(order.orderNumber, style: Theme.of(context).textTheme.headlineSmall),
                      const SizedBox(height: 8),
                      StatusChip(status: order.status),
                      if (order.notes != null && order.notes!.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        Text(order.notes!),
                      ],
                      const SizedBox(height: 20),
                      if (action != null)
                        FilledButton(
                          onPressed: () => _workflow(context, ref, order.status, online),
                          child: Text(action.label),
                        ),
                      if (order.status == 'ASSIGNED')
                        OutlinedButton(
                          onPressed: () => _reject(context, ref, online),
                          child: const Text('Reject order'),
                        ),
                      const SizedBox(height: 12),
                      OutlinedButton(
                        onPressed: () => context.push('/orders/$orderId/documents/cmr'),
                        child: const Text('Upload CMR'),
                      ),
                      const SizedBox(height: 24),
                      SectionCard(
                        title: 'Completion checklist',
                        child: checklistAsync.when(
                          loading: () => const CircularProgressIndicator(),
                          error: (error, _) => Text(error.toString()),
                          data: (checklist) => Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              LinearProgressIndicator(value: checklist.completionPercentage / 100),
                              const SizedBox(height: 8),
                              Text('${checklist.completionPercentage}% complete'),
                              if (checklist.missingItems.isNotEmpty) ...[
                                const SizedBox(height: 8),
                                Text('Missing: ${checklist.missingItems.join(', ')}'),
                              ],
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      SectionCard(
                        title: 'Stops',
                        child: Column(
                          children: order.stops
                              .map(
                                (stop) => ListTile(
                                  contentPadding: EdgeInsets.zero,
                                  leading: CircleAvatar(child: Text('${stop.sequence}')),
                                  title: Text(stop.stopType),
                                  subtitle: Text('${stop.label} • ${stop.progressStatus}'),
                                ),
                              )
                              .toList(),
                        ),
                      ),
                      const SizedBox(height: 16),
                      SectionCard(
                        title: 'Vehicles (${order.vehicles.length})',
                        child: Column(
                          children: order.vehicles
                              .map(
                                (vehicle) => ListTile(
                                  contentPadding: EdgeInsets.zero,
                                  title: Text('${vehicle.make ?? 'Vehicle'} ${vehicle.model ?? ''}'.trim()),
                                  subtitle: Text('VIN: ${vehicle.vin ?? '—'}'),
                                  trailing: Icon(
                                    vehicle.isVinVerified ? Icons.verified : Icons.warning_amber,
                                  ),
                                  onTap: () => context.push('/orders/$orderId/vehicles/${vehicle.id}'),
                                ),
                              )
                              .toList(),
                        ),
                      ),
                      const SizedBox(height: 16),
                      SectionCard(
                        title: 'Timeline',
                        child: timelineAsync.when(
                          loading: () => const CircularProgressIndicator(),
                          error: (error, _) => Text(error.toString()),
                          data: (entries) => Column(
                            children: entries
                                .map(
                                  (entry) => ListTile(
                                    contentPadding: EdgeInsets.zero,
                                    title: Text(entry.description),
                                    subtitle: Text(entry.createdAt),
                                  ),
                                )
                                .toList(),
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _workflow(BuildContext context, WidgetRef ref, String status, bool online) async {
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

  Future<void> _reject(BuildContext context, WidgetRef ref, bool online) async {
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
