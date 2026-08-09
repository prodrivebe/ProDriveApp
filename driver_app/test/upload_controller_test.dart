import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:prodrive_driver/core/connectivity/connectivity_service.dart';
import 'package:prodrive_driver/features/photos/providers/upload_providers.dart';
import 'package:prodrive_driver/features/sync/data/sync_service.dart';
import 'package:prodrive_driver/features/sync/providers/sync_providers.dart';

import 'helpers/hive_test_helper.dart';

void main() {
  setUp(() async {
    await initTestHive();
  });

  tearDown(() async {
    await closeTestHive();
  });

  test('uploadPhoto queues operation when offline', () async {
    final container = ProviderContainer(
      overrides: [
        isOnlineProvider.overrideWith((ref) => false),
      ],
    );
    addTearDown(container.dispose);

    await container.read(uploadControllerProvider).uploadPhoto(
          orderId: 'order-1',
          vehicleId: 'vehicle-1',
          filePath: '/tmp/front.jpg',
          photoType: 'FRONT',
        );

    final pending = await container.read(offlineQueueProvider).pending();
    expect(pending, hasLength(1));
    expect(pending.first.type, 'photo');
    expect(pending.first.fields?['photo_type'], 'FRONT');
  });

  test('submitDamage queues JSON body offline', () async {
    final container = ProviderContainer(
      overrides: [
        isOnlineProvider.overrideWith((ref) => false),
      ],
    );
    addTearDown(container.dispose);

    await container.read(uploadControllerProvider).submitDamage(
          orderId: 'order-1',
          vehicleId: 'vehicle-1',
          damageType: 'SCRATCH',
          severity: 'MINOR',
          description: 'Scratch on door',
          location: 'Front left door',
        );

    final pending = await container.read(offlineQueueProvider).pending();
    expect(pending.first.path, contains('/damage'));
    expect(pending.first.body?['severity'], 'MINOR');
  });

  test('uploadDocument queues CMR upload offline', () async {
    final container = ProviderContainer(
      overrides: [
        isOnlineProvider.overrideWith((ref) => false),
      ],
    );
    addTearDown(container.dispose);

    await container.read(uploadControllerProvider).uploadDocument(
          orderId: 'order-1',
          filePath: '/tmp/cmr.jpg',
        );

    final pending = await container.read(offlineQueueProvider).pending();
    expect(pending.first.type, 'document');
    expect(pending.first.fields?['document_type'], 'CMR');
  });

  test('verifyVin queues verification offline', () async {
    final container = ProviderContainer(
      overrides: [
        isOnlineProvider.overrideWith((ref) => false),
      ],
    );
    addTearDown(container.dispose);

    await container.read(uploadControllerProvider).verifyVin(
          orderId: 'order-1',
          vehicleId: 'vehicle-1',
          vin: '1HGCM82633A004352',
        );

    final pending = await container.read(offlineQueueProvider).pending();
    expect(pending.first.body?['vin'], '1HGCM82633A004352');
  });
}
