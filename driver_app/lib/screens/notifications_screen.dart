import 'package:flutter/material.dart';

import '../services/api_client.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  List<dynamic> _items = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final response = await widget.apiClient.getJson('/notifications');
    setState(() => _items = response['data'] as List<dynamic>);
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        itemCount: _items.length,
        itemBuilder: (context, index) {
          final item = _items[index] as Map<String, dynamic>;
          return ListTile(
            title: Text(item['title'] as String),
            subtitle: Text(item['message'] as String),
          );
        },
      ),
    );
  }
}
