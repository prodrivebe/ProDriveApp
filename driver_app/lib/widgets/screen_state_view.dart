import 'package:flutter/material.dart';

enum ViewState { loading, success, empty, error }

class ScreenStateView extends StatelessWidget {
  const ScreenStateView({
    super.key,
    required this.state,
    required this.onRetry,
    this.errorMessage,
    this.emptyMessage = 'Nothing to show yet.',
    required this.child,
  });

  final ViewState state;
  final VoidCallback onRetry;
  final String? errorMessage;
  final String emptyMessage;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    switch (state) {
      case ViewState.loading:
        return const Center(child: CircularProgressIndicator());
      case ViewState.empty:
        return _MessageView(
          icon: Icons.inbox_outlined,
          message: emptyMessage,
          onRetry: onRetry,
        );
      case ViewState.error:
        return _MessageView(
          icon: Icons.error_outline,
          message: errorMessage ?? 'Something went wrong.',
          onRetry: onRetry,
        );
      case ViewState.success:
        return child;
    }
  }
}

class _MessageView extends StatelessWidget {
  const _MessageView({
    required this.icon,
    required this.message,
    required this.onRetry,
  });

  final IconData icon;
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 48, color: Theme.of(context).colorScheme.error),
            const SizedBox(height: 16),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}
