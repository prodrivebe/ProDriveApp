import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/dio_provider.dart';
import '../../../shared/models/order_models.dart';

final notificationsRepositoryProvider = Provider<NotificationsRepository>((ref) {
  return NotificationsRepository(ref.watch(dioProvider));
});

final notificationsProvider = FutureProvider<List<AppNotification>>((ref) async {
  return ref.read(notificationsRepositoryProvider).list();
});

class NotificationsRepository {
  NotificationsRepository(this._dio);

  final Dio _dio;

  Future<List<AppNotification>> list() async {
    final response = await _dio.get<Map<String, dynamic>>('/notifications');
    return responseDataList(response)
        .map((item) => AppNotification.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<void> markRead(String id) async {
    await _dio.post<Map<String, dynamic>>('/notifications/$id/read');
  }
}
