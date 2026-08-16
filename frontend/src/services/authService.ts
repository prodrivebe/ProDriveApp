import { apiGet, apiPost, clearTokens, setTokens } from "./apiClient";
import type { TokenResponse, UserProfile } from "../types/api";

export async function login(username: string, password: string): Promise<UserProfile> {
  const tokens = await apiPost<TokenResponse>("/auth/login", { username, password });
  setTokens(tokens.access_token, tokens.refresh_token);
  const profile = await apiGet<UserProfile>("/auth/me");
  if (profile.role === "DRIVER") {
    clearTokens();
    throw new Error("Drivers must use the mobile app.");
  }
  return profile;
}

export async function logout(): Promise<void> {
  const refreshToken = localStorage.getItem("prodrive_refresh_token");
  if (refreshToken) {
    try {
      await apiPost("/auth/logout", { refresh_token: refreshToken });
    } catch {
      // Ignore remote logout failures.
    }
  }
  clearTokens();
}

export async function fetchCurrentUser(): Promise<UserProfile | null> {
  if (!localStorage.getItem("prodrive_access_token")) {
    return null;
  }
  try {
    const profile = await apiGet<UserProfile>("/auth/me");
    if (profile.role === "DRIVER") {
      clearTokens();
      return null;
    }
    return profile;
  } catch {
    clearTokens();
    return null;
  }
}
