import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/auth_repository.dart';
import 'auth_providers.dart';

class AuthController extends ChangeNotifier {
  AuthController(this._ref) {
    _bootstrap();
  }

  final Ref _ref;
  bool _ready = false;
  bool _authenticated = false;

  bool get ready => _ready;
  bool get authenticated => _authenticated;

  Future<void> _bootstrap() async {
    try {
      final tokens = await _ref.read(authRepositoryProvider).currentTokens();
      _ref.read(authTokensProvider.notifier).state = tokens;
      _authenticated = tokens != null;
    } catch (error, stackTrace) {
      debugPrint('Auth bootstrap failed: $error\n$stackTrace');
      _authenticated = false;
    } finally {
      _ready = true;
      notifyListeners();
    }
  }

  Future<void> login(String username, String password) async {
    final tokens = await _ref.read(authRepositoryProvider).login(username, password);
    _ref.read(authTokensProvider.notifier).state = tokens;
    _authenticated = true;
    notifyListeners();
  }

  Future<void> logout() async {
    await _ref.read(authRepositoryProvider).logout();
    _ref.read(authTokensProvider.notifier).state = null;
    _authenticated = false;
    notifyListeners();
  }
}

final authControllerProvider = ChangeNotifierProvider<AuthController>((ref) {
  final controller = AuthController(ref);
  ref.onDispose(controller.dispose);
  return controller;
});
