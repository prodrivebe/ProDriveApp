/// Maps workflow statuses to the next driver workflow screen route.
String? workflowRouteForStatus(String status) {
  switch (status) {
    case 'ASSIGNED':
    case 'ACCEPTED':
      return 'navigation';
    case 'ARRIVED_PICKUP':
    case 'LOADING':
      return 'loading';
    case 'LOADED':
    case 'IN_TRANSIT':
      return 'navigation';
    case 'ARRIVED_DELIVERY':
    case 'DELIVERING':
      return 'delivery';
    case 'DELIVERED':
    case 'COMPLETED':
      return 'completion';
    default:
      return null;
  }
}

/// Builds an order workflow path segment for GoRouter navigation.
String buildWorkflowPath({
  required String orderId,
  required String status,
}) {
  final segment = workflowRouteForStatus(status);
  if (segment == null) {
    return '/orders/$orderId';
  }
  return '/orders/$orderId/workflow/$segment';
}
