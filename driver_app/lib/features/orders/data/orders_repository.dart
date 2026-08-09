import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/storage/hive_boxes.dart';
import '../../../shared/models/order_models.dart';

class CacheRepository {
  static const _homeKey = 'driver_home';
  static const _currentOrderKey = 'current_order';
  static const _ordersKey = 'orders_list';

  Future<void> saveHome(DriverHome home) async {
    await HiveBoxes.cacheBox.put(_homeKey, encodeJson(_homeToJson(home)));
  }

  DriverHome? readHome() {
    final raw = HiveBoxes.cacheBox.get(_homeKey);
    if (raw == null) return null;
    return DriverHome.fromJson(decodeJson(raw));
  }

  Future<void> saveCurrentOrder(DriverCurrentOrder current) async {
    await HiveBoxes.cacheBox.put(
      _currentOrderKey,
      jsonEncode({
        'order': current.order == null ? null : _orderToJson(current.order!),
        'current_stop': current.currentStop == null ? null : _stopToJson(current.currentStop!),
        'remaining_stops': current.remainingStops.map(_stopToJson).toList(),
        'vehicles': current.vehicles.map(_vehicleToJson).toList(),
        'next_required_action': current.nextRequiredAction,
        'workflow_status': current.workflowStatus,
      }),
    );
  }

  DriverCurrentOrder? readCurrentOrder() {
    final raw = HiveBoxes.cacheBox.get(_currentOrderKey);
    if (raw == null) return null;
    return DriverCurrentOrder.fromJson(decodeJson(raw));
  }

  Future<void> saveOrders(List<OrderSummary> orders) async {
    await HiveBoxes.cacheBox.put(
      _ordersKey,
      jsonEncode(orders.map(_summaryToJson).toList()),
    );
  }

  List<OrderSummary> readOrders() {
    final raw = HiveBoxes.cacheBox.get(_ordersKey);
    if (raw == null) return [];
    final list = jsonDecode(raw) as List<dynamic>;
    return list.map((item) => OrderSummary.fromJson(item as Map<String, dynamic>)).toList();
  }

  Map<String, dynamic> _homeToJson(DriverHome home) => {
        'user_name': home.userName,
        'truck_label': home.truckLabel,
        'trailer_label': home.trailerLabel,
        'current_order': home.currentOrder == null ? null : _summaryToJson(home.currentOrder!),
        'next_action': home.nextAction,
        'unread_notifications': home.unreadNotifications,
        'driver': {
          'id': home.driver.id,
          'phone': home.driver.phone,
          'active': home.driver.active,
          'driving_license': home.driver.drivingLicense,
        },
      };

  Map<String, dynamic> _summaryToJson(OrderSummary order) => {
        'id': order.id,
        'order_number': order.orderNumber,
        'status': order.status,
        'customer_id': order.customerId,
        'planned_pickup_date': order.plannedPickupDate,
        'planned_delivery_date': order.plannedDeliveryDate,
      };

  Map<String, dynamic> _orderToJson(OrderDetail order) => {
        'id': order.id,
        'order_number': order.orderNumber,
        'status': order.status,
        'notes': order.notes,
        'stops': order.stops.map(_stopToJson).toList(),
        'vehicles': order.vehicles.map(_vehicleToJson).toList(),
        'assigned_truck_id': order.assignedTruckId,
        'assigned_trailer_id': order.assignedTrailerId,
      };

  Map<String, dynamic> _stopToJson(OrderStop stop) => {
        'id': stop.id,
        'stop_type': stop.stopType,
        'sequence': stop.sequence,
        'progress_status': stop.progressStatus,
        'city': stop.city,
        'address': stop.address,
        'country': stop.country,
      };

  Map<String, dynamic> _vehicleToJson(OrderVehicle vehicle) => {
        'id': vehicle.id,
        'make': vehicle.make,
        'model': vehicle.model,
        'color': vehicle.color,
        'vin': vehicle.vin,
        'verified_vin': vehicle.verifiedVin,
        'pickup_stop_id': vehicle.pickupStopId,
        'delivery_stop_id': vehicle.deliveryStopId,
      };
}

class DriverApiRepository {
  DriverApiRepository(this._dio, this._cache);

  final Dio _dio;
  final CacheRepository _cache;

  Future<DriverHome> fetchHome({bool allowCache = true}) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/drivers/me/home');
      final home = DriverHome.fromJson(responseDataMap(response));
      await _cache.saveHome(home);
      return home;
    } on DioException catch (error) {
      if (allowCache) {
        final cached = _cache.readHome();
        if (cached != null) return cached;
      }
      rethrowDio(error);
    }
  }

  Future<DriverCurrentOrder> fetchCurrentOrder({bool allowCache = true}) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/drivers/me/current-order');
      final current = DriverCurrentOrder.fromJson(responseDataMap(response));
      await _cache.saveCurrentOrder(current);
      return current;
    } on DioException catch (error) {
      if (allowCache) {
        final cached = _cache.readCurrentOrder();
        if (cached != null) return cached;
      }
      rethrowDio(error);
    }
  }

  Future<List<OrderSummary>> fetchOrders({bool allowCache = true}) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/drivers/me/orders');
      final orders = responseDataList(response)
          .map((item) => OrderSummary.fromJson(item as Map<String, dynamic>))
          .toList();
      await _cache.saveOrders(orders);
      return orders;
    } on DioException catch (error) {
      if (allowCache) return _cache.readOrders();
      rethrowDio(error);
    }
  }

  Future<OrderDetail> fetchOrder(String orderId) async {
    final response = await _dio.get<Map<String, dynamic>>('/orders/$orderId');
    return OrderDetail.fromJson(responseDataMap(response));
  }

  Future<List<TimelineEntry>> fetchTimeline(String orderId) async {
    final response = await _dio.get<Map<String, dynamic>>('/orders/$orderId/timeline');
    return responseDataList(response)
        .map((item) => TimelineEntry.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<CompletionChecklist> fetchChecklist(String orderId) async {
    final response =
        await _dio.get<Map<String, dynamic>>('/orders/$orderId/completion-checklist');
    return CompletionChecklist.fromJson(responseDataMap(response));
  }

  Future<void> workflowAction(String orderId, String action) async {
    await _dio.post<Map<String, dynamic>>('/orders/$orderId/$action');
  }
}
