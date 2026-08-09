import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { OrdersPage } from "./OrdersPage";
import { renderWithProviders } from "../test/testUtils";
import * as authHook from "../hooks/useAuth";

vi.mock("../hooks/useAuth");
vi.mock("../services/ordersService", () => ({
  ordersService: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: "order-1",
          company_id: "c1",
          customer_id: "cust-1",
          order_number: "ORD-001",
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
      pageSize: 25,
    }),
    get: vi.fn(),
  },
}));
vi.mock("../services/customersService", () => ({
  customersService: {
    list: vi.fn().mockResolvedValue({
      items: [{ id: "cust-1", company_name: "Acme GmbH", city: null, country: null, email: null, phone: null, address: null }],
      total: 1,
      page: 1,
      pageSize: 200,
    }),
  },
}));
vi.mock("../services/driversService", () => ({
  driversService: {
    list: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 200 }),
  },
}));

describe("OrdersPage", () => {
  it("renders paginated order table", async () => {
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

    renderWithProviders(<OrdersPage />);
    await waitFor(() => {
      expect(screen.getByText("ORD-001")).toBeInTheDocument();
      expect(screen.getByText("Acme GmbH")).toBeInTheDocument();
    });
  });
});
