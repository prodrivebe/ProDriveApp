import 'package:flutter_test/flutter_test.dart';
import 'package:prodrive_driver/services/workflow_helper.dart';

void main() {
  test('workflow helper maps delivery phase', () {
    expect(WorkflowHelper.showDeliverySection('IN_TRANSIT'), isTrue);
    expect(WorkflowHelper.showDeliverySection('LOADING'), isFalse);
  });
}
