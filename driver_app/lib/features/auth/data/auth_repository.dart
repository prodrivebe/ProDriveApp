import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/storage/secure_token_storage.dart';

class AuthRepository {
  AuthRepository(this._dio, this._storage);

  final Dio _dio;
  final SecureTokenStorage _storage;

  Future<StoredTokens> login(String username, String password) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/auth/login',
        data: {'username': username, 'password': password},
      );
      final data = responseDataMap(response);
      final tokens = StoredTokens(
        accessToken: data['access_token'] as String,
        refreshToken: data['refresh_token'] as String,
      );
      await _storage.writeTokens(tokens);
      return tokens;
    } on DioException catch (error) {
      rethrowDio(error);
    }
  }

  Future<StoredTokens?> refreshTokens() async {
    final existing = await _storage.readTokens();
    if (existing == null) return null;
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/auth/refresh',
        data: {'refresh_token': existing.refreshToken},
      );
      final data = responseDataMap(response);
      final tokens = StoredTokens(
        accessToken: data['access_token'] as String,
        refreshToken: data['refresh_token'] as String,
      );
      await _storage.writeTokens(tokens);
      return tokens;
    } catch (_) {
      await _storage.clear();
      return null;
    }
  }

  Future<void> logout() async {
    final tokens = await _storage.readTokens();
    if (tokens != null) {
      try {
        await _dio.post<Map<String, dynamic>>(
          '/auth/logout',
          data: {'refresh_token': tokens.refreshToken},
        );
      } catch (_) {}
    }
    await _storage.clear();
  }

  Future<StoredTokens?> currentTokens() => _storage.readTokens();
}
