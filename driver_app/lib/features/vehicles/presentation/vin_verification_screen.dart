import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/connectivity/connectivity_service.dart';
import '../../../core/network/api_exception.dart';
import '../../../shared/widgets/common_widgets.dart';
import '../../orders/providers/orders_providers.dart';
import '../../photos/providers/upload_providers.dart';
import '../providers/vehicle_detail_providers.dart';

class VinVerificationScreen extends ConsumerStatefulWidget {
  const VinVerificationScreen({
    super.key,
    required this.orderId,
    required this.vehicleId,
  });

  final String orderId;
  final String vehicleId;

  @override
  ConsumerState<VinVerificationScreen> createState() => _VinVerificationScreenState();
}

class _VinVerificationScreenState extends ConsumerState<VinVerificationScreen> {
  late final TextEditingController _vinController;
  bool _loading = false;
  String? _message;
  bool _initializedVin = false;

  @override
  void initState() {
    super.initState();
    _vinController = TextEditingController();
  }

  @override
  void dispose() {
    _vinController.dispose();
    super.dispose();
  }

  Future<void> _confirm() async {
    final vin = _vinController.text.trim().toUpperCase();
    if (vin.length < 11) {
      setState(() => _message = 'Enter a valid VIN (17 characters recommended).');
      return;
    }

    setState(() {
      _loading = true;
      _message = null;
    });

    try {
      final online = ref.read(isOnlineProvider);
      await ref.read(uploadControllerProvider).verifyVin(
            orderId: widget.orderId,
            vehicleId: widget.vehicleId,
            vin: vin,
          );
      if (mounted) {
        setState(() => _message = online ? 'VIN verified.' : 'Verification queued for sync.');
        ref.invalidate(orderDetailProvider(widget.orderId));
        ref.invalidate(vinHistoryProvider((orderId: widget.orderId, vehicleId: widget.vehicleId)));
      }
    } on ApiException catch (error) {
      setState(() => _message = error.userMessage);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _updateVin() async {
    final vin = _vinController.text.trim().toUpperCase();
    if (vin.isEmpty) return;
    setState(() => _loading = true);
    try {
      final online = ref.read(isOnlineProvider);
      await ref.read(uploadControllerProvider).updateVin(
            orderId: widget.orderId,
            vehicleId: widget.vehicleId,
            vin: vin,
          );
      if (mounted) {
        setState(() => _message = online ? 'VIN updated.' : 'VIN update queued.');
        ref.invalidate(orderDetailProvider(widget.orderId));
      }
    } on ApiException catch (error) {
      setState(() => _message = error.userMessage);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final orderAsync = ref.watch(orderDetailProvider(widget.orderId));
    final historyAsync =
        ref.watch(vinHistoryProvider((orderId: widget.orderId, vehicleId: widget.vehicleId)));

    return Scaffold(
      appBar: AppBar(title: const Text('VIN verification')),
      body: AsyncValueWidget(
        value: orderAsync,
        data: (order) {
          final vehicle = order.vehicles.firstWhere((item) => item.id == widget.vehicleId);
          if (!_initializedVin && vehicle.vin != null) {
            _vinController.text = vehicle.vin!;
            _initializedVin = true;
          }

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const OfflineBanner(),
              Text('Confirm or edit the vehicle VIN before loading.'),
              const SizedBox(height: 16),
              TextField(
                controller: _vinController,
                decoration: const InputDecoration(
                  labelText: 'VIN',
                  helperText: 'Manual confirmation — no OCR',
                ),
                textCapitalization: TextCapitalization.characters,
              ),
              if (_message != null) ...[
                const SizedBox(height: 12),
                Text(_message!),
              ],
              const SizedBox(height: 16),
              FilledButton(
                onPressed: _loading ? null : _confirm,
                child: Text(_loading ? 'Saving…' : 'Confirm VIN'),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: _loading ? null : _updateVin,
                child: const Text('Save edited VIN'),
              ),
              const SizedBox(height: 24),
              SectionCard(
                title: 'VIN history',
                child: historyAsync.when(
                  loading: () => const CircularProgressIndicator(),
                  error: (error, _) => Text(error.toString()),
                  data: (entries) => entries.isEmpty
                      ? const Text('No verification history yet.')
                      : Column(
                          children: entries
                              .map(
                                (entry) => ListTile(
                                  contentPadding: EdgeInsets.zero,
                                  title: Text(entry.verifiedVin),
                                  subtitle: Text('${entry.action} • ${entry.verifiedAt}'),
                                ),
                              )
                              .toList(),
                        ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
