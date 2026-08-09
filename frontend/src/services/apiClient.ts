import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from "axios";
import { API_BASE_URL } from "../app/config";
import type { ApiErrorBody, ApiResponse, PaginatedResult, TokenResponse } from "../types/api";

const ACCESS_TOKEN_KEY = "prodrive_access_token";
const REFRESH_TOKEN_KEY = "prodrive_refresh_token";

export class ApiClientError extends Error {
  code: string;
  status: number;

  constructor(code: string, message: string, status = 400) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

function extractError(error: AxiosError<ApiErrorBody>): ApiClientError {
  const payload = error.response?.data;
  return new ApiClientError(
    payload?.error?.code ?? "REQUEST_FAILED",
    payload?.error?.message ?? error.message ?? "Request failed.",
    error.response?.status ?? 500,
  );
}

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(client: AxiosInstance): Promise<string> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new ApiClientError("UNAUTHORIZED", "Session expired.", 401);
  }
  const response = await client.post<ApiResponse<TokenResponse>>("/auth/refresh", {
    refresh_token: refreshToken,
  });
  const { access_token, refresh_token } = response.data.data;
  setTokens(access_token, refresh_token);
  return access_token;
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: { Accept: "application/json" },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const original = error.config;
    if (
      error.response?.status === 401 &&
      original &&
      !original.url?.includes("/auth/login") &&
      !original.url?.includes("/auth/refresh")
    ) {
      try {
        refreshPromise ??= refreshAccessToken(apiClient);
        const accessToken = await refreshPromise;
        refreshPromise = null;
        original.headers.Authorization = `Bearer ${accessToken}`;
        return apiClient(original);
      } catch {
        refreshPromise = null;
        clearTokens();
      }
    }
    throw extractError(error);
  },
);

export async function apiGet<T>(path: string, params?: Record<string, unknown>): Promise<T> {
  const response = await apiClient.get<ApiResponse<T>>(path, { params });
  return response.data.data;
}

export async function apiGetList<T>(
  path: string,
  params?: Record<string, unknown>,
): Promise<PaginatedResult<T>> {
  const response = await apiClient.get<ApiResponse<T[]>>(path, { params });
  const pagination = response.data.meta?.pagination;
  return {
    items: response.data.data,
    total: pagination?.total ?? response.data.data.length,
    page: pagination?.page ?? 1,
    pageSize: pagination?.page_size ?? response.data.data.length,
  };
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await apiClient.post<ApiResponse<T>>(path, body);
  return response.data.data;
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const response = await apiClient.put<ApiResponse<T>>(path, body);
  return response.data.data;
}

export async function apiDelete<T>(path: string): Promise<T> {
  const response = await apiClient.delete<ApiResponse<T>>(path);
  return response.data.data;
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const response = await apiClient.post<ApiResponse<T>>(path, formData);
  return response.data.data;
}
