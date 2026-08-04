import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../services/driver_repository.dart';
import 'order_detail_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Map<String, dynamic>? _home;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final home = await DriverRepository(widget.apiClient).home();
      setState(() {
        _home = home;
        _error = null;
      });
    } catch (error) {
      setState(() => _error = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Center(child: Text(_error!));
    }
    if (_home == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final currentOrder = _home!['current_order'] as Map<String, dynamic>?;
    return RefreshIndicator(
      onRefresh: _load,
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
                  Text(
                    'Next action',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(_home!['next_action'] as String),
                ],
              ),
            ),
          ),
          if (currentOrder != null) ...[
            const SizedBox(height: 16),
            ListTile(
              title: Text(currentOrder['order_number'] as String),
              subtitle: Text(currentOrder['status'] as String),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => OrderDetailScreen(
                      apiClient: widget.apiClient,
                      orderId: currentOrder['id'] as String,
                    ),
                  ),
                );
              },
            ),
          ],
        ],
      ),
    );
  }
}
