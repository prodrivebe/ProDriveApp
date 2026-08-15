import 'package:flutter_test/flutter_test.dart';
import 'package:prodrive_driver/services/workflow_helper.dart';

void main() {
  test('primary actions follow backend workflow', () {
    expect(WorkflowHelper.primaryAction('ASSIGNED'), 'accept');
    expect(WorkflowHelper.primaryAction('ACCEPTED'), 'arrive-pickup');
    expect(WorkflowHelper.primaryAction('LOADING'), 'complete-loading');
    expect(WorkflowHelper.primaryAction('IN_TRANSIT'), 'arrive-delivery');
    expect(WorkflowHelper.primaryAction('DELIVERING'), 'complete-delivery');
  });

  test('delivery stop is selected by stop type', () {
    final stops = [
      {'stop_type': 'PICKUP', 'city': 'Antwerp', 'address': 'Port'},
      {'stop_type': 'DELIVERY', 'city': 'Munich', 'address': 'Terminal'},
    ];
    final delivery = WorkflowHelper.deliveryStop(stops);
    expect(delivery?['city'], 'Munich');
    expect(WorkflowHelper.stopAddress(delivery), contains('Munich'));
  });

  test('cmr section appears after loading completes', () {
    expect(WorkflowHelper.showCmrSection('LOADING'), isFalse);
    expect(WorkflowHelper.showCmrSection('IN_TRANSIT'), isTrue);
    expect(WorkflowHelper.canGenerateCmr('IN_TRANSIT'), isTrue);
  });
}
