import { useAuth } from "./useAuth";
import type { UserRole } from "../types/api";

export function usePermissions() {
  const { user } = useAuth();
  const role: UserRole | null = user?.role ?? null;

  return {
    role,
    isAdmin: role === "ADMIN",
    isDispatcher: role === "DISPATCHER",
    isStaff: role === "ADMIN" || role === "DISPATCHER",
    canManageSettings: role === "ADMIN",
    canDeleteResources: role === "ADMIN",
  };
}
