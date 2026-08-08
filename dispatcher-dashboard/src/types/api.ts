export interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta?: {
    pagination?: {
      page: number;
      page_size: number;
      total: number;
    };
  };
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
  };
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  id: string;
  company_id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: "ADMIN" | "DISPATCHER" | "DRIVER";
  is_active: boolean;
}

export interface OrderListItem {
  id: string;
  company_id: string;
  customer_id: string;
  order_number: string;
  status: string;
  assigned_driver_id: string | null;
  assigned_truck_id: string | null;
  assigned_trailer_id: string | null;
  planned_pickup_date: string | null;
  planned_delivery_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderStop {
  id: string;
  stop_type: "PICKUP" | "DELIVERY";
  sequence: number;
  city: string | null;
  address: string | null;
  country: string | null;
}

export interface OrderVehicle {
  id: string;
  make: string | null;
  model: string | null;
  vin: string | null;
}

export interface OrderDetail extends OrderListItem {
  stops: OrderStop[];
  vehicles: OrderVehicle[];
}

export interface Customer {
  id: string;
  company_name: string;
  city: string | null;
  country: string | null;
  email: string | null;
  phone: string | null;
}

export interface Driver {
  id: string;
  user_id: string;
  phone: string | null;
  active: boolean;
}

export interface Truck {
  id: string;
  registration_number: string;
  active: boolean;
}

export interface Trailer {
  id: string;
  registration_number: string;
  active: boolean;
}

export interface FleetOverview {
  drivers: { total: number; active: number };
  trucks: { total: number; active: number };
  trailers: { total: number; active: number };
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: string;
  read_at: string | null;
  created_at: string;
}

export interface KpiDashboard {
  total_orders: number;
  completed_orders: number;
  active_orders: number;
  total_customers: number;
  total_drivers: number;
  active_drivers: number;
  fleet: FleetOverview;
  generated_at: string;
}

export interface OrdersReport {
  total_orders: number;
  completed_orders: number;
  cancelled_orders: number;
  active_orders: number;
  by_status: Record<string, number>;
}

export interface DriversReport {
  total_drivers: number;
  drivers: Array<{
    driver_id: string;
    driver_name: string;
    assigned_orders: number;
    completed_orders: number;
    active_orders: number;
  }>;
}

export interface CustomersReport {
  total_customers: number;
  customers: Array<{
    customer_id: string;
    company_name: string;
    total_orders: number;
    completed_orders: number;
  }>;
}

export interface FleetReport {
  drivers: FleetOverview["drivers"];
  trucks: FleetOverview["trucks"];
  trailers: FleetOverview["trailers"];
  assigned_drivers: number;
  assigned_trucks: number;
  assigned_trailers: number;
}

export interface SearchResponse {
  orders: SearchResultItem[];
  customers: SearchResultItem[];
  drivers: SearchResultItem[];
  vehicles: SearchResultItem[];
}

export interface SearchResultItem {
  type: string;
  id: string;
  title: string;
  subtitle: string | null;
}

export interface OrderTimelineEntry {
  id: string;
  event_type: string;
  description: string;
  created_at: string;
}

export interface ParsedOrderDraft {
  pickup_stops: Array<{ stop_type: string; sequence: number; city?: string }>;
  delivery_stops: Array<{ stop_type: string; sequence: number; city?: string }>;
  vehicles: Array<{ make?: string; model?: string }>;
  missing_fields: string[];
  confidence_score: number;
}

export interface DriverSuggestion {
  driver_id: string;
  driver_name: string;
  score: number;
  reason: string;
}
