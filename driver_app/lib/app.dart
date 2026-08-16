import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/connectivity/connectivity_service.dart';
import 'core/realtime/realtime_providers.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/providers/auth_controller.dart';
import 'features/sync/providers/sync_providers.dart';

class ProDriveDriverApp extends ConsumerWidget {
  const ProDriveDriverApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen<bool>(isOnlineProvider, (previous, next) {
      if (next && previous == false) {
        ref.read(syncControllerProvider).syncIfOnline();
      }
    });
    ref.listen<AuthController>(authControllerProvider, (previous, next) {
      if (next.authenticated) {
        ref.read(realtimeControllerProvider).connect();
      } else if (next.ready) {
        ref.read(realtimeControllerProvider).disconnect();
      }
    });

    final router = ref.watch(appRouterProvider);
    return MaterialApp.router(
      title: 'ProDrive Driver',
      theme: AppTheme.light(),
      routerConfig: router,
    );
  }
}
