import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'core/storage/hive_boxes.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await HiveBoxes.init();
  } catch (error, stackTrace) {
    debugPrint('Hive initialization failed: $error\n$stackTrace');
  }
  runApp(const ProviderScope(child: ProDriveDriverApp()));
}
