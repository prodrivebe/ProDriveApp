import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginPage } from "./LoginPage";
import { renderWithProviders } from "../test/testUtils";
import * as authHook from "../hooks/useAuth";

vi.mock("../hooks/useAuth");

describe("LoginPage", () => {
  beforeEach(() => {
    vi.spyOn(authHook, "useAuth").mockReturnValue({
      user: null,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });
  });

  it("validates required fields", async () => {
    renderWithProviders(<LoginPage />);
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText(/valid email/i)).toBeInTheDocument();
  });

  it("submits credentials", async () => {
    const login = vi.fn().mockResolvedValue(undefined);
    vi.spyOn(authHook, "useAuth").mockReturnValue({
      user: null,
      loading: false,
      login,
      logout: vi.fn(),
    });

    renderWithProviders(<LoginPage />);
    await userEvent.type(screen.getByLabelText(/email/i), "admin@example.com");
    await userEvent.type(screen.getByLabelText(/password/i), "Admin123!");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith("admin@example.com", "Admin123!");
    });
  });
});
