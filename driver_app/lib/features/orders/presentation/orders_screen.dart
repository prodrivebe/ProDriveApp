import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../shared/widgets/common_widgets.dart';
import '../providers/orders_providers.dart';

class OrdersScreen extends ConsumerWidget {
  const OrdersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ordersAsync = ref.watch(driverOrdersProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Orders')),
      body: Column(
        children: [
          const OfflineBanner(),
          Expanded(
            child: RefreshIndicator(
              onRefresh: () async => ref.invalidate(driverOrdersProvider),
              child: AsyncValueWidget(
                value: ordersAsync,
                onRetry: () => ref.invalidate(driverOrdersProvider),
                data: (orders) {
                  if (orders.isEmpty) {
                    return ListView(
                      children: const [
                        SizedBox(height: 120),
                        Center(child: Text('No assigned orders yet.')),
                      ],
                    );
                  }

                  final active = orders.where((o) => !o.status.contains('COMPLETED')).toList();
                  final history = orders.where((o) => o.status.contains('COMPLETED')).toList();

                  return ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      if (active.isNotEmpty) ...[
                        Text('Active', style: Theme.of(context).textTheme.titleMedium),
                        const SizedBox(height: 8),
                        ...active.map((order) => _OrderTile(orderId: order.id, orderNumber: order.orderNumber, status: order.status)),
                        const SizedBox(height: 24),
                      ],
                      if (history.isNotEmpty) ...[
                        Text('History', style: Theme.of(context).textTheme.titleMedium),
                        const SizedBox(height: 8),
                        ...history.map((order) => _OrderTile(orderId: order.id, orderNumber: order.orderNumber, status: order.status)),
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
}

class _OrderTile extends StatelessWidget {
  const _OrderTile({
    required this.orderId,
    required this.orderNumber,
    required this.status,
  });

  final String orderId;
  final String orderNumber;
  final String status;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        title: Text(orderNumber),
        subtitle: StatusChip(status: status),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => context.push('/orders/$orderId'),
      ),
    );
  }
}
