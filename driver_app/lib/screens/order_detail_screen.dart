import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/api_client.dart';
import '../services/app_logger.dart';
import '../services/cmr_file_service.dart';
import '../services/driver_repository.dart';
import '../services/maps_launcher.dart';
import '../services/workflow_helper.dart';
import '../widgets/screen_state_view.dart';

class OrderDetailScreen extends StatefulWidget {
  const OrderDetailScreen({
    super.key,
    required this.apiClient,
    required this.orderId,
    this.embedded = false,
  });

  final ApiClient apiClient;
  final String orderId;
  final bool embedded;

  @override
  State<OrderDetailScreen> createState() => _OrderDetailScreenState();
}

class _OrderDetailScreenState extends State<OrderDetailScreen> {
  ViewState _state = ViewState.loading;
  Map<String, dynamic>? _order;
  Map<String, dynamic>? _cmr;
  File? _cmrFile;
  String? _error;
  bool _actionBusy = false;
  bool _cmrBusy = false;

  DriverRepository get repo => DriverRepository(widget.apiClient);

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    if (!mounted) return;
    setState(() {
      _state = ViewState.loading;
      _error = null;
    });

    try {
      final order = await repo.orderDetail(widget.orderId);
      Map<String, dynamic>? cmr;
      if (WorkflowHelper.showCmrSection(order['status'] as String)) {
        cmr = await repo.fetchCmr(widget.orderId);
      }

      if (!mounted) return;
      AppLogger.workflow(
        orderId: widget.orderId,
        status: order['status'] as String,
        detail: 'loaded',
      );
      setState(() {
        _order = order;
        _cmr = cmr;
        _state = ViewState.success;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error.toString();
        _state = ViewState.error;
      });
    }
  }

  Future<void> _runAction(String action) async {
    if (_actionBusy) return;
    setState(() => _actionBusy = true);
    try {
      final updated = await repo.workflowAction(widget.orderId, action);
      if (!mounted) return;
      setState(() => _order = updated);
      await _load();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Updated: ${updated['status']}')),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    } finally {
      if (mounted) setState(() => _actionBusy = false);
    }
  }

  Future<void> _navigateToDelivery() async {
    final stops = _order?['stops'] as List<dynamic>? ?? [];
    final delivery = WorkflowHelper.deliveryStop(stops);
    final address = WorkflowHelper.stopAddress(delivery);
    try {
      await MapsLauncher.openNavigation(
        address: address,
        latitude: delivery?['latitude']?.toString(),
        longitude: delivery?['longitude']?.toString(),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    }
  }

  Future<File?> _ensureCmrFile() async {
    if (_cmrFile != null && _cmrFile!.existsSync()) {
      return _cmrFile;
    }
    if (_cmr == null) {
      throw Exception('No CMR available yet.');
    }
    final bytes = await repo.downloadCmrBytes(_cmr!);
    final file = await CmrFileService.savePdf(
      bytes: bytes,
      orderNumber: _order?['order_number'] as String? ?? widget.orderId,
    );
    _cmrFile = file;
    return file;
  }

  Future<void> _loadCmr() async {
    if (_cmrBusy) return;
    setState(() => _cmrBusy = true);
    try {
      final cmr = await repo.fetchCmr(widget.orderId);
      if (!mounted) return;
      setState(() {
        _cmr = cmr;
        _cmrFile = null;
      });
      if (cmr == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No CMR generated yet.')),
        );
      }
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    } finally {
      if (mounted) setState(() => _cmrBusy = false);
    }
  }

  Future<void> _generateCmr() async {
    if (_cmrBusy) return;
    setState(() => _cmrBusy = true);
    try {
      final cmr = await repo.generateCmr(widget.orderId);
      if (!mounted) return;
      setState(() {
        _cmr = cmr;
        _cmrFile = null;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('CMR generated.')),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    } finally {
      if (mounted) setState(() => _cmrBusy = false);
    }
  }

  Future<void> _previewCmr() async {
    if (_cmrBusy) return;
    setState(() => _cmrBusy = true);
    try {
      final file = await _ensureCmrFile();
      await CmrFileService.preview(file!);
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    } finally {
      if (mounted) setState(() => _cmrBusy = false);
    }
  }

  Future<void> _shareCmr() async {
    if (_cmrBusy) return;
    setState(() => _cmrBusy = true);
    try {
      final file = await _ensureCmrFile();
      await CmrFileService.share(file!);
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    } finally {
      if (mounted) setState(() => _cmrBusy = false);
    }
  }

  Future<void> _uploadSignedCmrFromFile() async {
    if (_cmrBusy) return;
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'jpg', 'jpeg', 'png'],
      withData: true,
    );
    if (picked == null || picked.files.isEmpty) return;
    final file = picked.files.first;
    final bytes = file.bytes;
    if (bytes == null) return;

    setState(() => _cmrBusy = true);
    try {
      await repo.uploadSignedCmr(
        orderId: widget.orderId,
        bytes: bytes,
        fileName: file.name,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Signed CMR uploaded.')),
      );
      await _load();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    } finally {
      if (mounted) setState(() => _cmrBusy = false);
    }
  }

  Future<void> _uploadSignedCmr(ImageSource source) async {
    if (_cmrBusy) return;
    final picker = ImagePicker();
    XFile? picked;
    if (source == ImageSource.gallery) {
      picked = await picker.pickImage(source: ImageSource.gallery);
    } else {
      picked = await picker.pickImage(source: ImageSource.camera);
    }
    if (picked == null) return;

    setState(() => _cmrBusy = true);
    try {
      final bytes = await picked.readAsBytes();
      await repo.uploadSignedCmr(
        orderId: widget.orderId,
        bytes: bytes,
        fileName: picked.name.isNotEmpty ? picked.name : 'signed_cmr.jpg',
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Signed CMR uploaded.')),
      );
      await _load();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    } finally {
      if (mounted) setState(() => _cmrBusy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final body = ScreenStateView(
      state: _state,
      errorMessage: _error,
      onRetry: _load,
      child: _buildContent(context),
    );

    if (widget.embedded) {
      return body;
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(_order?['order_number'] as String? ?? 'Active order'),
        automaticallyImplyLeading: !WorkflowHelper.isActiveStatus(_order?['status'] as String?),
      ),
      body: body,
    );
  }

  Widget _buildContent(BuildContext context) {
    final order = _order!;
    final status = order['status'] as String;
    final stops = order['stops'] as List<dynamic>? ?? [];
    final vehicles = order['vehicles'] as List<dynamic>? ?? [];
    final delivery = WorkflowHelper.deliveryStop(stops);
    final deliveryAddress = WorkflowHelper.stopAddress(delivery);
    final primaryAction = WorkflowHelper.primaryAction(status);

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            WorkflowHelper.phaseTitle(status),
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 4),
          Text('Status: $status'),
          const SizedBox(height: 16),
          if (WorkflowHelper.showDeliverySection(status)) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Delivery', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    Text(deliveryAddress.isEmpty ? 'Delivery address is missing.' : deliveryAddress),
                    const SizedBox(height: 12),
                    FilledButton.icon(
                      onPressed: deliveryAddress.isEmpty ? null : _navigateToDelivery,
                      icon: const Icon(Icons.navigation_outlined),
                      label: const Text('Navigate'),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
          ],
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Vehicles (${vehicles.length})', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  if (vehicles.isEmpty)
                    const Text('No vehicles on this order.')
                  else
                    ...vehicles.map((vehicle) {
                      final map = vehicle as Map<String, dynamic>;
                      final vin = map['vin'] as String? ?? 'VIN pending';
                      final make = map['make'] as String? ?? 'Vehicle';
                      final model = map['model'] as String? ?? '';
                      return ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.directions_car_outlined),
                        title: Text('$make $model'.trim()),
                        subtitle: Text(vin),
                      );
                    }),
                ],
              ),
            ),
          ),
          if (WorkflowHelper.showCmrSection(status)) ...[
            const SizedBox(height: 12),
            _buildCmrSection(context, status),
          ],
          const SizedBox(height: 16),
          if (primaryAction != null)
            FilledButton(
              onPressed: _actionBusy ? null : () => _runAction(primaryAction),
              child: _actionBusy
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(WorkflowHelper.primaryActionLabel(status)),
            ),
          if (status == 'ASSIGNED') ...[
            const SizedBox(height: 8),
            OutlinedButton(
              onPressed: _actionBusy ? null : () => _runAction('reject'),
              child: const Text('Reject order'),
            ),
          ],
          if (status == 'COMPLETED')
            const Padding(
              padding: EdgeInsets.only(top: 16),
              child: Text('Job completed. Pull to refresh if needed.'),
            ),
        ],
      ),
    );
  }

  Widget _buildCmrSection(BuildContext context, String status) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('CMR', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text(_cmr == null ? 'No CMR loaded yet.' : 'CMR ready'),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton(
                  onPressed: _cmrBusy ? null : _loadCmr,
                  child: const Text('Refresh CMR'),
                ),
                if (WorkflowHelper.canGenerateCmr(status))
                  OutlinedButton(
                    onPressed: _cmrBusy ? null : _generateCmr,
                    child: const Text('Generate CMR'),
                  ),
                OutlinedButton(
                  onPressed: (_cmrBusy || _cmr == null) ? null : _previewCmr,
                  child: const Text('Preview'),
                ),
                OutlinedButton(
                  onPressed: (_cmrBusy || _cmr == null) ? null : _shareCmr,
                  child: const Text('Download / Share'),
                ),
                if (status == 'DELIVERING') ...[
                  OutlinedButton(
                    onPressed: _cmrBusy ? null : () => _uploadSignedCmr(ImageSource.camera),
                    child: const Text('Upload photo'),
                  ),
                  OutlinedButton(
                    onPressed: _cmrBusy ? null : () => _uploadSignedCmr(ImageSource.gallery),
                    child: const Text('Upload image'),
                  ),
                  OutlinedButton(
                    onPressed: _cmrBusy ? null : _uploadSignedCmrFromFile,
                    child: const Text('Upload PDF/file'),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// Opens the active order workflow and keeps the driver in-flow.
Future<void> openOrderWorkflow(
  BuildContext context, {
  required ApiClient apiClient,
  required String orderId,
  bool replace = false,
}) {
  AppLogger.workflow(orderId: orderId, status: 'navigate', target: 'workflow');
  final route = MaterialPageRoute<void>(
    builder: (_) => OrderDetailScreen(
      apiClient: apiClient,
      orderId: orderId,
    ),
  );
  if (replace) {
    return Navigator.of(context).pushReplacement(route);
  }
  return Navigator.of(context).push(route);
}
