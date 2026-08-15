import 'package:flutter/foundation.dart';

/// API configuration for the driver app.
class ApiConfig {
  ApiConfig._();

  static const String productionBaseUrl = 'https://api.prodriveservice.eu/api/v1';
  static const String devBaseUrl = 'http://10.0.2.2:8000/api/v1';

  static String get baseUrl {
    const override = String.fromEnvironment('API_BASE_URL');
    if (override.isNotEmpty) {
      return override;
    }
    if (kReleaseMode) {
      return productionBaseUrl;
    }
    return devBaseUrl;
  }

  static String resolveUploadUrl(String path) {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    final origin = baseUrl.replaceAll(RegExp(r'/api/v1/?$'), '');
    final normalized = path.startsWith('/') ? path : '/$path';
    return '$origin$normalized';
  }
}
