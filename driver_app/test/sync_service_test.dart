import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:prodrive_driver/features/sync/data/sync_service.dart';

import 'helpers/hive_test_helper.dart';

class _QueueAdapter implements HttpClientAdapter {
  _QueueAdapter(this.onRequest);

  final Future<ResponseBody> Function(RequestOptions options) onRequest;

  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<List<int>>? requestStream, Future<void>? cancelFuture) {
    return onRequest(options);
  }
}

void main() {
  setUp(() async {
    await initTestHive();
  });

  tearDown(() async {
    await closeTestHive();
  });

  test('syncPending posts queued workflow operations', () async {
    final queue = OfflineQueueRepository();
    await queue.enqueue(
      QueuedOperation(
        id: 'sync-1',
        type: 'workflow',
        path: '/orders/123/accept',
      ),
    );

    final requests = <String>[];
    final dio = Dio(BaseOptions(baseUrl: 'http://localhost/api/v1'));
    dio.httpClientAdapter = _QueueAdapter((options) async {
      requests.add(options.path);
      return ResponseBody.fromString(
        '{"success": true, "data": {}}',
        200,
        headers: {Headers.contentTypeHeader: [Headers.jsonContentType]},
      );
    });

    final synced = await SyncService(dio, queue).syncPending();
    expect(synced, 1);
    expect(requests, ['/orders/123/accept']);
    expect(await queue.pending(), isEmpty);
  });
}
