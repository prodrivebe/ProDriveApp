export type UserRole = "ADMIN" | "DISPATCHER" | "DRIVER";

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

export interface ApiErrorBody {
  success: false;
  error: {
    code: string;
    message: string;
  };
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
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
  role: UserRole;
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
  company_name: string | null;
  contact_name: string | null;
  phone: string | null;
  address: string | null;
  city: string | null;
  postal_code: string | null;
  country: string | null;
  progress_status: string;
  arrival_time: string | null;
  departure_time: string | null;
}

export interface OrderVehicle {
  id: string;
  pickup_stop_id: string | null;
  delivery_stop_id: string | null;
  vin: string | null;
  verified_vin: string | null;
  make: string | null;
  model: string | null;
  color: string | null;
}

export interface OrderDetail extends OrderListItem {
  stops: OrderStop[];
  vehicles: OrderVehicle[];
}

export interface OrderTimelineEntry {
  id: string;
  order_id: string;
  event_type: string;
  description: string;
  created_by: string | null;
  created_at: string;
}

export interface VehiclePhoto {
  id: string;
  vehicle_id: string;
  order_id: string | null;
  photo_type: string;
  file_path: string;
  file_name: string | null;
  uploaded_at: string;
}

export interface VehicleDamage {
  id: string;
  vehicle_id: string;
  damage_type: string;
  severity: string;
  description: string | null;
  location: string | null;
  reported_at: string;
  photo_ids: string[];
}

export interface OrderDocument {
  id: string;
  order_id: string;
  document_type: string;
  file_path: string;
  file_name: string;
  version: number;
  uploaded_at: string;
}

export interface CompletionChecklist {
  pickup_completed: boolean;
  delivery_completed: boolean;
  vins_verified: boolean;
  photos_uploaded: boolean;
  documents_uploaded: boolean;
  damage_reports_completed: boolean;
  can_complete: boolean;
  completion_percentage: number;
  completed_items: string[];
  missing_items: string[];
}

export interface Customer {
  id: string;
  company_name: string;
  city: string | null;
  country: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
}

export interface CustomerContact {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  job_title: string | null;
}

export interface Driver {
  id: string;
  user_id: string;
  phone: string | null;
  active: boolean;
  notes: string | null;
}

export interface Truck {
  id: string;
  registration_number: string;
  active: boolean;
  make: string | null;
  model: string | null;
}

export interface Trailer {
  id: string;
  registration_number: string;
  active: boolean;
  trailer_type: string | null;
}

export interface FleetOverview {
  drivers: { total: number; active: number };
  trucks: { total: number; active: number };
  trailers: { total: number; active: number };
}

export interface FleetAssignment {
  id: string;
  driver_id: string;
  truck_id: string | null;
  trailer_id: string | null;
  order_id: string | null;
  active: boolean;
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

export interface CompanySettings {
  timezone: string;
  default_currency: string;
  require_vehicle_photos: boolean;
  primary_color: string;
}

export interface CreateOrderPayload {
  customer_id: string;
  planned_pickup_date?: string | null;
  planned_delivery_date?: string | null;
  notes?: string | null;
  stops: Array<{
    stop_type: "PICKUP" | "DELIVERY";
    sequence: number;
    city?: string | null;
    address?: string | null;
    country?: string | null;
  }>;
  vehicles: Array<{
    make?: string | null;
    model?: string | null;
    vin?: string | null;
    pickup_stop_id?: string | null;
    delivery_stop_id?: string | null;
  }>;
}

export interface AssignDriverPayload {
  driver_id: string;
  truck_id?: string | null;
  trailer_id?: string | null;
}

export type AISuggestionStatus = "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED";
export type AISuggestionType = "ORDER_PARSE" | "DRIVER_RECOMMENDATION";

export interface AISuggestion {
  id: string;
  company_id: string;
  suggestion_type: AISuggestionType;
  input_text: string | null;
  output_json: Record<string, unknown>;
  confidence: number;
  status: AISuggestionStatus;
  prompt_version: string;
  model_version: string;
  created_by: string;
  approved_by: string | null;
  created_at: string;
  approved_at: string | null;
  related_order_id: string | null;
}

export interface ApproveSuggestionPayload {
  customer_id?: string;
  edited_output?: Record<string, unknown>;
}

export interface OrderParseStopDraft {
  stop_type: "PICKUP" | "DELIVERY";
  sequence: number;
  city?: string | null;
  address?: string | null;
  country?: string | null;
}

export interface OrderParseVehicleDraft {
  make?: string | null;
  model?: string | null;
  vin?: string | null;
}

export interface OrderParseOutput {
  customer_name?: string | null;
  pickup_stops: OrderParseStopDraft[];
  delivery_stops: OrderParseStopDraft[];
  vehicles: OrderParseVehicleDraft[];
  planned_pickup_date?: string | null;
  planned_delivery_date?: string | null;
  notes?: string | null;
  missing_fields?: string[];
  field_confidence: Record<string, number>;
  overall_confidence?: number;
  created_order_id?: string;
  rejection_reason?: string;
}

export interface DriverRecommendationCandidate {
  driver_id: string;
  driver_name: string;
  confidence: number;
  reasons: string[];
}

export interface DriverRecommendationOutput {
  order_id: string;
  recommended: DriverRecommendationCandidate | null;
  alternatives: DriverRecommendationCandidate[];
  overall_confidence: number;
}
