import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/dio_provider.dart';
import '../../../core/storage/secure_token_storage.dart';
import '../../../shared/models/auth_models.dart';
import '../data/auth_repository.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(ref.watch(dioProvider), ref.watch(secureTokenStorageProvider));
});

final authTokensProvider = StateProvider<StoredTokens?>((ref) => null);

final authBootstrapProvider = FutureProvider<bool>((ref) async {
  final tokens = await ref.read(authRepositoryProvider).currentTokens();
  ref.read(authTokensProvider.notifier).state = tokens;
  return tokens != null;
});

final userProfileProvider = FutureProvider<UserProfile>((ref) async {
  final dio = ref.watch(dioProvider);
  final response = await dio.get<Map<String, dynamic>>('/auth/me');
  final data = responseDataMap(response);
  return UserProfile.fromJson(data);
});

final driverProfileProvider = FutureProvider<DriverProfile>((ref) async {
  final dio = ref.watch(dioProvider);
  final response = await dio.get<Map<String, dynamic>>('/drivers/me');
  final data = responseDataMap(response);
  return DriverProfile.fromJson(data);
});
