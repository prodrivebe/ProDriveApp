import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./ProtectedRoute";
import { renderWithProviders } from "../test/testUtils";
import * as authHook from "../hooks/useAuth";

vi.mock("../hooks/useAuth");

describe("ProtectedRoute", () => {
  it("redirects unauthenticated users to login", () => {
    vi.spyOn(authHook, "useAuth").mockReturnValue({
      user: null,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderWithProviders(
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<div>Protected content</div>} />
        </Route>
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>,
      { route: "/" },
    );

    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("renders protected content for authenticated staff", () => {
    vi.spyOn(authHook, "useAuth").mockReturnValue({
      user: {
        id: "1",
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

    renderWithProviders(
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<div>Protected content</div>} />
        </Route>
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>,
      { route: "/" },
    );

    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });
});
