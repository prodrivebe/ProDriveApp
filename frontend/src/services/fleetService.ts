import { apiGet, apiGetList } from "./apiClient";
import type { FleetOverview, Trailer, Truck } from "../types/api";

export const fleetService = {
  overview: () => apiGet<FleetOverview>("/fleet/overview"),

  listTrucks: (params: { page?: number; page_size?: number; active?: boolean } = {}) =>
    apiGetList<Truck>("/trucks", params),

  listTrailers: (params: { page?: number; page_size?: number; active?: boolean } = {}) =>
    apiGetList<Trailer>("/trailers", params),
};
