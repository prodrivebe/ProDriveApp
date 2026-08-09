import { apiGet, apiPost } from "./apiClient";
import type { AISuggestion, ApproveSuggestionPayload } from "../types/api";

export interface AISuggestionListParams {
  status?: string;
  suggestion_type?: string;
}

export const aiService = {
  parseOrder: (message: string) =>
    apiPost<AISuggestion>("/ai/parse-order", { message }),

  recommendDriver: (orderId: string) =>
    apiPost<AISuggestion>("/ai/recommend-driver", { order_id: orderId }),

  listSuggestions: (params: AISuggestionListParams = {}) =>
    apiGet<AISuggestion[]>("/ai/suggestions", params),

  getSuggestion: (suggestionId: string) =>
    apiGet<AISuggestion>(`/ai/suggestions/${suggestionId}`),

  approveSuggestion: (suggestionId: string, payload: ApproveSuggestionPayload = {}) =>
    apiPost<AISuggestion>(`/ai/suggestions/${suggestionId}/approve`, payload),

  rejectSuggestion: (suggestionId: string, reason?: string) =>
    apiPost<AISuggestion>(`/ai/suggestions/${suggestionId}/reject`, { reason }),
};
