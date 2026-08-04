import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../services/driver_repository.dart';
import 'order_detail_screen.dart';

class OrdersScreen extends StatefulWidget {
  const OrdersScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<OrdersScreen> createState() => _OrdersScreenState();
}

class _OrdersScreenState extends State<OrdersScreen> {
  List<dynamic> _orders = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final orders = await DriverRepository(widget.apiClient).orders();
    setState(() => _orders = orders);
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        itemCount: _orders.length,
        itemBuilder: (context, index) {
          final order = _orders[index] as Map<String, dynamic>;
          return ListTile(
            title: Text(order['order_number'] as String),
            subtitle: Text(order['status'] as String),
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => OrderDetailScreen(
                    apiClient: widget.apiClient,
                    orderId: order['id'] as String,
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
