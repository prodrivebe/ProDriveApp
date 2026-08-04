import 'api_client.dart';

class AuthService {
  AuthService(this._api);

  final ApiClient _api;

  Future<void> login(String email, String password) async {
    final response = await _api.postJson('/auth/login', {
      'email': email,
      'password': password,
    });
    final token = response['data']['access_token'] as String;
    await _api.saveToken(token);
  }

  Future<void> logout() => _api.clearToken();
}
