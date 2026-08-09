import 'dart:convert';

import 'package:dio/dio.dart';

import '../config/api_config.dart';
import '../storage/secure_token_storage.dart';
import 'api_exception.dart';

class TokenRefreshInterceptor extends Interceptor {
  TokenRefreshInterceptor(this._storage);

  final SecureTokenStorage _storage;
  Dio? _refreshDio;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final tokens = await _storage.readTokens();
    if (tokens != null) {
      options.headers['Authorization'] = 'Bearer ${tokens.accessToken}';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode != 401 ||
        err.requestOptions.path.contains('/auth/login') ||
        err.requestOptions.path.contains('/auth/refresh')) {
      return handler.next(err);
    }

    try {
      final tokens = await _storage.readTokens();
      if (tokens == null) return handler.next(err);

      _refreshDio ??= Dio(BaseOptions(baseUrl: ApiConfig.baseUrl));
      final response = await _refreshDio!.post<Map<String, dynamic>>(
        '/auth/refresh',
        data: {'refresh_token': tokens.refreshToken},
      );
      final body = response.data;
      if (body?['success'] != true) return handler.next(err);

      final data = body!['data'] as Map<String, dynamic>;
      final refreshed = StoredTokens(
        accessToken: data['access_token'] as String,
        refreshToken: data['refresh_token'] as String,
      );
      await _storage.writeTokens(refreshed);

      final retry = err.requestOptions;
      retry.headers['Authorization'] = 'Bearer ${refreshed.accessToken}';
      final clone = Dio(BaseOptions(baseUrl: ApiConfig.baseUrl));
      final result = await clone.fetch(retry);
      return handler.resolve(result);
    } catch (_) {
      await _storage.clear();
      return handler.next(err);
    }
  }
}

Map<String, dynamic> responseDataMap(Response<dynamic> response) {
  final body = response.data;
  if (body is! Map<String, dynamic> || body['success'] != true) {
    final error = (body as Map?)?['error'] as Map<String, dynamic>? ?? {};
    throw ApiException(
      code: error['code'] as String? ?? 'REQUEST_FAILED',
      message: error['message'] as String? ?? 'Request failed.',
      statusCode: response.statusCode,
    );
  }
  return body['data'] as Map<String, dynamic>? ?? {};
}

List<dynamic> responseDataList(Response<dynamic> response) {
  final body = response.data;
  if (body is! Map<String, dynamic> || body['success'] != true) {
    final error = body['error'] as Map<String, dynamic>? ?? {};
    throw ApiException(
      code: error['code'] as String? ?? 'REQUEST_FAILED',
      message: error['message'] as String? ?? 'Request failed.',
      statusCode: response.statusCode,
    );
  }
  return body['data'] as List<dynamic>? ?? [];
}

Never rethrowDio(DioException error) {
  final data = error.response?.data;
  if (data is Map<String, dynamic> && data['error'] is Map<String, dynamic>) {
    final apiError = data['error'] as Map<String, dynamic>;
    throw ApiException(
      code: apiError['code'] as String? ?? 'REQUEST_FAILED',
      message: apiError['message'] as String? ?? 'Request failed.',
      statusCode: error.response?.statusCode,
    );
  }
  throw ApiException(
    code: 'NETWORK_ERROR',
    message: 'Unable to reach the server. Changes will sync when connection returns.',
    statusCode: error.response?.statusCode,
  );
}

String encodeJson(Map<String, dynamic> value) => jsonEncode(value);

Map<String, dynamic> decodeJson(String value) =>
    jsonDecode(value) as Map<String, dynamic>;
