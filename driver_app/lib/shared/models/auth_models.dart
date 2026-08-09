class AuthTokens {
  const AuthTokens({required this.accessToken, required this.refreshToken});

  final String accessToken;
  final String refreshToken;

  factory AuthTokens.fromJson(Map<String, dynamic> json) => AuthTokens(
        accessToken: json['access_token'] as String,
        refreshToken: json['refresh_token'] as String,
      );
}

class UserProfile {
  const UserProfile({
    required this.id,
    required this.firstName,
    required this.lastName,
    required this.email,
    required this.role,
  });

  final String id;
  final String firstName;
  final String lastName;
  final String email;
  final String role;

  String get fullName => '$firstName $lastName'.trim();

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
        id: json['id'] as String,
        firstName: json['first_name'] as String,
        lastName: json['last_name'] as String,
        email: json['email'] as String,
        role: json['role'] as String,
      );
}

class DriverProfile {
  const DriverProfile({
    required this.id,
    required this.phone,
    required this.active,
    required this.drivingLicense,
  });

  final String id;
  final String? phone;
  final bool active;
  final String? drivingLicense;

  factory DriverProfile.fromJson(Map<String, dynamic> json) => DriverProfile(
        id: json['id'] as String,
        phone: json['phone'] as String?,
        active: json['active'] as bool? ?? true,
        drivingLicense: json['driving_license'] as String?,
      );
}
