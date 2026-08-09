import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { DashboardPage } from "./DashboardPage";
import { renderWithProviders } from "../test/testUtils";
import * as authHook from "../hooks/useAuth";

const fullKpi = {
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
};

const emptyKpi = {
  total_orders: 0,
  completed_orders: 0,
  active_orders: 0,
  total_customers: 0,
  total_drivers: 0,
  active_drivers: 0,
  fleet: {
    drivers: { total: 0, active: 0 },
    trucks: { total: 0, active: 0 },
    trailers: { total: 0, active: 0 },
  },
  generated_at: new Date().toISOString(),
};

const ordersReport = {
  total_orders: 10,
  completed_orders: 4,
  cancelled_orders: 0,
  active_orders: 5,
  by_status: { READY: 2, IN_TRANSIT: 3, COMPLETED: 4 },
};

vi.mock("../hooks/useAuth");
vi.mock("../services/documentsService", () => ({
  dashboardService: {
    kpi: vi.fn(),
    ordersReport: vi.fn(),
    search: vi.fn(),
  },
}));
vi.mock("../services/notificationsService", () => ({
  notificationsService: {
    list: vi.fn(),
  },
}));
vi.mock("../services/ordersService", () => ({
  ordersService: {
    list: vi.fn(),
  },
}));
vi.mock("../components/OperationsBoard", () => ({
  OperationsBoard: () => <div>Operations board</div>,
}));

import { dashboardService } from "../services/documentsService";
import { notificationsService } from "../services/notificationsService";
import { ordersService } from "../services/ordersService";

function mockAuth() {
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
}

describe("DashboardPage", () => {
  it("renders operations board widgets with full data", async () => {
    mockAuth();
    vi.mocked(dashboardService.kpi).mockResolvedValue(fullKpi);
    vi.mocked(dashboardService.ordersReport).mockResolvedValue(ordersReport);
    vi.mocked(notificationsService.list).mockResolvedValue([]);
    vi.mocked(ordersService.list).mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 100 });

    renderWithProviders(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Operations Board")).toBeInTheDocument();
      expect(screen.getByText("Waiting assignment")).toBeInTheDocument();
      expect(screen.getByText("Drivers: 2/2 active")).toBeInTheDocument();
      expect(screen.getByText("Active drivers")).toBeInTheDocument();
    });
  });

  it("renders empty state when there is no activity", async () => {
    mockAuth();
    vi.mocked(dashboardService.kpi).mockResolvedValue(emptyKpi);
    vi.mocked(dashboardService.ordersReport).mockResolvedValue({
      ...ordersReport,
      total_orders: 0,
      active_orders: 0,
      by_status: {},
    });
    vi.mocked(notificationsService.list).mockResolvedValue([]);
    vi.mocked(ordersService.list).mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 100 });

    renderWithProviders(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/No transport activity yet/i)).toBeInTheDocument();
      expect(screen.getByText("Drivers: 0/0 active")).toBeInTheDocument();
    });
  });

  it("renders with partial order data", async () => {
    mockAuth();
    vi.mocked(dashboardService.kpi).mockResolvedValue(fullKpi);
    vi.mocked(dashboardService.ordersReport).mockResolvedValue({
      ...ordersReport,
      by_status: { READY: 1 },
    });
    vi.mocked(notificationsService.list).mockResolvedValue([
      {
        id: "n1",
        title: "Delay alert",
        message: "Order delayed",
        type: "ORDER",
        read_at: null,
        created_at: new Date().toISOString(),
      },
    ]);
    vi.mocked(ordersService.list).mockResolvedValue({
      items: [
        {
          id: "o1",
          company_id: "c1",
          customer_id: "cust-1",
          order_number: "PD-001",
          status: "READY",
          assigned_driver_id: null,
          assigned_truck_id: null,
          assigned_trailer_id: null,
          planned_pickup_date: null,
          planned_delivery_date: null,
          notes: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total: 1,
      page: 1,
      pageSize: 100,
    });

    renderWithProviders(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Delay alert")).toBeInTheDocument();
      expect(screen.getByText("Waiting assignment")).toBeInTheDocument();
    });
  });
});
