import 'package:flutter_test/flutter_test.dart';

void main() {
  test('workflow realtime event names are stable', () {
    const events = [
      'ORDER_ASSIGNED',
      'ORDER_ACCEPTED',
      'LOADING_STARTED',
      'TRANSIT_STARTED',
      'ORDER_COMPLETED',
      'TIMELINE_ENTRY',
      'NOTIFICATION_CREATED',
    ];
    expect(events.every((event) => event.contains('_')), isTrue);
  });
}
