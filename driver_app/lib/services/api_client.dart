import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';
import 'app_logger.dart';

class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;
  String? _accessToken;

  bool get isAuthenticated => _accessToken != null;

  Future<void> loadToken() async {
    final prefs = await SharedPreferences.getInstance();
    _accessToken = prefs.getString('access_token');
  }

  Future<void> saveToken(String token) async {
    _accessToken = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', token);
  }

  Future<void> clearToken() async {
    _accessToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
  }

  Map<String, String> _headers({bool jsonBody = false, Map<String, String>? extra}) {
    final headers = <String, String>{
      if (jsonBody) 'Content-Type': 'application/json',
      ...?extra,
    };
    if (_accessToken != null) {
      headers['Authorization'] = 'Bearer $_accessToken';
    }
    return headers;
  }

  Future<Map<String, dynamic>> postJson(
    String path,
    Map<String, dynamic> body,
  ) async {
    AppLogger.api('POST', path);
    final response = await _client.post(
      Uri.parse('${ApiConfig.baseUrl}$path'),
      headers: _headers(jsonBody: true),
      body: jsonEncode(body),
    );
    return _decode(response, path: path);
  }

  Future<Map<String, dynamic>> getJson(String path) async {
    AppLogger.api('GET', path);
    final response = await _client.get(
      Uri.parse('${ApiConfig.baseUrl}$path'),
      headers: _headers(),
    );
    return _decode(response, path: path);
  }

  Future<Map<String, dynamic>> postAction(String path) async {
    AppLogger.api('POST', path);
    final response = await _client.post(
      Uri.parse('${ApiConfig.baseUrl}$path'),
      headers: _headers(),
    );
    return _decode(response, path: path);
  }

  Future<Uint8List> getBytes(String url) async {
    AppLogger.api('GET', url, detail: 'bytes');
    final response = await _client.get(
      Uri.parse(url),
      headers: _headers(),
    );
    if (response.statusCode >= 400) {
      throw ApiException('Failed to download file (${response.statusCode}).', statusCode: response.statusCode);
    }
    return response.bodyBytes;
  }

  Future<Map<String, dynamic>> uploadMultipart({
    required String path,
    required String fieldName,
    required String fileName,
    required Uint8List bytes,
  }) async {
    AppLogger.api('POST', path, detail: 'multipart $fileName');
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('${ApiConfig.baseUrl}$path'),
    );
    request.headers.addAll(_headers());
    request.files.add(
      http.MultipartFile.fromBytes(
        fieldName,
        bytes,
        filename: fileName,
      ),
    );
    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);
    return _decode(response, path: path);
  }

  Map<String, dynamic> _decode(http.Response response, {required String path}) {
    AppLogger.api(response.request?.method ?? 'HTTP', path, status: response.statusCode);

    Map<String, dynamic> body;
    try {
      body = jsonDecode(response.body) as Map<String, dynamic>;
    } catch (_) {
      if (response.statusCode >= 400) {
        throw ApiException('Request failed (${response.statusCode}).', statusCode: response.statusCode);
      }
      throw ApiException('Invalid server response.');
    }

    if (response.statusCode >= 400) {
      final message = body['error']?['message'] as String? ?? 'Request failed';
      throw ApiException(message, statusCode: response.statusCode);
    }
    return body;
  }
}
