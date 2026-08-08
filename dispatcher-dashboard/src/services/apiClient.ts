import { API_BASE_URL } from "../config/api";
import type { ApiError, ApiResponse } from "../types/api";

const TOKEN_KEY = "prodrive_access_token";
const REFRESH_KEY = "prodrive_refresh_token";

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_KEY, refreshToken);
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export class ApiClientError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const body = (await response.json()) as ApiResponse<T> | ApiError;
  if (!response.ok || !body.success) {
    const errorBody = body as ApiError;
    throw new ApiClientError(
      errorBody.error?.code ?? "REQUEST_FAILED",
      errorBody.error?.message ?? "Request failed.",
    );
  }
  return (body as ApiResponse<T>).data;
}

function buildHeaders(jsonBody = false): HeadersInit {
  const headers: Record<string, string> = {};
  if (jsonBody) {
    headers["Content-Type"] = "application/json";
  }
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: buildHeaders(),
  });
  return parseResponse<T>(response);
}

export async function apiPost<T>(
  path: string,
  body?: unknown,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: buildHeaders(body !== undefined),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return parseResponse<T>(response);
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PUT",
    headers: buildHeaders(true),
    body: JSON.stringify(body),
  });
  return parseResponse<T>(response);
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
}

export async function apiGetList<T>(
  path: string,
): Promise<PaginatedResult<T>> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: buildHeaders(),
  });
  const body = (await response.json()) as ApiResponse<T[]> | ApiError;
  if (!response.ok || !body.success) {
    const errorBody = body as ApiError;
    throw new ApiClientError(
      errorBody.error?.code ?? "REQUEST_FAILED",
      errorBody.error?.message ?? "Request failed.",
    );
  }
  const successBody = body as ApiResponse<T[]>;
  return {
    items: successBody.data,
    total: successBody.meta?.pagination?.total ?? successBody.data.length,
  };
}
