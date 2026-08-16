import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/connectivity/connectivity_service.dart';
import '../../../core/network/api_exception.dart';
import '../../sync/data/sync_service.dart';
import '../../sync/providers/sync_providers.dart';
import '../../vehicles/providers/vehicle_detail_providers.dart';
import '../../vehicles/providers/vehicle_providers.dart';

final uploadControllerProvider = Provider<UploadController>((ref) => UploadController(ref));

class UploadController {
  UploadController(this._ref);

  final Ref _ref;

  Future<void> uploadPhoto({
    required String orderId,
    required String vehicleId,
    required String filePath,
    required String photoType,
  }) async {
    final online = _ref.read(isOnlineProvider);
    final path = '/orders/$orderId/vehicles/$vehicleId/photos';
    if (!online) {
      await _ref.read(offlineQueueProvider).enqueue(
            QueuedOperation(
              id: 'photo-$vehicleId-$photoType-${DateTime.now().millisecondsSinceEpoch}',
              type: 'photo',
              path: path,
              filePath: filePath,
              fields: {'photo_type': photoType},
            ),
          );
      _ref.read(syncTickProvider.notifier).state++;
      return;
    }

    try {
      await _ref.read(vehicleRepositoryProvider).uploadPhoto(orderId, vehicleId, filePath, photoType);
      _ref.invalidate(vehiclePhotosProvider((orderId: orderId, vehicleId: vehicleId)));
    } on ApiException {
      rethrow;
    }
  }

  Future<void> uploadDocument({
    required String orderId,
    required String filePath,
    String documentType = 'CMR',
  }) async {
    final online = _ref.read(isOnlineProvider);
    final path = '/orders/$orderId/documents';
    if (!online) {
      await _ref.read(offlineQueueProvider).enqueue(
            QueuedOperation(
              id: 'doc-$orderId-$documentType-${DateTime.now().millisecondsSinceEpoch}',
              type: 'document',
              path: path,
              filePath: filePath,
              fields: {'document_type': documentType},
            ),
          );
      _ref.read(syncTickProvider.notifier).state++;
      return;
    }

    await _ref.read(vehicleRepositoryProvider).uploadDocument(orderId, filePath, type: documentType);
  }

  Future<void> verifyVin({
    required String orderId,
    required String vehicleId,
    required String vin,
  }) async {
    final online = _ref.read(isOnlineProvider);
    if (!online) {
      await _ref.read(offlineQueueProvider).enqueue(
            QueuedOperation(
              id: 'vin-verify-$vehicleId-${DateTime.now().millisecondsSinceEpoch}',
              type: 'vin',
              path: '/orders/$orderId/vehicles/$vehicleId/verify-vin',
              body: {'vin': vin},
            ),
          );
      _ref.read(syncTickProvider.notifier).state++;
      return;
    }

    await _ref.read(vehicleRepositoryProvider).verifyVin(orderId, vehicleId, vin);
    _ref.invalidate(vinHistoryProvider((orderId: orderId, vehicleId: vehicleId)));
  }

  Future<void> updateVin({
    required String orderId,
    required String vehicleId,
    required String vin,
  }) async {
    final online = _ref.read(isOnlineProvider);
    if (!online) {
      await _ref.read(offlineQueueProvider).enqueue(
            QueuedOperation(
              id: 'vin-update-$vehicleId-${DateTime.now().millisecondsSinceEpoch}',
              type: 'vin',
              method: 'PUT',
              path: '/orders/$orderId/vehicles/$vehicleId/vin',
              body: {'vin': vin},
            ),
          );
      _ref.read(syncTickProvider.notifier).state++;
      return;
    }

    await _ref.read(vehicleRepositoryProvider).updateVin(orderId, vehicleId, vin);
  }

  Future<void> submitDamage({
    required String orderId,
    required String vehicleId,
    required String damageType,
    required String severity,
    required String description,
    required String location,
    List<String> photoIds = const [],
  }) async {
    final online = _ref.read(isOnlineProvider);
    if (!online) {
      await _ref.read(offlineQueueProvider).enqueue(
            QueuedOperation(
              id: 'damage-$vehicleId-${DateTime.now().millisecondsSinceEpoch}',
              type: 'damage',
              path: '/orders/$orderId/vehicles/$vehicleId/damage',
              body: {
                'damage_type': damageType,
                'severity': severity,
                'description': description,
                'location': location,
                'photo_ids': photoIds,
              },
            ),
          );
      _ref.read(syncTickProvider.notifier).state++;
      return;
    }

    await _ref.read(vehicleRepositoryProvider).createDamage(
          orderId,
          vehicleId,
          damageType: damageType,
          severity: severity,
          description: description,
          location: location,
          photoIds: photoIds,
        );
    _ref.invalidate(vehicleDamageProvider((orderId: orderId, vehicleId: vehicleId)));
  }
}
