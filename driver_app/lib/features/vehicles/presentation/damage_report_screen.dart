import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/connectivity/connectivity_service.dart';
import '../../../core/network/api_exception.dart';
import '../../../shared/widgets/common_widgets.dart';
import '../../photos/providers/upload_providers.dart';
import '../providers/vehicle_detail_providers.dart';

class DamageReportScreen extends ConsumerStatefulWidget {
  const DamageReportScreen({
    super.key,
    required this.orderId,
    required this.vehicleId,
  });

  final String orderId;
  final String vehicleId;

  @override
  ConsumerState<DamageReportScreen> createState() => _DamageReportScreenState();
}

class _DamageReportScreenState extends ConsumerState<DamageReportScreen> {
  final _descriptionController = TextEditingController();
  final _locationController = TextEditingController();
  String _damageType = 'SCRATCH';
  String _severity = 'MINOR';
  bool _submitting = false;
  String? _message;

  @override
  void dispose() {
    _descriptionController.dispose();
    _locationController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _submitting = true;
      _message = null;
    });

    try {
      final online = ref.read(isOnlineProvider);
      await ref.read(uploadControllerProvider).submitDamage(
            orderId: widget.orderId,
            vehicleId: widget.vehicleId,
            damageType: _damageType,
            severity: _severity,
            description: _descriptionController.text.trim(),
            location: _locationController.text.trim(),
          );
      setState(() => _message = online ? 'Damage report submitted.' : 'Report queued for sync.');
      ref.invalidate(vehicleDamageProvider((orderId: widget.orderId, vehicleId: widget.vehicleId)));
    } on ApiException catch (error) {
      setState(() => _message = error.userMessage);
    } finally {
      setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Damage report')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const OfflineBanner(),
          DropdownButtonFormField<String>(
            value: _damageType,
            decoration: const InputDecoration(labelText: 'Damage type'),
            items: const [
              DropdownMenuItem(value: 'SCRATCH', child: Text('Scratch')),
              DropdownMenuItem(value: 'DENT', child: Text('Dent')),
              DropdownMenuItem(value: 'BROKEN', child: Text('Broken part')),
              DropdownMenuItem(value: 'OTHER', child: Text('Other')),
            ],
            onChanged: (value) => setState(() => _damageType = value!),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            value: _severity,
            decoration: const InputDecoration(labelText: 'Severity'),
            items: const [
              DropdownMenuItem(value: 'MINOR', child: Text('Minor')),
              DropdownMenuItem(value: 'MODERATE', child: Text('Moderate')),
              DropdownMenuItem(value: 'SEVERE', child: Text('Severe')),
            ],
            onChanged: (value) => setState(() => _severity = value!),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _locationController,
            decoration: const InputDecoration(labelText: 'Location on vehicle'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _descriptionController,
            decoration: const InputDecoration(labelText: 'Description'),
            maxLines: 3,
          ),
          if (_message != null) ...[
            const SizedBox(height: 12),
            Text(_message!),
          ],
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _submitting ? null : _submit,
            child: Text(_submitting ? 'Submitting…' : 'Submit damage report'),
          ),
        ],
      ),
    );
  }
}
