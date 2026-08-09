import { apiGet, apiPost } from "./apiClient";
import type { Notification } from "../types/api";

export const notificationsService = {
  list: (unreadOnly = false) =>
    apiGet<Notification[]>("/notifications", { unread_only: unreadOnly }),

  markRead: (notificationId: string) =>
    apiPost<Notification>(`/notifications/${notificationId}/read`),

  markAllRead: () => apiPost<{ updated_count: number }>("/notifications/read-all"),
};
