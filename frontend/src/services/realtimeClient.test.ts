import { describe, expect, it, vi } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import { applyRealtimeEvent } from "../services/realtimeClient";

describe("applyRealtimeEvent", () => {
  it("invalidates dashboard and order queries on order assignment", () => {
    const queryClient = new QueryClient();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    applyRealtimeEvent(queryClient, {
      id: "1",
      type: "ORDER_ASSIGNED",
      company_id: "company-1",
      channel: "dispatcher:company-1",
      payload: { order_id: "order-1", order_number: "ORD-001", status: "ASSIGNED" },
      created_at: new Date().toISOString(),
    });

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["dashboard"] });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["orders", "order-1"] });
  });

  it("invalidates notifications on notification events", () => {
    const queryClient = new QueryClient();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    applyRealtimeEvent(queryClient, {
      id: "2",
      type: "NOTIFICATION_CREATED",
      company_id: "company-1",
      channel: "notifications:user-1",
      payload: { notification_id: "n-1" },
      created_at: new Date().toISOString(),
    });

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["notifications"] });
  });
});
