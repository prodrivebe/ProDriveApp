import 'package:flutter_test/flutter_test.dart';
import 'package:prodrive_driver/features/orders/domain/workflow_actions.dart';

void main() {
  group('workflow actions', () {
    test('maps assigned status to accept', () {
      final action = primaryWorkflowAction('ASSIGNED');
      expect(action?.endpoint, 'accept');
      expect(action?.label, 'Accept order');
    });

    test('maps delivering status to complete delivery', () {
      final action = primaryWorkflowAction('DELIVERING');
      expect(action?.endpoint, 'complete-delivery');
    });

    test('returns reject as secondary for assigned', () {
      final action = secondaryWorkflowAction('ASSIGNED');
      expect(action?.endpoint, 'reject');
    });

    test('returns null for completed orders', () {
      expect(primaryWorkflowAction('COMPLETED'), isNull);
    });
  });
}
