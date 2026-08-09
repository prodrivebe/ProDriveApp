import 'package:flutter_test/flutter_test.dart';
import 'package:prodrive_driver/core/network/api_exception.dart';

void main() {
  test('maps checklist incomplete to friendly message', () {
    final error = ApiException(
      code: 'CHECKLIST_INCOMPLETE',
      message: 'Checklist incomplete',
    );
    expect(error.userMessage, contains('photos'));
  });

  test('maps unauthorized to session message', () {
    final error = ApiException(code: 'UNAUTHORIZED', message: 'Unauthorized');
    expect(error.userMessage, contains('session'));
  });
}
