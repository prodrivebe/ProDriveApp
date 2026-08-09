import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/connectivity/connectivity_service.dart';
import '../../../core/network/api_exception.dart';
import '../../../shared/widgets/common_widgets.dart';
import '../../photos/providers/upload_providers.dart';

class CmrUploadScreen extends ConsumerStatefulWidget {
  const CmrUploadScreen({super.key, required this.orderId});

  final String orderId;

  @override
  ConsumerState<CmrUploadScreen> createState() => _CmrUploadScreenState();
}

class _CmrUploadScreenState extends ConsumerState<CmrUploadScreen> {
  String? _previewPath;
  bool _uploading = false;
  String? _message;

  Future<void> _pick(ImageSource source) async {
    final picker = ImagePicker();
    final file = await picker.pickImage(source: source, imageQuality: 85);
    if (file != null) setState(() => _previewPath = file.path);
  }

  Future<void> _upload() async {
    final path = _previewPath;
    if (path == null) return;

    setState(() {
      _uploading = true;
      _message = null;
    });

    try {
      final online = ref.read(isOnlineProvider);
      await ref.read(uploadControllerProvider).uploadDocument(
            orderId: widget.orderId,
            filePath: path,
            documentType: 'CMR',
          );
      setState(() {
        _message = online ? 'CMR uploaded successfully.' : 'CMR queued for upload.';
        _previewPath = null;
      });
    } on ApiException catch (error) {
      setState(() => _message = error.userMessage);
    } finally {
      setState(() => _uploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('CMR document')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const OfflineBanner(),
          const Text('Capture or select the signed CMR document for this order.'),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: _uploading ? null : () => _pick(ImageSource.camera),
                  icon: const Icon(Icons.photo_camera),
                  label: const Text('Camera'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _uploading ? null : () => _pick(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library),
                  label: const Text('Gallery'),
                ),
              ),
            ],
          ),
          if (_previewPath != null) ...[
            const SizedBox(height: 16),
            Text('Selected: ${_previewPath!.split('/').last}'),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: _uploading ? null : _upload,
              child: Text(_uploading ? 'Uploading…' : 'Upload CMR'),
            ),
          ],
          if (_message != null) ...[
            const SizedBox(height: 16),
            Text(_message!, style: Theme.of(context).textTheme.titleMedium),
          ],
        ],
      ),
    );
  }
}
