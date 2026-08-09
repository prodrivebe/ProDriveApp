import { describe, expect, it, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import { usePermissions } from "./usePermissions";
import * as authHook from "./useAuth";

describe("usePermissions", () => {
  it("grants settings access to admins only", () => {
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

    const { result } = renderHook(() => usePermissions());
    expect(result.current.canManageSettings).toBe(true);
    expect(result.current.isStaff).toBe(true);
  });

  it("denies settings access to dispatchers", () => {
    vi.spyOn(authHook, "useAuth").mockReturnValue({
      user: {
        id: "2",
        company_id: "c1",
        first_name: "Dispatch",
        last_name: "User",
        email: "dispatch@example.com",
        role: "DISPATCHER",
        is_active: true,
      },
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    const { result } = renderHook(() => usePermissions());
    expect(result.current.canManageSettings).toBe(false);
    expect(result.current.isStaff).toBe(true);
  });
});
