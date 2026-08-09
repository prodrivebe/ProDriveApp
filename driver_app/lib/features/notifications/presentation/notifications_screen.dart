import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/widgets/common_widgets.dart';
import '../providers/notifications_providers.dart';

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notificationsAsync = ref.watch(notificationsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Notifications')),
      body: Column(
        children: [
          const OfflineBanner(),
          Expanded(
            child: RefreshIndicator(
              onRefresh: () async => ref.invalidate(notificationsProvider),
              child: AsyncValueWidget(
                value: notificationsAsync,
                onRetry: () => ref.invalidate(notificationsProvider),
                data: (items) {
                  if (items.isEmpty) {
                    return ListView(
                      children: const [
                        SizedBox(height: 120),
                        Center(child: Text('No notifications.')),
                      ],
                    );
                  }

                  return ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: items.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      final item = items[index];
                      final unread = item.readAt == null;
                      return ListTile(
                        title: Text(item.title, style: TextStyle(fontWeight: unread ? FontWeight.bold : FontWeight.normal)),
                        subtitle: Text(item.message),
                        trailing: unread ? const Icon(Icons.circle, size: 10) : null,
                        onTap: () async {
                          if (unread) {
                            await ref.read(notificationsRepositoryProvider).markRead(item.id);
                            ref.invalidate(notificationsProvider);
                          }
                        },
                      );
                    },
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}
