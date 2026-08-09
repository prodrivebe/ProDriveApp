import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/storage/hive_boxes.dart';

class QueuedOperation {
  QueuedOperation({
    required this.id,
    required this.type,
    required this.path,
    this.method = 'POST',
    this.body,
    this.filePath,
    this.fields,
  });

  final String id;
  final String type;
  final String method;
  final String path;
  final Map<String, dynamic>? body;
  final String? filePath;
  final Map<String, String>? fields;

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': type,
        'method': method,
        'path': path,
        'body': body,
        'file_path': filePath,
        'fields': fields,
      };

  factory QueuedOperation.fromJson(Map<String, dynamic> json) => QueuedOperation(
        id: json['id'] as String,
        type: json['type'] as String,
        method: json['method'] as String? ?? 'POST',
        path: json['path'] as String,
        body: json['body'] as Map<String, dynamic>?,
        filePath: json['file_path'] as String?,
        fields: (json['fields'] as Map?)?.cast<String, String>(),
      );
}

class OfflineQueueRepository {
  Future<List<QueuedOperation>> pending() async {
    final box = HiveBoxes.queueBox;
    return box.values
        .map((raw) => QueuedOperation.fromJson(jsonDecode(raw) as Map<String, dynamic>))
        .toList();
  }

  Future<void> enqueue(QueuedOperation operation) async {
    final box = HiveBoxes.queueBox;
    await box.put(operation.id, jsonEncode(operation.toJson()));
  }

  Future<void> remove(String id) async {
    await HiveBoxes.queueBox.delete(id);
  }

  Future<void> clear() async {
    await HiveBoxes.queueBox.clear();
  }
}

class SyncService {
  SyncService(this._dio, this._queue);

  final Dio _dio;
  final OfflineQueueRepository _queue;

  Future<int> syncPending() async {
    final pending = await _queue.pending();
    var synced = 0;
    for (final operation in pending) {
      try {
        if (operation.filePath != null) {
          final formData = FormData.fromMap({
            ...?operation.fields,
            'file': await MultipartFile.fromFile(operation.filePath!),
          });
          await _dio.post<Map<String, dynamic>>(operation.path, data: formData);
        } else if (operation.method == 'PUT') {
          await _dio.put<Map<String, dynamic>>(operation.path, data: operation.body);
        } else {
          await _dio.post<Map<String, dynamic>>(operation.path, data: operation.body);
        }
        await _queue.remove(operation.id);
        synced += 1;
      } on DioException catch (error) {
        rethrowDio(error);
      }
    }
    return synced;
  }
}
