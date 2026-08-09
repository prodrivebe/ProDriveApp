import 'package:flutter_test/flutter_test.dart';
import 'package:prodrive_driver/features/sync/data/sync_service.dart';

import 'helpers/hive_test_helper.dart';

void main() {
  setUp(() async {
    await initTestHive();
  });

  tearDown(() async {
    await closeTestHive();
  });

  test('enqueue and list pending operations', () async {
    final queue = OfflineQueueRepository();
    await queue.enqueue(
      QueuedOperation(
        id: 'op-1',
        type: 'workflow',
        path: '/orders/abc/accept',
      ),
    );

    final pending = await queue.pending();
    expect(pending, hasLength(1));
    expect(pending.first.path, '/orders/abc/accept');
  });

  test('remove clears queued operation', () async {
    final queue = OfflineQueueRepository();
    await queue.enqueue(
      QueuedOperation(
        id: 'op-2',
        type: 'workflow',
        path: '/orders/abc/reject',
      ),
    );
    await queue.remove('op-2');
    expect(await queue.pending(), isEmpty);
  });
}
