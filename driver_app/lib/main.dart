import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'core/connectivity/connectivity_service.dart';
import 'core/storage/hive_boxes.dart';
import 'features/auth/providers/auth_controller.dart';
import 'features/sync/providers/sync_providers.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await HiveBoxes.init();
  runApp(const ProviderScope(child: BootstrapApp()));
}

class BootstrapApp extends ConsumerStatefulWidget {
  const BootstrapApp({super.key});

  @override
  ConsumerState<BootstrapApp> createState() => _BootstrapAppState();
}

class _BootstrapAppState extends ConsumerState<BootstrapApp> {
  @override
  Widget build(BuildContext context) {
    ref.listen<bool>(isOnlineProvider, (previous, next) {
      if (next && previous == false) {
        ref.read(syncControllerProvider).syncIfOnline();
      }
    });

    final auth = ref.watch(authControllerProvider);
    if (!auth.ready) {
      return MaterialApp(
        home: Scaffold(
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: const [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Starting ProDrive Driver…'),
              ],
            ),
          ),
        ),
      );
    }
    return const ProDriveDriverApp();
  }
}
