const API_BASE_URL = import.meta.env.VITE_API_URL ?? "/api/v1";
const TOKEN_STORAGE_KEY = "competitor-intelligence-token";

interface ErrorEnvelope {
  error?: { code?: string; message?: string };
  detail?: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | undefined;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export function getStoredToken(): string | null {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function storeToken(token: string): void {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken(): void {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

/** Send an authenticated JSON request to the API. */
export async function apiRequest<ResponseBody>(
  path: string,
  init: RequestInit = {},
): Promise<ResponseBody> {
  const headers = new Headers(init.headers);
  const token = getStoredToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    let envelope: ErrorEnvelope = {};
    try {
      envelope = (await response.json()) as ErrorEnvelope;
    } catch {
      // The status text remains the safe fallback for non-JSON proxy errors.
    }
    throw new ApiError(
      response.status,
      envelope.error?.message ?? envelope.detail ?? response.statusText,
      envelope.error?.code,
    );
  }
  if (response.status === 204) return undefined as ResponseBody;
  return (await response.json()) as ResponseBody;
}

