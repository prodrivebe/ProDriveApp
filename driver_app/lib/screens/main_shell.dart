import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../services/auth_service.dart';
import 'home_screen.dart';
import 'notifications_screen.dart';
import 'order_detail_screen.dart';
import 'orders_screen.dart';
import 'profile_screen.dart';

class MainShell extends StatefulWidget {
  const MainShell({
    super.key,
    required this.apiClient,
    required this.onLogout,
  });

  final ApiClient apiClient;
  final VoidCallback onLogout;

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _index = 0;
  bool _resumedWorkflow = false;

  void _resumeActiveOrder(String orderId) {
    if (_resumedWorkflow || !mounted) return;
    _resumedWorkflow = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      openOrderWorkflow(
        context,
        apiClient: widget.apiClient,
        orderId: orderId,
        replace: false,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      HomeScreen(
        apiClient: widget.apiClient,
        onActiveOrderFound: _resumeActiveOrder,
      ),
      OrdersScreen(apiClient: widget.apiClient),
      NotificationsScreen(apiClient: widget.apiClient),
      ProfileScreen(
        apiClient: widget.apiClient,
        onLogout: () async {
          await AuthService(widget.apiClient).logout();
          widget.onLogout();
        },
      ),
    ];

    return Scaffold(
      body: pages[_index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.list_alt), label: 'Orders'),
          NavigationDestination(icon: Icon(Icons.notifications), label: 'Alerts'),
          NavigationDestination(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}
