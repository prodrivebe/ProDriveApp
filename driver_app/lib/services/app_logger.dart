import 'package:flutter/foundation.dart';

/// Lightweight debug logging — never logs tokens or passwords.
class AppLogger {
  AppLogger._();

  static void debug(String message) {
    if (kDebugMode) {
      debugPrint('[ProDrive] $message');
    }
  }

  static void workflow({
    required String orderId,
    required String status,
    String? action,
    String? target,
    String? detail,
  }) {
    debug(
      'workflow order=$orderId status=$status'
      '${action == null ? '' : ' action=$action'}'
      '${target == null ? '' : ' target=$target'}'
      '${detail == null ? '' : ' $detail'}',
    );
  }

  static void api(String method, String path, {int? status, String? detail}) {
    debug(
      'api $method $path'
      '${status == null ? '' : ' status=$status'}'
      '${detail == null ? '' : ' $detail'}',
    );
  }

  static void cmr(String message) {
    debug('cmr $message');
  }
}
