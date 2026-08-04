import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

/// Minimal offline action queue — syncs when connectivity returns.
class OfflineQueue {
  static const _storageKey = 'offline_queue';

  Future<List<Map<String, dynamic>>> pendingActions() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList(_storageKey) ?? [];
    return raw.map((item) => jsonDecode(item) as Map<String, dynamic>).toList();
  }

  Future<void> enqueue(String method, String path, {Map<String, dynamic>? body}) async {
    final prefs = await SharedPreferences.getInstance();
    final items = prefs.getStringList(_storageKey) ?? [];
    items.add(jsonEncode({'method': method, 'path': path, 'body': body}));
    await prefs.setStringList(_storageKey, items);
  }

  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_storageKey);
  }
}
