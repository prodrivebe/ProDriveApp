import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/widgets/common_widgets.dart';
import '../../orders/providers/orders_providers.dart';
import '../providers/vehicle_detail_providers.dart';

class VehicleDetailScreen extends ConsumerWidget {
  const VehicleDetailScreen({
    super.key,
    required this.orderId,
    required this.vehicleId,
  });

  final String orderId;
  final String vehicleId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final orderAsync = ref.watch(orderDetailProvider(orderId));
    final photosAsync = ref.watch(vehiclePhotosProvider((orderId: orderId, vehicleId: vehicleId)));
    final damageAsync = ref.watch(vehicleDamageProvider((orderId: orderId, vehicleId: vehicleId)));

    return Scaffold(
      appBar: AppBar(title: const Text('Vehicle')),
      body: AsyncValueWidget(
        value: orderAsync,
        onRetry: () => ref.invalidate(orderDetailProvider(orderId)),
        data: (order) {
          final vehicle = order.vehicles.firstWhere((item) => item.id == vehicleId);
          final pickup = order.stops.where((s) => s.id == vehicle.pickupStopId).firstOrNull;
          final delivery = order.stops.where((s) => s.id == vehicle.deliveryStopId).firstOrNull;

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('${vehicle.make ?? 'Vehicle'} ${vehicle.model ?? ''}'.trim(),
                  style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 8),
              Text('Color: ${vehicle.color ?? '—'}'),
              Text('VIN: ${vehicle.vin ?? '—'}'),
              const SizedBox(height: 8),
              StatusChip(status: vehicle.isVinVerified ? 'VIN VERIFIED' : 'VIN PENDING'),
              const SizedBox(height: 16),
              SectionCard(
                title: 'Stops',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Pickup: ${pickup?.label ?? '—'}'),
                    const SizedBox(height: 8),
                    Text('Delivery: ${delivery?.label ?? '—'}'),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              SectionCard(
                title: 'Execution status',
                child: photosAsync.when(
                  loading: () => const CircularProgressIndicator(),
                  error: (error, _) => Text(error.toString()),
                  data: (photos) => damageAsync.when(
                    loading: () => const CircularProgressIndicator(),
                    error: (error, _) => Text(error.toString()),
                    data: (damage) => Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Photos uploaded: ${photos.length}'),
                        Text('Damage reports: ${damage.length}'),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: () => context.push('/orders/$orderId/vehicles/$vehicleId/vin'),
                child: const Text('Verify VIN'),
              ),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: () => context.push('/orders/$orderId/vehicles/$vehicleId/photos'),
                child: const Text('Capture photos'),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () => context.push('/orders/$orderId/vehicles/$vehicleId/damage'),
                child: const Text('Report damage'),
              ),
            ],
          );
        },
      ),
    );
  }
}

extension<T> on Iterable<T> {
  T? get firstOrNull {
    final iterator = this.iterator;
    if (!iterator.moveNext()) return null;
    return iterator.current;
  }
}
