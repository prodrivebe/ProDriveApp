import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../shared/models/order_models.dart';

class VehicleExecutionRepository {
  VehicleExecutionRepository(this._dio);

  final Dio _dio;

  Future<List<VinHistoryEntry>> vinHistory(String orderId, String vehicleId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/orders/$orderId/vehicles/$vehicleId/vin-history',
    );
    return responseDataList(response)
        .map((item) => VinHistoryEntry.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<OrderVehicle> verifyVin(String orderId, String vehicleId, String vin) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/orders/$orderId/vehicles/$vehicleId/verify-vin',
      data: {'vin': vin},
    );
    final data = responseDataMap(response);
    return OrderVehicle(
      id: data['vehicle_id'] as String,
      make: null,
      model: null,
      color: null,
      vin: data['vin'] as String?,
      verifiedVin: data['verified_vin'] as String?,
      pickupStopId: null,
      deliveryStopId: null,
    );
  }

  Future<void> updateVin(String orderId, String vehicleId, String vin) async {
    await _dio.put<Map<String, dynamic>>(
      '/orders/$orderId/vehicles/$vehicleId/vin',
      data: {'vin': vin},
    );
  }

  Future<List<VehiclePhoto>> listPhotos(String orderId, String vehicleId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/orders/$orderId/vehicles/$vehicleId/photos',
    );
    return responseDataList(response)
        .map((item) => VehiclePhoto.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<void> uploadPhoto(
    String orderId,
    String vehicleId,
    String filePath,
    String photoType,
  ) async {
    final formData = FormData.fromMap({
      'photo_type': photoType,
      'file': await MultipartFile.fromFile(filePath),
    });
    await _dio.post<Map<String, dynamic>>(
      '/orders/$orderId/vehicles/$vehicleId/photos',
      data: formData,
    );
  }

  Future<List<VehicleDamageReport>> listDamage(String orderId, String vehicleId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/orders/$orderId/vehicles/$vehicleId/damage',
    );
    return responseDataList(response)
        .map((item) => VehicleDamageReport.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<void> createDamage(
    String orderId,
    String vehicleId, {
    required String damageType,
    required String severity,
    required String description,
    required String location,
    List<String> photoIds = const [],
  }) async {
    await _dio.post<Map<String, dynamic>>(
      '/orders/$orderId/vehicles/$vehicleId/damage',
      data: {
        'damage_type': damageType,
        'severity': severity,
        'description': description,
        'location': location,
        'photo_ids': photoIds,
      },
    );
  }

  Future<void> uploadDocument(String orderId, String filePath, {String type = 'CMR'}) async {
    final formData = FormData.fromMap({
      'document_type': type,
      'file': await MultipartFile.fromFile(filePath),
    });
    await _dio.post<Map<String, dynamic>>('/orders/$orderId/documents', data: formData);
  }
}
