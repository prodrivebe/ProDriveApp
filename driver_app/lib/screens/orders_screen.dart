import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../services/driver_repository.dart';
import '../widgets/screen_state_view.dart';
import 'order_detail_screen.dart';

class OrdersScreen extends StatefulWidget {
  const OrdersScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<OrdersScreen> createState() => _OrdersScreenState();
}

class _OrdersScreenState extends State<OrdersScreen> {
  ViewState _state = ViewState.loading;
  List<dynamic> _orders = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _state = ViewState.loading;
      _error = null;
    });
    try {
      final orders = await DriverRepository(widget.apiClient).orders();
      if (!mounted) return;
      setState(() {
        _orders = orders;
        _state = orders.isEmpty ? ViewState.empty : ViewState.success;
      });
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
    return Scaffold(
      appBar: AppBar(title: const Text('Orders')),
      body: ScreenStateView(
        state: _state,
        errorMessage: _error,
        emptyMessage: 'No orders assigned.',
        onRetry: _load,
        child: RefreshIndicator(
          onRefresh: _load,
          child: ListView.builder(
            itemCount: _orders.length,
            itemBuilder: (context, index) {
              final order = _orders[index] as Map<String, dynamic>;
              return ListTile(
                title: Text(order['order_number'] as String),
                subtitle: Text(order['status'] as String),
                onTap: () => openOrderWorkflow(
                  context,
                  apiClient: widget.apiClient,
                  orderId: order['id'] as String,
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}
