import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/models/order_models.dart';
import '../data/vehicle_repository.dart';
import 'vehicle_providers.dart';

final vehiclePhotosProvider =
    FutureProvider.family<List<VehiclePhoto>, ({String orderId, String vehicleId})>((ref, args) {
  return ref.read(vehicleRepositoryProvider).listPhotos(args.orderId, args.vehicleId);
});

final vehicleDamageProvider =
    FutureProvider.family<List<VehicleDamageReport>, ({String orderId, String vehicleId})>((ref, args) {
  return ref.read(vehicleRepositoryProvider).listDamage(args.orderId, args.vehicleId);
});

final vinHistoryProvider =
    FutureProvider.family<List<VinHistoryEntry>, ({String orderId, String vehicleId})>((ref, args) {
  return ref.read(vehicleRepositoryProvider).vinHistory(args.orderId, args.vehicleId);
});
