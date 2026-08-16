export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "https://api.prodriveservice.eu/api/v1"
).replace(/\/$/, "");

export const ACCESS_TOKEN_KEY = "prodrive_access_token";
export const REFRESH_TOKEN_KEY = "prodrive_refresh_token";

export class ApiError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

function authHeaders(includeJson = false): HeadersInit {
  const headers: Record<string, string> = {};
  if (includeJson) {
    headers["Content-Type"] = "application/json";
  }
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function parseSuccess<T>(response: Response): Promise<T> {
  const body = await response.json();
  if (!response.ok || !body.success) {
    const error = body.error ?? {};
    throw new ApiError(error.code ?? "REQUEST_FAILED", error.message ?? "Request failed.");
  }
  return body.data as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: authHeaders(),
  });
  return parseSuccess<T>(response);
}

export async function apiPost<T>(path: string, payload?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: authHeaders(payload !== undefined),
    body: payload !== undefined ? JSON.stringify(payload) : undefined,
  });
  return parseSuccess<T>(response);
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
}

export async function apiGetPaginated<T>(path: string): Promise<PaginatedResult<T>> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: authHeaders(),
  });
  const body = await response.json();
  if (!response.ok || !body.success) {
    const error = body.error ?? {};
    throw new ApiError(error.code ?? "REQUEST_FAILED", error.message ?? "Request failed.");
  }
  const total = body.meta?.pagination?.total ?? body.data.length;
  return { items: body.data as T[], total };
}

export function resolveLoginEmail(username: string): string {
  const normalized = username.trim();
  return normalized.includes("@") ? normalized.toLowerCase() : `${normalized.toLowerCase()}@prodrive.demo`;
}

export async function login(username: string, password: string) {
  const tokens = await apiPost<{
    access_token: string;
    refresh_token: string;
  }>("/auth/login", {
    username: username.trim(),
    email: resolveLoginEmail(username),
    password,
  });
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  return tokens;
}

export function logout() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export interface OrderDocument {
  id: string;
  document_type: string;
  file_path: string;
  version?: number;
  generated_at?: string;
}

/**
 * v0.1 backend exposes CMR via /orders/{id}/cmr, not /orders/{id}/documents.
 * Order detail must not fail when the legacy documents list endpoint is absent.
 */
export async function fetchOrderDocuments(orderId: string): Promise<OrderDocument[]> {
  try {
    return await apiGet<OrderDocument[]>(`/orders/${orderId}/documents`);
  } catch {
    try {
      const cmr = await apiGet<OrderDocument>(`/orders/${orderId}/cmr`);
      return [{ ...cmr, document_type: "CMR", version: 2 }];
    } catch {
      return [];
    }
  }
}
