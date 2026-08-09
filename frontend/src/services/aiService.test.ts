import { describe, expect, it } from "vitest";
import type { OrderParseOutput } from "../types/api";

describe("AI suggestion types", () => {
  it("supports low-confidence field highlighting threshold", () => {
    const output: OrderParseOutput = {
      pickup_stops: [],
      delivery_stops: [],
      vehicles: [],
      field_confidence: { vin: 0.61, customer_name: 0.98 },
    };

    expect(output.field_confidence.vin).toBeLessThan(0.7);
    expect(output.field_confidence.customer_name).toBeGreaterThanOrEqual(0.85);
  });
});
