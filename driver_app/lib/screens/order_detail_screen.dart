import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../services/api_client.dart';
import '../services/driver_repository.dart';

class OrderDetailScreen extends StatefulWidget {
  const OrderDetailScreen({
    super.key,
    required this.apiClient,
    required this.orderId,
  });

  final ApiClient apiClient;
  final String orderId;

  @override
  State<OrderDetailScreen> createState() => _OrderDetailScreenState();
}

class _OrderDetailScreenState extends State<OrderDetailScreen> {
  Map<String, dynamic>? _order;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final order = await DriverRepository(widget.apiClient).orderDetail(widget.orderId);
    setState(() => _order = order);
  }

  Future<void> _action(String name) async {
    await DriverRepository(widget.apiClient).workflowAction(widget.orderId, name);
    await _load();
  }

  Future<void> _navigate() async {
    final stops = _order?['stops'] as List<dynamic>? ?? [];
    if (stops.isEmpty) return;
    final stop = stops.first as Map<String, dynamic>;
    final city = stop['city'] as String? ?? '';
    final uri = Uri.parse('https://www.google.com/maps/search/?api=1&query=$city');
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    if (_order == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final status = _order!['status'] as String;
    return Scaffold(
      appBar: AppBar(title: Text(_order!['order_number'] as String)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Status: $status'),
          const SizedBox(height: 16),
          FilledButton(onPressed: _navigate, child: const Text('Navigate')),
          const SizedBox(height: 8),
          if (status == 'ASSIGNED')
            FilledButton(onPressed: () => _action('accept'), child: const Text('Accept')),
          if (status == 'ACCEPTED')
            FilledButton(
              onPressed: () => _action('arrive-pickup'),
              child: const Text('Arrived at pickup'),
            ),
          if (status == 'LOADING')
            FilledButton(
              onPressed: () => _action('complete-loading'),
              child: const Text('Complete loading'),
            ),
          if (status == 'IN_TRANSIT')
            FilledButton(
              onPressed: () => _action('arrive-delivery'),
              child: const Text('Arrived at delivery'),
            ),
          if (status == 'DELIVERING')
            FilledButton(
              onPressed: () => _action('complete-delivery'),
              child: const Text('Complete delivery'),
            ),
        ],
      ),
    );
  }
}
