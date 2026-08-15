import 'dart:typed_data';

import '../config/api_config.dart';
import 'api_client.dart';
import 'app_logger.dart';

class DriverRepository {
  DriverRepository(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> home() async {
    final response = await _api.getJson('/drivers/me/home');
    return response['data'] as Map<String, dynamic>;
  }

  Future<List<dynamic>> orders() async {
    final response = await _api.getJson('/drivers/me/orders');
    final data = response['data'];
    if (data is List<dynamic>) {
      return data;
    }
    return (data as Map<String, dynamic>? ?? {})['items'] as List<dynamic>? ?? [];
  }

  Future<Map<String, dynamic>> orderDetail(String orderId) async {
    final response = await _api.getJson('/orders/$orderId');
    return response['data'] as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> workflowAction(String orderId, String action) async {
    AppLogger.workflow(orderId: orderId, status: 'action', action: action);
    final response = await _api.postAction('/orders/$orderId/$action');
    final data = response['data'] as Map<String, dynamic>;
    AppLogger.workflow(
      orderId: orderId,
      status: data['status'] as String? ?? 'unknown',
      action: action,
      detail: 'completed',
    );
    return data;
  }

  Future<Map<String, dynamic>?> fetchCmr(String orderId) async {
    try {
      final response = await _api.getJson('/orders/$orderId/cmr');
      return response['data'] as Map<String, dynamic>;
    } on ApiException catch (error) {
      if (error.statusCode == 404) {
        return null;
      }
      rethrow;
    }
  }

  Future<Map<String, dynamic>> generateCmr(String orderId) async {
    final response = await _api.postAction('/orders/$orderId/cmr/generate');
    return response['data'] as Map<String, dynamic>;
  }

  Future<Uint8List> downloadCmrBytes(Map<String, dynamic> document) async {
    final filePath = document['file_path'] as String;
    final url = ApiConfig.resolveUploadUrl(filePath);
    AppLogger.cmr('download url=$url');
    return _api.getBytes(url);
  }

  Future<Map<String, dynamic>> uploadSignedCmr({
    required String orderId,
    required Uint8List bytes,
    required String fileName,
  }) async {
    final response = await _api.uploadMultipart(
      path: '/orders/$orderId/cmr/upload',
      fieldName: 'file',
      fileName: fileName,
      bytes: bytes,
    );
    return response['data'] as Map<String, dynamic>;
  }
}
