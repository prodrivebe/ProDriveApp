import 'package:flutter_test/flutter_test.dart';

import 'package:prodrive_driver/features/orders/domain/workflow_navigation.dart';

void main() {
  test('workflowRouteForStatus maps pickup statuses to loading', () {
    expect(workflowRouteForStatus('LOADING'), 'loading');
    expect(workflowRouteForStatus('ARRIVED_PICKUP'), 'loading');
  });

  test('buildWorkflowPath returns order detail fallback for unknown status', () {
    expect(
      buildWorkflowPath(orderId: 'abc', status: 'CANCELLED'),
      '/orders/abc',
    );
  });
}
