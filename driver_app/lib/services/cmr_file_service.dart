import 'dart:io';
import 'dart:typed_data';

import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import 'app_logger.dart';

class CmrFileService {
  CmrFileService._();

  static Future<File> savePdf({
    required Uint8List bytes,
    required String orderNumber,
  }) async {
    final directory = await getTemporaryDirectory();
    final safeName = orderNumber.replaceAll(RegExp(r'[^A-Za-z0-9_-]'), '_');
    final file = File('${directory.path}/cmr_$safeName.pdf');
    await file.writeAsBytes(bytes, flush: true);
    if (!file.existsSync()) {
      throw Exception('Could not save CMR PDF.');
    }
    AppLogger.cmr('saved path=${file.path} size=${file.lengthSync()}');
    return file;
  }

  static Future<void> preview(File file) async {
    if (!file.existsSync()) {
      throw Exception('CMR file not found.');
    }
    AppLogger.cmr('preview path=${file.path}');
    final result = await OpenFilex.open(file.path, type: 'application/pdf');
    AppLogger.cmr('preview result=${result.type} message=${result.message}');
    if (result.type != ResultType.done && result.type != ResultType.noAppToOpen) {
      throw Exception(result.message);
    }
    if (result.type == ResultType.noAppToOpen) {
      await share(file);
    }
  }

  static Future<void> share(File file) async {
    if (!file.existsSync()) {
      throw Exception('CMR file not found.');
    }
    AppLogger.cmr('share path=${file.path}');
    await Share.shareXFiles([XFile(file.path)], text: 'ProDrive CMR');
  }
}
