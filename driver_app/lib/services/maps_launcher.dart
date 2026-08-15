import 'package:url_launcher/url_launcher.dart';

import 'app_logger.dart';

class MapsLaunchException implements Exception {
  MapsLaunchException(this.message);

  final String message;

  @override
  String toString() => message;
}

class MapsLauncher {
  MapsLauncher._();

  static Future<void> openNavigation({
    required String? address,
    String? latitude,
    String? longitude,
  }) async {
    final query = _buildQuery(address: address, latitude: latitude, longitude: longitude);
    if (query == null || query.isEmpty) {
      throw MapsLaunchException('Delivery address is missing.');
    }

    AppLogger.debug('maps query=$query');

    final googleMaps = Uri.parse(
      'https://www.google.com/maps/dir/?api=1&destination=${Uri.encodeComponent(query)}',
    );
    final geo = _geoUri(latitude, longitude, query);

    if (await launchUrl(googleMaps, mode: LaunchMode.externalApplication)) {
      AppLogger.debug('maps opened google');
      return;
    }

    if (geo != null && await launchUrl(geo, mode: LaunchMode.externalApplication)) {
      AppLogger.debug('maps opened geo fallback');
      return;
    }

    final browser = Uri.parse('https://www.google.com/maps/search/?api=1&query=${Uri.encodeComponent(query)}');
    if (await launchUrl(browser, mode: LaunchMode.externalApplication)) {
      AppLogger.debug('maps opened browser fallback');
      return;
    }

    throw MapsLaunchException('Could not open navigation. Check that a maps app is installed.');
  }

  static String? _buildQuery({
    required String? address,
    String? latitude,
    String? longitude,
  }) {
    if (address != null && address.trim().isNotEmpty) {
      return address.trim();
    }
    if (latitude != null &&
        longitude != null &&
        latitude.isNotEmpty &&
        longitude.isNotEmpty) {
      return '$latitude,$longitude';
    }
    return null;
  }

  static Uri? _geoUri(String? latitude, String? longitude, String query) {
    if (latitude != null &&
        longitude != null &&
        latitude.isNotEmpty &&
        longitude.isNotEmpty) {
      return Uri.parse('geo:$latitude,$longitude?q=$latitude,$longitude');
    }
    return Uri.parse('geo:0,0?q=${Uri.encodeComponent(query)}');
  }
}
