import { apiGet } from "./apiClient";
import type { KpiDashboard, OrdersReport, SearchResponse } from "../types/api";

export const dashboardService = {
  kpi: () => apiGet<KpiDashboard>("/reports/kpi"),
  ordersReport: () => apiGet<OrdersReport>("/reports/orders"),
  search: (query: string) => apiGet<SearchResponse>("/search", { q: query }),
};
