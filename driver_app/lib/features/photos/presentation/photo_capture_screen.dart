import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/connectivity/connectivity_service.dart';
import '../../../core/network/api_exception.dart';
import '../../../shared/widgets/common_widgets.dart';
import '../providers/upload_providers.dart';
import '../../vehicles/providers/vehicle_detail_providers.dart';

const photoTypes = [
  'FRONT',
  'REAR',
  'LEFT',
  'RIGHT',
  'DAMAGE',
  'INTERIOR',
  'DOCUMENT',
];

class PhotoCaptureScreen extends ConsumerStatefulWidget {
  const PhotoCaptureScreen({
    super.key,
    required this.orderId,
    required this.vehicleId,
  });

  final String orderId;
  final String vehicleId;

  @override
  ConsumerState<PhotoCaptureScreen> createState() => _PhotoCaptureScreenState();
}

class _PhotoCaptureScreenState extends ConsumerState<PhotoCaptureScreen> {
  String _selectedType = 'FRONT';
  String? _previewPath;
  double? _progress;
  String? _message;
  bool _uploading = false;

  Future<void> _pick(ImageSource source) async {
    final picker = ImagePicker();
    final file = await picker.pickImage(source: source, imageQuality: 85);
    if (file != null) {
      setState(() => _previewPath = file.path);
    }
  }

  Future<void> _upload() async {
    final path = _previewPath;
    if (path == null) return;

    setState(() {
      _uploading = true;
      _progress = null;
      _message = null;
    });

    try {
      final online = ref.read(isOnlineProvider);
      await ref.read(uploadControllerProvider).uploadPhoto(
            orderId: widget.orderId,
            vehicleId: widget.vehicleId,
            filePath: path,
            photoType: _selectedType,
          );
      setState(() {
        _message = online ? 'Photo uploaded.' : 'Photo queued for upload.';
        _previewPath = null;
        _progress = 1;
      });
      ref.invalidate(vehiclePhotosProvider((orderId: widget.orderId, vehicleId: widget.vehicleId)));
    } on ApiException catch (error) {
      setState(() => _message = error.userMessage);
    } finally {
      setState(() => _uploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final photosAsync =
        ref.watch(vehiclePhotosProvider((orderId: widget.orderId, vehicleId: widget.vehicleId)));

    return Scaffold(
      appBar: AppBar(title: const Text('Vehicle photos')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const OfflineBanner(),
          DropdownButtonFormField<String>(
            value: _selectedType,
            decoration: const InputDecoration(labelText: 'Photo type'),
            items: photoTypes
                .map((type) => DropdownMenuItem(value: type, child: Text(type)))
                .toList(),
            onChanged: _uploading ? null : (value) => setState(() => _selectedType = value!),
          ),
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
            Text('Preview', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Container(
              height: 180,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                border: Border.all(color: Theme.of(context).colorScheme.outline),
              ),
              child: Text(_previewPath!.split('/').last),
            ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: _uploading ? null : _upload,
              child: Text(_uploading ? 'Uploading…' : 'Upload photo'),
            ),
          ],
          if (_progress != null) ...[
            const SizedBox(height: 12),
            LinearProgressIndicator(value: _progress),
          ],
          if (_message != null) ...[
            const SizedBox(height: 12),
            Text(_message!),
          ],
          const SizedBox(height: 24),
          SectionCard(
            title: 'Uploaded photos',
            child: photosAsync.when(
              loading: () => const CircularProgressIndicator(),
              error: (error, _) => Text(error.toString()),
              data: (photos) => photos.isEmpty
                  ? const Text('No photos yet.')
                  : Column(
                      children: photos
                          .map(
                            (photo) => ListTile(
                              contentPadding: EdgeInsets.zero,
                              title: Text(photo.photoType),
                              subtitle: Text(photo.uploadedAt),
                            ),
                          )
                          .toList(),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}
