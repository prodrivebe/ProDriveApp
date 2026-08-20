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
  customer_name?: string | null;
  assigned_driver_name?: string | null;
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
  company_id?: string;
  company_name: string;
  vat_number?: string | null;
  street?: string | null;
  house_number?: string | null;
  postal_code?: string | null;
  address: string | null;
  city: string | null;
  country: string | null;
  email: string | null;
  invoice_email?: string | null;
  phone: string | null;
  dispatch_phone?: string | null;
  is_active?: boolean;
  notes?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface CustomerCreatePayload {
  company_name: string;
  vat_number?: string | null;
  street?: string | null;
  house_number?: string | null;
  postal_code?: string | null;
  address?: string | null;
  city?: string | null;
  country?: string | null;
  email?: string | null;
  invoice_email?: string | null;
  phone?: string | null;
  dispatch_phone?: string | null;
  is_active?: boolean;
  notes?: string | null;
}

export type CustomerUpdatePayload = CustomerCreatePayload;

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
  first_name?: string | null;
  last_name?: string | null;
  email?: string | null;
  display_name?: string | null;
  phone: string | null;
  address?: string | null;
  country?: string | null;
  date_of_birth?: string | null;
  id_document_number?: string | null;
  id_expiry?: string | null;
  driving_license?: string | null;
  driving_licence_expiry?: string | null;
  adr_certificate?: string | null;
  code95_expiry?: string | null;
  tachograph_card_number?: string | null;
  tachograph_card_expiry?: string | null;
  visa_residence_expiry?: string | null;
  active: boolean;
  notes: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface DriverCreatePayload {
  user_id?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  password?: string;
  phone?: string | null;
  address?: string | null;
  country?: string | null;
  date_of_birth?: string | null;
  id_document_number?: string | null;
  id_expiry?: string | null;
  driving_license?: string | null;
  driving_licence_expiry?: string | null;
  adr_certificate?: string | null;
  code95_expiry?: string | null;
  tachograph_card_number?: string | null;
  tachograph_card_expiry?: string | null;
  visa_residence_expiry?: string | null;
  notes?: string | null;
  active?: boolean;
}

export interface DriverUpdatePayload {
  first_name?: string | null;
  last_name?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  country?: string | null;
  date_of_birth?: string | null;
  id_document_number?: string | null;
  id_expiry?: string | null;
  driving_license?: string | null;
  driving_licence_expiry?: string | null;
  adr_certificate?: string | null;
  code95_expiry?: string | null;
  tachograph_card_number?: string | null;
  tachograph_card_expiry?: string | null;
  visa_residence_expiry?: string | null;
  notes?: string | null;
  active?: boolean;
}

export interface Truck {
  id: string;
  company_id?: string;
  registration_number: string;
  active: boolean;
  brand: string | null;
  model: string | null;
  vin?: string | null;
  capacity?: number | null;
  current_mileage?: number | null;
  created_at?: string;
  updated_at?: string;
}

export interface TruckCreatePayload {
  registration_number: string;
  brand?: string | null;
  model?: string | null;
  vin?: string | null;
  capacity?: number | null;
  active?: boolean;
}

export interface TruckUpdatePayload {
  registration_number: string;
  brand?: string | null;
  model?: string | null;
  vin?: string | null;
  capacity?: number | null;
  current_mileage?: number | null;
  active?: boolean;
}

export interface TruckMaintenanceRecord {
  id: string;
  truck_id: string;
  maintenance_date: string;
  mileage: number | null;
  maintenance_type: string;
  notes: string | null;
  created_at: string;
}

export interface TruckInspectionRecord {
  id: string;
  truck_id: string;
  inspection_date: string;
  mileage: number | null;
  inspection_type: string;
  notes: string | null;
  created_at: string;
}

export interface TruckTireRecord {
  id: string;
  truck_id: string;
  tire_date: string;
  mileage: number | null;
  tire_type: string;
  notes: string | null;
  created_at: string;
}

export interface TruckMaintenanceCreatePayload {
  maintenance_date: string;
  mileage?: number | null;
  maintenance_type: string;
  notes?: string | null;
}

export interface TruckInspectionCreatePayload {
  inspection_date: string;
  mileage?: number | null;
  inspection_type: string;
  notes?: string | null;
}

export interface TruckTireCreatePayload {
  tire_date: string;
  mileage?: number | null;
  tire_type: string;
  notes?: string | null;
}

export interface Trailer {
  id: string;
  registration_number: string;
  active: boolean;
  trailer_type: string | null;
  maximum_vehicle_count?: number;
  maximum_height?: number | null;
  maximum_weight?: number | null;
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
export type AISuggestionType = "ORDER_PARSE" | "DRIVER_RECOMMENDATION" | "LOADING_OPTIMIZATION";

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
  stock_id?: string | null;
  license_plate?: string | null;
  location?: string | null;
  ll_id?: string | null;
  autohero_car?: boolean | null;
  notes?: string | null;
}

export interface OrderParseTableRow {
  stock_id?: string | null;
  vin?: string | null;
  model?: string | null;
  license_plate?: string | null;
  location?: string | null;
  ll_id?: string | null;
  autohero_car?: boolean | null;
  make?: string | null;
}

export interface OrderParseOutput {
  customer_name?: string | null;
  pickup_stops: OrderParseStopDraft[];
  delivery_stops: OrderParseStopDraft[];
  vehicles: OrderParseVehicleDraft[];
  table_rows?: OrderParseTableRow[];
  planned_pickup_date?: string | null;
  planned_delivery_date?: string | null;
  notes?: string | null;
  missing_fields?: string[];
  validation_errors?: string[];
  warnings?: string[];
  vehicle_count?: number;
  reference_numbers?: string[];
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

export interface PlanningOrderCard {
  id: string;
  order_number: string;
  status: string;
  customer_id: string;
  assigned_driver_id: string | null;
  assigned_truck_id: string | null;
  assigned_trailer_id: string | null;
  planned_pickup_date: string | null;
  planned_delivery_date: string | null;
  vehicle_count: number;
  column: string;
}

export type OrderSummary = OrderListItem;

export interface ResourceAvailability {
  id: string;
  label: string;
  resource_type: string;
  available: boolean;
  active_assignments: number;
  capacity_indicator: string | null;
  conflict: boolean;
  conflict_reason: string | null;
}

export interface PlanningBoardResponse {
  columns: Record<string, PlanningOrderCard[]>;
  drivers: ResourceAvailability[];
  trucks: ResourceAvailability[];
  trailers: ResourceAvailability[];
  active_assignments: Array<Record<string, unknown>>;
}

export interface PlanningAssignPayload {
  order_id: string;
  driver_id?: string;
  truck_id?: string;
  trailer_id?: string;
  clear_assignment?: boolean;
}

export interface LoadingPositionDraft {
  vehicle_id: string;
  vehicle_label?: string | null;
  upper_deck: boolean;
  trailer_position: number;
  loading_order: number;
  unloading_order: number;
  destination_city?: string | null;
  weight_kg?: number | null;
  height_m?: number | null;
  confirmed_by_dispatcher?: boolean;
  ai_generated?: boolean;
}

export interface LoadPlanPayload {
  order_id: string;
  positions?: Array<{
    vehicle_id: string;
    upper_deck: boolean;
    trailer_position: number;
    loading_order: number;
    unloading_order: number;
    destination_city?: string | null;
  }>;
  route_sequence?: string[];
  confirm?: boolean;
  suggestion_id?: string;
  acknowledge_warnings?: boolean;
}

export interface LoadPlanResponse {
  id: string;
  order_id: string;
  trailer_id: string | null;
  status: string;
  estimated_total_height: number | null;
  estimated_total_weight: number | null;
  estimated_travel_km: number | null;
  front_axle_percent: number | null;
  rear_axle_percent: number | null;
  warnings: string[];
  positions: LoadingPositionDraft[];
  route_sequence: string[];
  created_at: string;
  confirmed_at: string | null;
}

export interface OptimizationResponse {
  suggestion_id: string;
  order_id: string;
  loading: Record<string, unknown>;
  route: Record<string, unknown> | null;
  validation: Record<string, unknown>;
  confidence: number;
  reasoning: string[];
  status: string;
}

export interface ValidatePlanPayload {
  order_id: string;
  positions: Array<{
    vehicle_id: string;
    upper_deck: boolean;
    trailer_position: number;
    loading_order: number;
    unloading_order: number;
    destination_city?: string | null;
  }>;
  route_sequence?: string[];
}

export interface ValidationResponse {
  is_valid: boolean;
  errors: Array<{ code: string; message: string; severity?: string }>;
  warnings: Array<{ code: string; message: string; severity?: string }>;
  estimated_total_height_m: number;
  estimated_total_weight_kg: number;
  front_axle_percent: number;
  rear_axle_percent: number;
}
