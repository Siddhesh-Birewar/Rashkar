/**
 * Minimal API client groundwork for the CropNet web frontend.
 * Product screens will be built in v0; this file only wires the base URL,
 * Bearer-token injection and typed error mapping.
 */
const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  readonly status: number;
  readonly detail?: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export interface ApiRequestOptions extends RequestInit {
  /** Supabase access token; sent as `Authorization: Bearer <token>`. */
  token?: string | null;
}

export async function apiFetch<T>(
  path: string,
  { token, headers, ...rest }: ApiRequestOptions = {},
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...rest,
    headers: {
      Accept: "application/json",
      ...(rest.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    cache: "no-store",
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const message =
      data && typeof data.detail === "string"
        ? data.detail
        : `HTTP ${response.status}`;
    throw new ApiError(response.status, message, data);
  }

  return data as T;
}
