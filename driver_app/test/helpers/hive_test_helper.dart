import 'dart:io';

import 'package:hive/hive.dart';

Future<void> initTestHive() async {
  final dir = Directory.systemTemp.createTempSync('prodrive_driver_test_');
  Hive.init(dir.path);
  await Hive.openBox<String>('operational_cache');
  await Hive.openBox<String>('offline_queue');
}

Future<void> closeTestHive() async {
  await Hive.box<String>('operational_cache').clear();
  await Hive.box<String>('offline_queue').clear();
  await Hive.close();
}
