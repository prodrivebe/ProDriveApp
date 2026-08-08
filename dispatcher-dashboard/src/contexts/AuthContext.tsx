import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  apiGet,
  apiPost,
  clearTokens,
  getAccessToken,
  setTokens,
} from "../services/apiClient";
import type { TokenResponse, UserProfile } from "../types/api";

interface AuthContextValue {
  user: UserProfile | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const loadProfile = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const profile = await apiGet<UserProfile>("/auth/me");
      if (profile.role === "DRIVER") {
        clearTokens();
        setUser(null);
      } else {
        setUser(profile);
      }
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await apiPost<TokenResponse>("/auth/login", {
      email,
      password,
    });
    setTokens(tokens.access_token, tokens.refresh_token);
    const profile = await apiGet<UserProfile>("/auth/me");
    if (profile.role === "DRIVER") {
      clearTokens();
      throw new Error("Drivers must use the mobile app.");
    }
    setUser(profile);
  }, []);

  const logout = useCallback(async () => {
    const refreshToken = localStorage.getItem("prodrive_refresh_token");
    if (refreshToken) {
      try {
        await apiPost("/auth/logout", { refresh_token: refreshToken });
      } catch {
        // Ignore logout errors locally.
      }
    }
    clearTokens();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, logout }),
    [user, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
