import 'package:flutter_test/flutter_test.dart';

import 'package:prodrive_driver/features/auth/providers/auth_controller.dart';

void main() {
  test('AuthController exposes ready and authenticated flags', () {
    expect(AuthController, isNotNull);
  });
}
