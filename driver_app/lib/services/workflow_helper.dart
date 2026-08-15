/// Workflow helpers aligned with backend order status machine.
class WorkflowHelper {
  WorkflowHelper._();

  static const activeStatuses = {
    'ASSIGNED',
    'ACCEPTED',
    'LOADING',
    'IN_TRANSIT',
    'DELIVERING',
  };

  static bool isActiveStatus(String? status) =>
      status != null && activeStatuses.contains(status);

  /// Primary workflow action endpoint for the current status.
  static String? primaryAction(String status) {
    switch (status) {
      case 'ASSIGNED':
        return 'accept';
      case 'ACCEPTED':
        return 'arrive-pickup';
      case 'LOADING':
        return 'complete-loading';
      case 'IN_TRANSIT':
        return 'arrive-delivery';
      case 'DELIVERING':
        return 'complete-delivery';
      default:
        return null;
    }
  }

  static String primaryActionLabel(String status) {
    switch (status) {
      case 'ASSIGNED':
        return 'Accept order';
      case 'ACCEPTED':
        return 'Arrived at pickup';
      case 'LOADING':
        return 'Finish loading';
      case 'IN_TRANSIT':
        return 'Arrived at delivery';
      case 'DELIVERING':
        return 'Complete job';
      default:
        return 'Continue';
    }
  }

  static String phaseTitle(String status) {
    switch (status) {
      case 'ASSIGNED':
        return 'New assignment';
      case 'ACCEPTED':
        return 'Navigate to pickup';
      case 'LOADING':
        return 'Loading vehicles';
      case 'IN_TRANSIT':
        return 'Generate CMR & deliver';
      case 'DELIVERING':
        return 'Delivery & CMR';
      case 'COMPLETED':
        return 'Job completed';
      default:
        return 'Order';
    }
  }

  static bool showDeliverySection(String status) =>
      status == 'IN_TRANSIT' || status == 'DELIVERING';

  static bool showCmrSection(String status) =>
      status == 'IN_TRANSIT' || status == 'DELIVERING';

  static bool canGenerateCmr(String status) =>
      status == 'IN_TRANSIT' || status == 'DELIVERING';

  static Map<String, dynamic>? pickupStop(List<dynamic> stops) {
    for (final stop in stops) {
      final map = stop as Map<String, dynamic>;
      if (map['stop_type'] == 'PICKUP') return map;
    }
    return stops.isNotEmpty ? stops.first as Map<String, dynamic> : null;
  }

  static Map<String, dynamic>? deliveryStop(List<dynamic> stops) {
    for (final stop in stops) {
      final map = stop as Map<String, dynamic>;
      if (map['stop_type'] == 'DELIVERY') return map;
    }
    if (stops.length > 1) {
      return stops.last as Map<String, dynamic>;
    }
    return null;
  }

  static String stopAddress(Map<String, dynamic>? stop) {
    if (stop == null) return '';
    final parts = <String>[
      stop['address'] as String? ?? '',
      stop['city'] as String? ?? '',
      stop['postal_code'] as String? ?? '',
      stop['country'] as String? ?? '',
    ].where((part) => part.trim().isNotEmpty);
    return parts.join(', ');
  }
}
