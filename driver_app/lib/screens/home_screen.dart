import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../services/driver_repository.dart';
import '../services/workflow_helper.dart';
import '../widgets/screen_state_view.dart';
import 'order_detail_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({
    super.key,
    required this.apiClient,
    this.onActiveOrderFound,
  });

  final ApiClient apiClient;
  final void Function(String orderId)? onActiveOrderFound;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  ViewState _state = ViewState.loading;
  Map<String, dynamic>? _home;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load(resumeWorkflow: true);
  }

  Future<void> _load({bool resumeWorkflow = false}) async {
    setState(() {
      _state = ViewState.loading;
      _error = null;
    });
    try {
      final home = await DriverRepository(widget.apiClient).home();
      if (!mounted) return;
      setState(() {
        _home = home;
        _state = ViewState.success;
      });

      final currentOrder = home['current_order'] as Map<String, dynamic>?;
      if (resumeWorkflow &&
          currentOrder != null &&
          WorkflowHelper.isActiveStatus(currentOrder['status'] as String?)) {
        widget.onActiveOrderFound?.call(currentOrder['id'] as String);
      }
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error.toString();
        _state = ViewState.error;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return ScreenStateView(
      state: _state,
      errorMessage: _error,
      onRetry: () => _load(),
      emptyMessage: 'Home data unavailable.',
      child: _buildContent(context),
    );
  }

  Widget _buildContent(BuildContext context) {
    final currentOrder = _home!['current_order'] as Map<String, dynamic>?;

    return RefreshIndicator(
      onRefresh: () => _load(),
      child: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Text(
            'Hello, ${_home!['user_name']}',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          Text('Truck: ${_home!['truck_label'] ?? '—'}'),
          Text('Trailer: ${_home!['trailer_label'] ?? '—'}'),
          const SizedBox(height: 24),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Next action', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  Text(_home!['next_action'] as String),
                ],
              ),
            ),
          ),
          if (currentOrder != null) ...[
            const SizedBox(height: 16),
            Card(
              child: ListTile(
                title: Text(currentOrder['order_number'] as String),
                subtitle: Text(currentOrder['status'] as String),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => openOrderWorkflow(
                  context,
                  apiClient: widget.apiClient,
                  orderId: currentOrder['id'] as String,
                ),
              ),
            ),
            const SizedBox(height: 8),
            FilledButton(
              onPressed: () => openOrderWorkflow(
                context,
                apiClient: widget.apiClient,
                orderId: currentOrder['id'] as String,
                replace: true,
              ),
              child: const Text('Continue active order'),
            ),
          ],
        ],
      ),
    );
  }
}
