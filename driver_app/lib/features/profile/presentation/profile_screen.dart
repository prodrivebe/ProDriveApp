import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/widgets/common_widgets.dart';
import '../../auth/providers/auth_controller.dart';
import '../../auth/providers/auth_providers.dart';
import '../../sync/providers/sync_providers.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userAsync = ref.watch(userProfileProvider);
    final driverAsync = ref.watch(driverProfileProvider);
    final pendingAsync = ref.watch(pendingQueueCountProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: Column(
        children: [
          const OfflineBanner(),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                AsyncValueWidget(
                  value: userAsync,
                  onRetry: () => ref.invalidate(userProfileProvider),
                  data: (user) => Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(user.fullName, style: Theme.of(context).textTheme.headlineSmall),
                      Text(user.email),
                      Text('Role: ${user.role}'),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                driverAsync.when(
                  loading: () => const CircularProgressIndicator(),
                  error: (error, _) => Text(error.toString()),
                  data: (driver) => SectionCard(
                    title: 'Driver details',
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Phone: ${driver.phone ?? '—'}'),
                        Text('License: ${driver.drivingLicense ?? '—'}'),
                        Text('Status: ${driver.active ? 'Active' : 'Inactive'}'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                pendingAsync.when(
                  data: (count) => SectionCard(
                    title: 'Offline queue',
                    child: Text('$count pending operations'),
                  ),
                  loading: () => const SizedBox.shrink(),
                  error: (_, __) => const SizedBox.shrink(),
                ),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: () async {
                    await ref.read(syncControllerProvider).syncIfOnline();
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Sync attempted')),
                      );
                    }
                  },
                  child: const Text('Sync now'),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () async {
                    await ref.read(authControllerProvider).logout();
                  },
                  child: const Text('Sign out'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
