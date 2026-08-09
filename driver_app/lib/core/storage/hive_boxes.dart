import 'package:hive_flutter/hive_flutter.dart';

class HiveBoxes {
  static const cache = 'operational_cache';
  static const queue = 'offline_queue';

  static Future<void> init() async {
    await Hive.initFlutter();
    await Hive.openBox<String>(cache);
    await Hive.openBox<String>(queue);
  }

  static Box<String> get cacheBox => Hive.box<String>(cache);
  static Box<String> get queueBox => Hive.box<String>(queue);
}
