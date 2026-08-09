import { apiGet, apiGetList, apiPost, apiPut, apiUpload } from "./apiClient";
import type {
  AssignDriverPayload,
  CompletionChecklist,
  CreateOrderPayload,
  OrderDetail,
  OrderDocument,
  OrderListItem,
  OrderTimelineEntry,
  OrderVehicle,
  VehicleDamage,
  VehiclePhoto,
} from "../types/api";

export interface OrderListParams {
  page?: number;
  page_size?: number;
  status?: string;
  customer_id?: string;
  driver_id?: string;
  search?: string;
}

export const ordersService = {
  list: (params: OrderListParams = {}) =>
    apiGetList<OrderListItem>("/orders", params),

  get: (orderId: string) => apiGet<OrderDetail>(`/orders/${orderId}`),

  create: (payload: CreateOrderPayload) => apiPost<OrderDetail>("/orders", payload),

  assignDriver: (orderId: string, payload: AssignDriverPayload) =>
    apiPost<OrderDetail>(`/orders/${orderId}/assign-driver`, payload),

  timeline: (orderId: string) =>
    apiGet<OrderTimelineEntry[]>(`/orders/${orderId}/timeline`),

  checklist: (orderId: string) =>
    apiGet<CompletionChecklist>(`/orders/${orderId}/completion-checklist`),

  listDocuments: (orderId: string) =>
    apiGet<OrderDocument[]>(`/orders/${orderId}/documents`),

  uploadDocument: (orderId: string, file: File, documentType = "CMR") => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("document_type", documentType);
    return apiUpload<OrderDocument>(`/orders/${orderId}/documents`, formData);
  },

  listVehiclePhotos: (orderId: string, vehicleId: string) =>
    apiGet<VehiclePhoto[]>(`/orders/${orderId}/vehicles/${vehicleId}/photos`),

  listVehicleDamage: (orderId: string, vehicleId: string) =>
    apiGet<VehicleDamage[]>(`/orders/${orderId}/vehicles/${vehicleId}/damage`),

  updateStatus: (orderId: string, payload: { customer_id: string; status?: string }) =>
    apiPut<OrderDetail>(`/orders/${orderId}`, payload),
};

export type { OrderVehicle };
