export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export const UPLOAD_BASE_URL = import.meta.env.VITE_UPLOAD_BASE_URL ?? "";

export function resolveUploadUrl(path: string): string {
  if (path.startsWith("http")) return path;
  return `${UPLOAD_BASE_URL}${path}`;
}
