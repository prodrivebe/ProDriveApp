class WorkflowAction {
  const WorkflowAction({required this.endpoint, required this.label});

  final String endpoint;
  final String label;
}

WorkflowAction? primaryWorkflowAction(String status) {
  switch (status) {
    case 'ASSIGNED':
      return const WorkflowAction(endpoint: 'accept', label: 'Accept order');
    case 'ACCEPTED':
      return const WorkflowAction(endpoint: 'arrive-pickup', label: 'Arrived at pickup');
    case 'ARRIVED_PICKUP':
      return const WorkflowAction(endpoint: 'start-loading', label: 'Start loading');
    case 'LOADING':
      return const WorkflowAction(endpoint: 'complete-loading', label: 'Complete loading');
    case 'LOADED':
      return const WorkflowAction(endpoint: 'start-transit', label: 'Start transit');
    case 'IN_TRANSIT':
      return const WorkflowAction(endpoint: 'arrive-delivery', label: 'Arrived at delivery');
    case 'ARRIVED_DELIVERY':
      return const WorkflowAction(endpoint: 'start-delivery', label: 'Start delivery');
    case 'DELIVERING':
      return const WorkflowAction(endpoint: 'complete-delivery', label: 'Complete delivery');
    default:
      return null;
  }
}

WorkflowAction? secondaryWorkflowAction(String status) {
  if (status == 'ASSIGNED') {
    return const WorkflowAction(endpoint: 'reject', label: 'Reject order');
  }
  return null;
}
