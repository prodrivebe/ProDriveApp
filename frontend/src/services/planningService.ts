import { apiGet, apiPost } from "./apiClient";
import type {
  LoadPlanPayload,
  LoadPlanResponse,
  OptimizationResponse,
  PlanningAssignPayload,
  PlanningBoardResponse,
  ValidatePlanPayload,
  ValidationResponse,
} from "../types/api";

export interface PlanningBoardParams {
  search?: string;
  planned_date?: string;
  driver_id?: string;
  truck_id?: string;
  trailer_id?: string;
}

export const planningService = {
  getBoard: (params: PlanningBoardParams = {}) =>
    apiGet<PlanningBoardResponse>("/planning/board", params),

  assign: (payload: PlanningAssignPayload) =>
    apiPost<{ id: string; status: string }>("/planning/assign", payload),

  optimize: (orderId: string, includeRoute = true) =>
    apiPost<OptimizationResponse>("/planning/optimize", {
      order_id: orderId,
      include_route: includeRoute,
    }),

  validate: (payload: ValidatePlanPayload) =>
    apiPost<ValidationResponse>("/planning/validate", payload),

  saveLoadPlan: (payload: LoadPlanPayload) =>
    apiPost<LoadPlanResponse>("/planning/load-plan", payload),

  getLoadPlan: (orderId: string) =>
    apiGet<LoadPlanResponse>(`/planning/load-plan/${orderId}`),
};
