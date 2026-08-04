import 'package:flutter/material.dart';

import '../services/api_client.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({
    super.key,
    required this.apiClient,
    required this.onLogout,
  });

  final ApiClient apiClient;
  final VoidCallback onLogout;

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Map<String, dynamic>? _profile;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final response = await widget.apiClient.getJson('/drivers/me');
    setState(() => _profile = response['data'] as Map<String, dynamic>);
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        if (_profile != null) ...[
          Text('Phone: ${_profile!['phone'] ?? '—'}'),
          Text('License: ${_profile!['driving_license'] ?? '—'}'),
        ],
        const SizedBox(height: 24),
        OutlinedButton(onPressed: widget.onLogout, child: const Text('Logout')),
      ],
    );
  }
}
