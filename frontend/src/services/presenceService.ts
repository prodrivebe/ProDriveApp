import { apiGet } from "./apiClient";

export interface PresenceRecord {
  user_id: string;
  role: string;
  status: string;
  active_order_id: string | null;
  last_seen: string;
}

export const presenceService = {
  list(): Promise<PresenceRecord[]> {
    return apiGet<PresenceRecord[]>("/realtime/presence");
  },
};
