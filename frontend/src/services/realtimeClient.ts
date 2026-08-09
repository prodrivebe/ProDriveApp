import type { QueryClient } from "@tanstack/react-query";

export type RealtimeSeverity = "info" | "success" | "warning" | "error";

export interface RealtimeEvent {
  id: string;
  type: string;
  company_id: string;
  channel: string;
  payload: Record<string, unknown>;
  severity?: RealtimeSeverity;
  created_at: string;
}

export type ConnectionState = "connecting" | "connected" | "disconnected" | "error";

type EventHandler = (event: RealtimeEvent) => void;
type StateHandler = (state: ConnectionState) => void;

function wsBaseUrl(): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/v1/ws`;
}

export class RealtimeClient {
  private socket: WebSocket | null = null;
  private handlers = new Set<EventHandler>();
  private stateHandlers = new Set<StateHandler>();
  private reconnectAttempts = 0;
  private reconnectTimer: number | null = null;
  private pingTimer: number | null = null;
  private token: string | null = null;
  private shouldReconnect = true;

  connect(accessToken: string): void {
    this.token = accessToken;
    this.shouldReconnect = true;
    this.openSocket();
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this.clearTimers();
    this.socket?.close();
    this.socket = null;
    this.setState("disconnected");
  }

  subscribe(handler: EventHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  onStateChange(handler: StateHandler): () => void {
    this.stateHandlers.add(handler);
    return () => this.stateHandlers.delete(handler);
  }

  subscribeOrder(orderId: string): void {
    this.send({ action: "subscribe", channel: "order", order_id: orderId });
  }

  private openSocket(): void {
    if (!this.token) return;
    this.clearTimers();
    this.setState("connecting");
    const socket = new WebSocket(`${wsBaseUrl()}?token=${encodeURIComponent(this.token)}`);
    this.socket = socket;

    socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.setState("connected");
      this.pingTimer = window.setInterval(() => {
        this.send({ action: "ping" });
      }, 25_000);
    };

    socket.onmessage = (message) => {
      try {
        const payload = JSON.parse(message.data) as RealtimeEvent | { type: "BATCH"; events: RealtimeEvent[] };
        if (payload.type === "BATCH" && Array.isArray(payload.events)) {
          payload.events.forEach((event) => this.emit(event));
          return;
        }
        this.emit(payload as RealtimeEvent);
      } catch {
        // Ignore malformed frames.
      }
    };

    socket.onerror = () => this.setState("error");

    socket.onclose = () => {
      this.clearTimers();
      this.setState("disconnected");
      if (this.shouldReconnect) {
        const delay = Math.min(30_000, 1000 * 2 ** this.reconnectAttempts);
        this.reconnectAttempts += 1;
        this.reconnectTimer = window.setTimeout(() => this.openSocket(), delay);
      }
    };
  }

  private emit(event: RealtimeEvent): void {
    if (event.type === "HEARTBEAT") return;
    this.handlers.forEach((handler) => handler(event));
  }

  private send(payload: Record<string, unknown>): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload));
    }
  }

  private setState(state: ConnectionState): void {
    this.stateHandlers.forEach((handler) => handler(state));
  }

  private clearTimers(): void {
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.pingTimer !== null) {
      window.clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }
}

export const realtimeClient = new RealtimeClient();

const ORDER_EVENT_PREFIXES = ["ORDER_", "LOADING_", "TRANSIT_", "DELIVERY_", "DRIVER_ARRIVED", "ARRIVED_"];

export function applyRealtimeEvent(queryClient: QueryClient, event: RealtimeEvent): void {
  const { type, payload } = event;
  const orderId = typeof payload.order_id === "string" ? payload.order_id : null;

  if (type === "NOTIFICATION_CREATED") {
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
    return;
  }

  if (type === "TIMELINE_ENTRY" && orderId) {
    queryClient.invalidateQueries({ queryKey: ["orders", orderId, "timeline"] });
  }

  if (type === "PRESENCE_UPDATED" || type === "DRIVER_CONNECTED" || type === "DRIVER_DISCONNECTED") {
    queryClient.invalidateQueries({ queryKey: ["presence"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  }

  if (ORDER_EVENT_PREFIXES.some((prefix) => type.startsWith(prefix)) || type.includes("VIN") || type.includes("PHOTO") || type.includes("DAMAGE") || type.includes("DOCUMENT") || type.includes("CMR")) {
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    queryClient.invalidateQueries({ queryKey: ["orders"] });
    if (orderId) {
      queryClient.invalidateQueries({ queryKey: ["orders", orderId] });
      queryClient.invalidateQueries({ queryKey: ["orders", orderId, "timeline"] });
      queryClient.invalidateQueries({ queryKey: ["orders", orderId, "checklist"] });
      queryClient.invalidateQueries({ queryKey: ["orders", orderId, "documents"] });
    }
  }
}
