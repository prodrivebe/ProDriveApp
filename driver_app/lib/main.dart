import 'package:flutter/material.dart';

import 'screens/login_screen.dart';
import 'screens/main_shell.dart';
import 'services/api_client.dart';

void main() {
  runApp(const ProDriveDriverApp());
}

class ProDriveDriverApp extends StatelessWidget {
  const ProDriveDriverApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ProDrive Driver',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1565C0)),
        useMaterial3: true,
      ),
      home: AppBootstrap(apiClient: ApiClient()),
    );
  }
}

class AppBootstrap extends StatefulWidget {
  const AppBootstrap({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  State<AppBootstrap> createState() => _AppBootstrapState();
}

class _AppBootstrapState extends State<AppBootstrap> {
  bool _loading = true;
  bool _loggedIn = false;

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    await widget.apiClient.loadToken();
    setState(() {
      _loggedIn = widget.apiClient.isAuthenticated;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (!_loggedIn) {
      return LoginScreen(
        apiClient: widget.apiClient,
        onLoggedIn: () => setState(() => _loggedIn = true),
      );
    }
    return MainShell(
      apiClient: widget.apiClient,
      onLogout: () => setState(() => _loggedIn = false),
    );
  }
}
