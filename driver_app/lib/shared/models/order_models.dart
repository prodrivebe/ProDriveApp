import 'auth_models.dart';

class OrderSummary {
  const OrderSummary({
    required this.id,
    required this.orderNumber,
    required this.status,
    required this.customerId,
    this.plannedPickupDate,
    this.plannedDeliveryDate,
  });

  final String id;
  final String orderNumber;
  final String status;
  final String customerId;
  final String? plannedPickupDate;
  final String? plannedDeliveryDate;

  factory OrderSummary.fromJson(Map<String, dynamic> json) => OrderSummary(
        id: json['id'] as String,
        orderNumber: json['order_number'] as String,
        status: json['status'] as String,
        customerId: json['customer_id'] as String,
        plannedPickupDate: json['planned_pickup_date'] as String?,
        plannedDeliveryDate: json['planned_delivery_date'] as String?,
      );
}

class OrderStop {
  const OrderStop({
    required this.id,
    required this.stopType,
    required this.sequence,
    required this.progressStatus,
    this.city,
    this.address,
    this.country,
  });

  final String id;
  final String stopType;
  final int sequence;
  final String progressStatus;
  final String? city;
  final String? address;
  final String? country;

  factory OrderStop.fromJson(Map<String, dynamic> json) => OrderStop(
        id: json['id'] as String,
        stopType: json['stop_type'] as String,
        sequence: json['sequence'] as int,
        progressStatus: json['progress_status'] as String? ?? 'PENDING',
        city: json['city'] as String?,
        address: json['address'] as String?,
        country: json['country'] as String?,
      );

  String get label => [city, address].where((v) => v != null && v.isNotEmpty).join(', ');
}

class OrderVehicle {
  const OrderVehicle({
    required this.id,
    required this.make,
    required this.model,
    required this.color,
    required this.vin,
    required this.verifiedVin,
    required this.pickupStopId,
    required this.deliveryStopId,
  });

  final String id;
  final String? make;
  final String? model;
  final String? color;
  final String? vin;
  final String? verifiedVin;
  final String? pickupStopId;
  final String? deliveryStopId;

  factory OrderVehicle.fromJson(Map<String, dynamic> json) => OrderVehicle(
        id: json['id'] as String,
        make: json['make'] as String?,
        model: json['model'] as String?,
        color: json['color'] as String?,
        vin: json['vin'] as String?,
        verifiedVin: json['verified_vin'] as String?,
        pickupStopId: json['pickup_stop_id'] as String?,
        deliveryStopId: json['delivery_stop_id'] as String?,
      );

  bool get isVinVerified => verifiedVin != null && verifiedVin!.isNotEmpty;
}

class OrderDetail {
  const OrderDetail({
    required this.id,
    required this.orderNumber,
    required this.status,
    required this.notes,
    required this.stops,
    required this.vehicles,
    this.assignedTruckId,
    this.assignedTrailerId,
  });

  final String id;
  final String orderNumber;
  final String status;
  final String? notes;
  final List<OrderStop> stops;
  final List<OrderVehicle> vehicles;
  final String? assignedTruckId;
  final String? assignedTrailerId;

  factory OrderDetail.fromJson(Map<String, dynamic> json) => OrderDetail(
        id: json['id'] as String,
        orderNumber: json['order_number'] as String,
        status: json['status'] as String,
        notes: json['notes'] as String?,
        stops: (json['stops'] as List<dynamic>? ?? [])
            .map((item) => OrderStop.fromJson(item as Map<String, dynamic>))
            .toList(),
        vehicles: (json['vehicles'] as List<dynamic>? ?? [])
            .map((item) => OrderVehicle.fromJson(item as Map<String, dynamic>))
            .toList(),
        assignedTruckId: json['assigned_truck_id'] as String?,
        assignedTrailerId: json['assigned_trailer_id'] as String?,
      );
}

class DriverCurrentOrder {
  const DriverCurrentOrder({
    required this.order,
    required this.currentStop,
    required this.remainingStops,
    required this.vehicles,
    required this.nextRequiredAction,
    required this.workflowStatus,
  });

  final OrderDetail? order;
  final OrderStop? currentStop;
  final List<OrderStop> remainingStops;
  final List<OrderVehicle> vehicles;
  final String nextRequiredAction;
  final String? workflowStatus;

  factory DriverCurrentOrder.fromJson(Map<String, dynamic> json) => DriverCurrentOrder(
        order: json['order'] == null
            ? null
            : OrderDetail.fromJson(json['order'] as Map<String, dynamic>),
        currentStop: json['current_stop'] == null
            ? null
            : OrderStop.fromJson(json['current_stop'] as Map<String, dynamic>),
        remainingStops: (json['remaining_stops'] as List<dynamic>? ?? [])
            .map((item) => OrderStop.fromJson(item as Map<String, dynamic>))
            .toList(),
        vehicles: (json['vehicles'] as List<dynamic>? ?? [])
            .map((item) => OrderVehicle.fromJson(item as Map<String, dynamic>))
            .toList(),
        nextRequiredAction: json['next_required_action'] as String? ?? 'No active orders',
        workflowStatus: json['workflow_status'] as String?,
      );
}

class DriverHome {
  const DriverHome({
    required this.userName,
    required this.truckLabel,
    required this.trailerLabel,
    required this.currentOrder,
    required this.nextAction,
    required this.unreadNotifications,
    required this.driver,
  });

  final String userName;
  final String? truckLabel;
  final String? trailerLabel;
  final OrderSummary? currentOrder;
  final String nextAction;
  final int unreadNotifications;
  final DriverProfile driver;

  factory DriverHome.fromJson(Map<String, dynamic> json) => DriverHome(
        userName: json['user_name'] as String? ?? 'Driver',
        truckLabel: json['truck_label'] as String?,
        trailerLabel: json['trailer_label'] as String?,
        currentOrder: json['current_order'] == null
            ? null
            : OrderSummary.fromJson(json['current_order'] as Map<String, dynamic>),
        nextAction: json['next_action'] as String? ?? 'No active orders',
        unreadNotifications: json['unread_notifications'] as int? ?? 0,
        driver: DriverProfile.fromJson(json['driver'] as Map<String, dynamic>),
      );
}

class TimelineEntry {
  const TimelineEntry({
    required this.id,
    required this.eventType,
    required this.description,
    required this.createdAt,
  });

  final String id;
  final String eventType;
  final String description;
  final String createdAt;

  factory TimelineEntry.fromJson(Map<String, dynamic> json) => TimelineEntry(
        id: json['id'] as String,
        eventType: json['event_type'] as String,
        description: json['description'] as String,
        createdAt: json['created_at'] as String,
      );
}

class CompletionChecklist {
  const CompletionChecklist({
    required this.canComplete,
    required this.completionPercentage,
    required this.missingItems,
    required this.completedItems,
  });

  final bool canComplete;
  final int completionPercentage;
  final List<String> missingItems;
  final List<String> completedItems;

  factory CompletionChecklist.fromJson(Map<String, dynamic> json) => CompletionChecklist(
        canComplete: json['can_complete'] as bool? ?? false,
        completionPercentage: json['completion_percentage'] as int? ?? 0,
        missingItems: (json['missing_items'] as List<dynamic>? ?? []).cast<String>(),
        completedItems: (json['completed_items'] as List<dynamic>? ?? []).cast<String>(),
      );
}

class VinHistoryEntry {
  const VinHistoryEntry({
    required this.originalVin,
    required this.verifiedVin,
    required this.action,
    required this.verifiedAt,
  });

  final String? originalVin;
  final String verifiedVin;
  final String action;
  final String verifiedAt;

  factory VinHistoryEntry.fromJson(Map<String, dynamic> json) => VinHistoryEntry(
        originalVin: json['original_vin'] as String?,
        verifiedVin: json['verified_vin'] as String,
        action: json['action'] as String,
        verifiedAt: json['verified_at'] as String,
      );
}

class VehiclePhoto {
  const VehiclePhoto({
    required this.id,
    required this.photoType,
    required this.filePath,
    required this.uploadedAt,
  });

  final String id;
  final String photoType;
  final String filePath;
  final String uploadedAt;

  factory VehiclePhoto.fromJson(Map<String, dynamic> json) => VehiclePhoto(
        id: json['id'] as String,
        photoType: json['photo_type'] as String,
        filePath: json['file_path'] as String,
        uploadedAt: json['uploaded_at'] as String,
      );
}

class VehicleDamageReport {
  const VehicleDamageReport({
    required this.id,
    required this.damageType,
    required this.severity,
    required this.description,
    required this.location,
  });

  final String id;
  final String damageType;
  final String severity;
  final String? description;
  final String? location;

  factory VehicleDamageReport.fromJson(Map<String, dynamic> json) => VehicleDamageReport(
        id: json['id'] as String,
        damageType: json['damage_type'] as String,
        severity: json['severity'] as String,
        description: json['description'] as String?,
        location: json['location'] as String?,
      );
}

class AppNotification {
  const AppNotification({
    required this.id,
    required this.title,
    required this.message,
    required this.type,
    required this.readAt,
    required this.createdAt,
  });

  final String id;
  final String title;
  final String message;
  final String type;
  final String? readAt;
  final String createdAt;

  factory AppNotification.fromJson(Map<String, dynamic> json) => AppNotification(
        id: json['id'] as String,
        title: json['title'] as String,
        message: json['message'] as String,
        type: json['type'] as String,
        readAt: json['read_at'] as String?,
        createdAt: json['created_at'] as String,
      );
}
