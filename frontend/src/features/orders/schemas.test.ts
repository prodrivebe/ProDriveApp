import { describe, expect, it } from "vitest";
import { createOrderSchema } from "./schemas";

describe("createOrderSchema", () => {
  it("requires customer, stops, and vehicles", () => {
    const result = createOrderSchema.safeParse({
      customer_id: "",
      pickup_stops: [],
      delivery_stops: [],
      vehicles: [],
    });
    expect(result.success).toBe(false);
  });

  it("accepts a valid payload", () => {
    const result = createOrderSchema.safeParse({
      customer_id: "customer-1",
      pickup_stops: [{ stop_type: "PICKUP", sequence: 1, city: "Hamburg" }],
      delivery_stops: [{ stop_type: "DELIVERY", sequence: 1, city: "Berlin" }],
      vehicles: [{ make: "BMW", model: "X3" }],
    });
    expect(result.success).toBe(true);
  });
});
