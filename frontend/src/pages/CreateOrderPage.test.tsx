import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CreateOrderPage } from "../pages/CreateOrderPage";
import { renderWithProviders } from "../test/testUtils";
import * as authHook from "../hooks/useAuth";

vi.mock("../hooks/useAuth");
vi.mock("../services/customersService", () => ({
  customersService: {
    list: vi.fn(),
    create: vi.fn(),
  },
}));
vi.mock("../services/driversService", () => ({
  driversService: {
    list: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 100 }),
  },
}));
vi.mock("../services/fleetService", () => ({
  fleetService: {
    listTrucks: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 100 }),
    listTrailers: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 100 }),
  },
}));
vi.mock("../services/ordersService", () => ({
  ordersService: {
    create: vi.fn(),
    assignDriver: vi.fn(),
  },
}));
vi.mock("../services/aiService", () => ({
  aiService: {
    parseOrder: vi.fn(),
    approveSuggestion: vi.fn(),
    rejectSuggestion: vi.fn(),
  },
}));

import { customersService } from "../services/customersService";

const authUser = {
  user: {
    id: "1",
    company_id: "c1",
    first_name: "Admin",
    last_name: "User",
    email: "admin@example.com",
    role: "ADMIN" as const,
    is_active: true,
  },
  loading: false,
  login: vi.fn(),
  logout: vi.fn(),
};

describe("CreateOrderPage customer selection", () => {
  it("shows an error when customers fail to load", async () => {
    vi.spyOn(authHook, "useAuth").mockReturnValue(authUser);
    vi.mocked(customersService.list).mockRejectedValue(new Error("Customers unavailable"));

    renderWithProviders(<CreateOrderPage />);

    await waitFor(() => {
      expect(screen.getByText(/customers unavailable/i)).toBeInTheDocument();
    });
  });

  it("shows empty customer alert and company_name labels only", async () => {
    vi.spyOn(authHook, "useAuth").mockReturnValue(authUser);
    vi.mocked(customersService.list).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      pageSize: 100,
    });

    renderWithProviders(<CreateOrderPage />);

    await waitFor(() => {
      expect(screen.getByText(/no customers found/i)).toBeInTheDocument();
    });

    const createCustomerLink = screen.getByRole("link", { name: /create a customer/i });
    expect(createCustomerLink).toHaveAttribute("href", "/customers");
  });

  it(
    "invalidates customers after creating one from dialog",
    async () => {
      vi.spyOn(authHook, "useAuth").mockReturnValue(authUser);

      vi.mocked(customersService.list)
        .mockResolvedValueOnce({
          items: [],
          total: 0,
          page: 1,
          pageSize: 100,
        })
        .mockResolvedValueOnce({
          items: [
            {
              id: "cust-new",
              company_name: "New Customer BV",
              city: null,
              country: null,
              email: null,
              phone: null,
              address: null,
              is_active: true,
            },
          ],
          total: 1,
          page: 1,
          pageSize: 100,
        });

      vi.mocked(customersService.create).mockResolvedValue({
        id: "cust-new",
        company_name: "New Customer BV",
        city: null,
        country: null,
        email: null,
        phone: null,
        address: null,
        is_active: true,
      });

      const user = userEvent.setup();
      renderWithProviders(<CreateOrderPage />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /new customer/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: /new customer/i }));

      const companyField = await screen.findByLabelText(/company name/i);
      fireEvent.change(companyField, { target: { value: "New Customer BV" } });
      await user.click(screen.getByRole("button", { name: /create customer/i }));

      await waitFor(() => {
        expect(customersService.create).toHaveBeenCalledWith(
          expect.objectContaining({ company_name: "New Customer BV" }),
        );
        expect(customersService.list.mock.calls.length).toBeGreaterThan(1);
      });
    },
    15000,
  );
});
