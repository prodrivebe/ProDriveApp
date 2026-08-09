import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_provider.dart';
import '../data/vehicle_repository.dart';

final vehicleRepositoryProvider = Provider<VehicleExecutionRepository>((ref) {
  return VehicleExecutionRepository(ref.watch(dioProvider));
});
