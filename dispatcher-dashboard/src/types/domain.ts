export interface UserProfile {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
}

export interface OrderStop {
  id: string;
  stop_type: "PICKUP" | "DELIVERY";
  sequence: number;
  city?: string | null;
  address?: string | null;
}

export interface OrderVehicle {
  id: string;
  make?: string | null;
  model?: string | null;
  vin?: string | null;
}

export interface OrderSummary {
  id: string;
  order_number: string;
  status: string;
  planned_pickup_date?: string | null;
  planned_delivery_date?: string | null;
  created_at: string;
}

export interface OrderDetail extends OrderSummary {
  notes?: string | null;
  assigned_driver_id?: string | null;
  loading_locked?: boolean;
  stops: OrderStop[];
  vehicles: OrderVehicle[];
}

export interface TimelineEntry {
  id: string;
  event_type: string;
  message: string;
  created_at: string;
}

export interface DriverOption {
  id: string;
  user?: { first_name?: string; last_name?: string };
}

export interface FleetOption {
  id: string;
  registration_number?: string | null;
}

export interface SuggestDriverResponse {
  recommended?: { driver_id?: string | null } | null;
}
