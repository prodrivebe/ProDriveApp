import { apiGet, ApiClientError } from "./apiClient";
import type { KpiDashboard, OrdersReport, SearchResponse } from "../types/api";

function parseKpiDashboard(data: KpiDashboard): KpiDashboard {
  const fleet = data.fleet;
  if (
    !fleet?.drivers ||
    !fleet?.trucks ||
    !fleet?.trailers ||
    typeof fleet.drivers.active !== "number" ||
    typeof fleet.trucks.total !== "number" ||
    typeof fleet.trailers.active !== "number"
  ) {
    throw new ApiClientError(
      "INVALID_KPI_RESPONSE",
      "KPI dashboard response is missing fleet summary details.",
    );
  }
  return data;
}

export const dashboardService = {
  kpi: async () => parseKpiDashboard(await apiGet<KpiDashboard>("/reports/kpi")),
  ordersReport: () => apiGet<OrdersReport>("/reports/orders"),
  search: (query: string) => apiGet<SearchResponse>("/search", { q: query }),
};
