import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AiOrderPanel } from "../components/AiOrderPanel";
import { renderWithProviders } from "../test/testUtils";

vi.mock("../services/aiService", () => ({
  aiService: {
    parseOrder: vi.fn().mockResolvedValue({
      id: "suggestion-1",
      status: "PENDING",
      confidence: 0.91,
      output_json: {
        customer_name: "Autohero",
        pickup_stops: [{ stop_type: "PICKUP", sequence: 1, city: "Wanze" }],
        delivery_stops: [{ stop_type: "DELIVERY", sequence: 1, city: "Brussels" }],
        vehicles: [
          {
            vin: "6FPPXXMJ2PPL53082",
            make: "Ford",
            model: "Ranger 3.0 EcoBlue",
            notes: "Stock ID: AS19517; License plate: 2FOA296",
          },
        ],
        missing_fields: ["planned_pickup_date"],
        warnings: ["Verify delivery window"],
        field_confidence: { customer_name: 0.95, autohero_stock: 0.96, vin: 0.62 },
      },
    }),
    approveSuggestion: vi.fn(),
    rejectSuggestion: vi.fn(),
  },
}));

describe("AiOrderPanel table import preview", () => {
  it(
    "shows parsed table rows, validation messages, and confirm step",
    async () => {
      renderWithProviders(
        <AiOrderPanel
          customers={[
            {
              id: "cust-1",
              company_name: "Acme GmbH",
              city: null,
              country: null,
              email: null,
              phone: null,
              address: null,
            },
          ]}
          onOrderCreated={vi.fn()}
        />,
      );

      fireEvent.change(screen.getByLabelText(/customer message/i), {
        target: { value: "Wanze AS19517 6FPPXXMJ2PPL53082 Ford Ranger 2FOA296" },
      });
      await userEvent.click(screen.getByRole("button", { name: /parse order/i }));

      await waitFor(
        () => {
          expect(screen.getByText(/parsed vehicles/i)).toBeInTheDocument();
          expect(screen.getByDisplayValue("AS19517")).toBeInTheDocument();
          expect(screen.getByDisplayValue("6FPPXXMJ2PPL53082")).toBeInTheDocument();
          expect(screen.getByDisplayValue("2FOA296")).toBeInTheDocument();
          expect(screen.getByText(/planned_pickup_date/i)).toBeInTheDocument();
          expect(screen.getByText(/verify delivery window/i)).toBeInTheDocument();
          expect(screen.getByText(/1 vehicle/i)).toBeInTheDocument();
          expect(screen.getByRole("button", { name: /review & confirm/i })).toBeDisabled();
        },
        { timeout: 10000 },
      );
    },
    15000,
  );
});
