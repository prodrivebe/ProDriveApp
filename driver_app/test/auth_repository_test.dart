import 'package:flutter_test/flutter_test.dart';
import 'package:prodrive_driver/core/storage/secure_token_storage.dart';
import 'package:prodrive_driver/shared/models/auth_models.dart';

void main() {
  test('StoredTokens hold access and refresh values', () {
    const tokens = StoredTokens(accessToken: 'access', refreshToken: 'refresh');
    expect(tokens.accessToken, 'access');
    expect(tokens.refreshToken, 'refresh');
  });

  test('UserProfile fullName combines names', () {
    const profile = UserProfile(
      id: '1',
      firstName: 'Alex',
      lastName: 'Driver',
      email: 'alex@example.com',
      role: 'DRIVER',
    );
    expect(profile.fullName, 'Alex Driver');
  });

  test('AuthTokens fromJson maps backend payload', () {
    final tokens = AuthTokens.fromJson({
      'access_token': 'access-token',
      'refresh_token': 'refresh-token',
    });
    expect(tokens.accessToken, 'access-token');
  });
}
