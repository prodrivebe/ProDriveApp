import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { DashboardPage } from "./DashboardPage";
import { renderWithProviders } from "../test/testUtils";
import * as authHook from "../hooks/useAuth";

vi.mock("../hooks/useAuth");
vi.mock("../services/documentsService", () => ({
  dashboardService: {
    kpi: vi.fn().mockResolvedValue({
      total_orders: 10,
      completed_orders: 4,
      active_orders: 5,
      total_customers: 3,
      total_drivers: 2,
      active_drivers: 2,
      fleet: {
        drivers: { total: 2, active: 2 },
        trucks: { total: 2, active: 2 },
        trailers: { total: 1, active: 1 },
      },
      generated_at: new Date().toISOString(),
    }),
    ordersReport: vi.fn().mockResolvedValue({
      total_orders: 10,
      completed_orders: 4,
      cancelled_orders: 0,
      active_orders: 5,
      by_status: { READY: 2, IN_TRANSIT: 3, COMPLETED: 4 },
    }),
    search: vi.fn(),
  },
}));
vi.mock("../services/notificationsService", () => ({
  notificationsService: {
    list: vi.fn().mockResolvedValue([]),
  },
}));
vi.mock("../services/ordersService", () => ({
  ordersService: {
    list: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 100 }),
  },
}));
vi.mock("../services/driversService", () => ({
  driversService: {
    list: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 100 }),
  },
}));

describe("DashboardPage", () => {
  it("renders operations board widgets", async () => {
    vi.spyOn(authHook, "useAuth").mockReturnValue({
      user: {
        id: "1",
        company_id: "c1",
        first_name: "Admin",
        last_name: "User",
        email: "admin@example.com",
        role: "ADMIN",
        is_active: true,
      },
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderWithProviders(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Operations Board")).toBeInTheDocument();
      expect(screen.getByText("Waiting assignment")).toBeInTheDocument();
    });
  });
});
