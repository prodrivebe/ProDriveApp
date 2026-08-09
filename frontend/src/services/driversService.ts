import { apiGet, apiGetList } from "./apiClient";
import type { Driver } from "../types/api";

export const driversService = {
  list: (params: { page?: number; page_size?: number; active?: boolean; search?: string } = {}) =>
    apiGetList<Driver>("/drivers", params),

  get: (driverId: string) => apiGet<Driver>(`/drivers/${driverId}`),
};
