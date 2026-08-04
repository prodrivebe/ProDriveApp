import '../services/api_client.dart';

class DriverRepository {
  DriverRepository(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> home() async {
    final response = await _api.getJson('/drivers/me/home');
    return response['data'] as Map<String, dynamic>;
  }

  Future<List<dynamic>> orders() async {
    final response = await _api.getJson('/drivers/me/orders');
    return response['data'] as List<dynamic>;
  }

  Future<Map<String, dynamic>> orderDetail(String orderId) async {
    final response = await _api.getJson('/orders/$orderId');
    return response['data'] as Map<String, dynamic>;
  }

  Future<void> workflowAction(String orderId, String action) async {
    await _api.postAction('/orders/$orderId/$action');
  }
}
