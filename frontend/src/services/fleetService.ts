import { apiDelete, apiGet, apiGetList, apiPost, apiPut } from "./apiClient";
import type {
  FleetOverview,
  Trailer,
  Truck,
  TruckCreatePayload,
  TruckInspectionCreatePayload,
  TruckInspectionRecord,
  TruckMaintenanceCreatePayload,
  TruckMaintenanceRecord,
  TruckTireCreatePayload,
  TruckTireRecord,
  TruckUpdatePayload,
} from "../types/api";

export const fleetService = {
  overview: () => apiGet<FleetOverview>("/fleet/overview"),

  listTrucks: (params: { page?: number; page_size?: number; active?: boolean; search?: string } = {}) =>
    apiGetList<Truck>("/trucks", params),

  getTruck: (truckId: string) => apiGet<Truck>(`/trucks/${truckId}`),

  createTruck: (payload: TruckCreatePayload) => apiPost<Truck>("/trucks", payload),

  updateTruck: (truckId: string, payload: TruckUpdatePayload) =>
    apiPut<Truck>(`/trucks/${truckId}`, payload),

  deleteTruck: (truckId: string) => apiDelete<{ message: string }>(`/trucks/${truckId}`),

  listMaintenanceRecords: (truckId: string) =>
    apiGet<TruckMaintenanceRecord[]>(`/trucks/${truckId}/maintenance`),

  createMaintenanceRecord: (truckId: string, payload: TruckMaintenanceCreatePayload) =>
    apiPost<TruckMaintenanceRecord>(`/trucks/${truckId}/maintenance`, payload),

  listInspectionRecords: (truckId: string) =>
    apiGet<TruckInspectionRecord[]>(`/trucks/${truckId}/inspections`),

  createInspectionRecord: (truckId: string, payload: TruckInspectionCreatePayload) =>
    apiPost<TruckInspectionRecord>(`/trucks/${truckId}/inspections`, payload),

  listTireRecords: (truckId: string) =>
    apiGet<TruckTireRecord[]>(`/trucks/${truckId}/tires`),

  createTireRecord: (truckId: string, payload: TruckTireCreatePayload) =>
    apiPost<TruckTireRecord>(`/trucks/${truckId}/tires`, payload),

  listTrailers: (params: { page?: number; page_size?: number; active?: boolean } = {}) =>
    apiGetList<Trailer>("/trailers", params),
};
