import { apiDelete, apiGet, apiGetList, apiPost, apiPut } from "./apiClient";
import type { Driver, DriverCreatePayload, DriverUpdatePayload } from "../types/api";

export const driversService = {
  list: (params: { page?: number; page_size?: number; active?: boolean; search?: string } = {}) =>
    apiGetList<Driver>("/drivers", params),

  get: (driverId: string) => apiGet<Driver>(`/drivers/${driverId}`),

  create: (payload: DriverCreatePayload) => apiPost<Driver>("/drivers", payload),

  update: (driverId: string, payload: DriverUpdatePayload) =>
    apiPut<Driver>(`/drivers/${driverId}`, payload),

  delete: (driverId: string) => apiDelete<{ message: string }>(`/drivers/${driverId}`),
};
