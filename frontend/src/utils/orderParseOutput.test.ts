import { describe, expect, it } from "vitest";
import type { OrderParseOutput } from "../types/api";
import { buildTableRows, collectParseValidationMessages } from "./orderParseOutput";

describe("orderParseOutput", () => {
  it("builds editable table rows from vehicle notes", () => {
    const output: OrderParseOutput = {
      pickup_stops: [{ stop_type: "PICKUP", sequence: 1, city: "Wanze" }],
      delivery_stops: [],
      vehicles: [
        {
          vin: "6FPPXXMJ2PPL53082",
          make: "Ford",
          model: "Ranger",
          notes: "Stock ID: AS19517; License plate: 2FOA296",
        },
      ],
      reference_numbers: ["8100-20260814-507"],
      field_confidence: { autohero_stock: 0.96 },
    };

    const rows = buildTableRows(output);

    expect(rows[0]).toMatchObject({
      stock_id: "AS19517",
      vin: "6FPPXXMJ2PPL53082",
      model: "Ranger",
      license_plate: "2FOA296",
      location: "Wanze",
      ll_id: "8100-20260814-507",
      autohero_car: true,
    });
  });

  it("collects validation errors, warnings, and vehicle count", () => {
    const output: OrderParseOutput = {
      pickup_stops: [],
      delivery_stops: [],
      vehicles: [{ vin: "123" }, { vin: "456" }],
      missing_fields: ["customer_name"],
      warnings: ["Double-check VIN"],
      field_confidence: { vin: 0.5 },
    };

    const result = collectParseValidationMessages(output);

    expect(result.errors).toContain("customer_name");
    expect(result.warnings.some((item) => item.includes("Double-check VIN"))).toBe(true);
    expect(result.vehicleCount).toBe(2);
  });
});
