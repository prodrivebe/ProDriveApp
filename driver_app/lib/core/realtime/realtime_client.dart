import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

import '../config/api_config.dart';
import '../storage/secure_token_storage.dart';

typedef RealtimeEventHandler = void Function(Map<String, dynamic> event);

class RealtimeClient {
  RealtimeClient(this._storage);

  final SecureTokenStorage _storage;
  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _subscription;
  Timer? _reconnectTimer;
  Timer? _pingTimer;
  bool _shouldReconnect = false;
  int _reconnectAttempts = 0;
  final _handlers = <RealtimeEventHandler>{};

  void addListener(RealtimeEventHandler handler) => _handlers.add(handler);

  void removeListener(RealtimeEventHandler handler) => _handlers.remove(handler);

  Future<void> connect() async {
    final tokens = await _storage.readTokens();
    if (tokens == null) return;
    _shouldReconnect = true;
    await _open(tokens.accessToken);
  }

  Future<void> disconnect() async {
    _shouldReconnect = false;
    _reconnectTimer?.cancel();
    _pingTimer?.cancel();
    await _subscription?.cancel();
    await _channel?.sink.close();
    _channel = null;
  }

  void subscribeOrder(String orderId) {
    _send({'action': 'subscribe', 'channel': 'order', 'order_id': orderId});
  }

  void updatePresence({required String status, String? activeOrderId}) {
    _send({
      'action': 'presence',
      'status': status,
      if (activeOrderId != null) 'active_order_id': activeOrderId,
    });
  }

  Future<void> _open(String token) async {
    await _subscription?.cancel();
    await _channel?.sink.close();

    final base = ApiConfig.baseUrl.replaceFirst('http', 'ws');
    final uri = Uri.parse('$base/ws?token=${Uri.encodeComponent(token)}');
    _channel = WebSocketChannel.connect(uri);
    _subscription = _channel!.stream.listen(
      _onMessage,
      onDone: _scheduleReconnect,
      onError: (_) => _scheduleReconnect,
    );
    _reconnectAttempts = 0;
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(const Duration(seconds: 25), (_) {
      _send({'action': 'ping'});
    });
  }

  void _onMessage(dynamic message) {
    final decoded = jsonDecode(message as String) as Map<String, dynamic>;
    if (decoded['type'] == 'BATCH') {
      final events = decoded['events'] as List<dynamic>? ?? [];
      for (final item in events) {
        _dispatch(item as Map<String, dynamic>);
      }
      return;
    }
    _dispatch(decoded);
  }

  void _dispatch(Map<String, dynamic> event) {
    if (event['type'] == 'HEARTBEAT') return;
    for (final handler in _handlers) {
      handler(event);
    }
  }

  void _send(Map<String, dynamic> payload) {
    final channel = _channel;
    if (channel == null) return;
    channel.sink.add(jsonEncode(payload));
  }

  void _scheduleReconnect() {
    if (!_shouldReconnect) return;
    _reconnectTimer?.cancel();
    final delay = Duration(seconds: (1 << _reconnectAttempts.clamp(0, 5)));
    _reconnectAttempts += 1;
    _reconnectTimer = Timer(delay, () async {
      final tokens = await _storage.readTokens();
      if (tokens != null) {
        await _open(tokens.accessToken);
      }
    });
  }
}
