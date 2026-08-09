class ApiException implements Exception {
  ApiException({required this.code, required this.message, this.statusCode});

  final String code;
  final String message;
  final int? statusCode;

  @override
  String toString() => message;

  String get userMessage {
    switch (code) {
      case 'CHECKLIST_INCOMPLETE':
        return 'Complete required photos, VIN verification, and documents before finishing delivery.';
      case 'UNAUTHORIZED':
        return 'Your session expired. Please sign in again.';
      case 'INVALID_ORDER_STATUS':
        return 'This action is not available for the current order state.';
      default:
        return message;
    }
  }
}
