import { ApiClientError } from "../services/apiClient";

export function getErrorMessage(error: unknown, fallback = "Something went wrong."): string {
  if (error instanceof ApiClientError) return error.message;
  if (error instanceof Error) return error.message;
  return fallback;
}

export function isForbidden(error: unknown): boolean {
  return error instanceof ApiClientError && error.status === 403;
}

export function isNotFound(error: unknown): boolean {
  return error instanceof ApiClientError && error.status === 404;
}

export function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiClientError && error.status === 401;
}

export function isValidationError(error: unknown): boolean {
  return error instanceof ApiClientError && error.status === 422;
}

export function isNetworkError(error: unknown): boolean {
  return error instanceof ApiClientError && error.code === "REQUEST_FAILED" && error.status >= 500;
}
