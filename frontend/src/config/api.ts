const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

function normalizeHttpBaseUrl(value: string | undefined): string {
  return (value || DEFAULT_API_BASE_URL).replace(/\/+$/, "");
}

function buildWebSocketBaseUrl(apiBaseUrl: string): string {
  if (import.meta.env.VITE_WS_BASE_URL) {
    return import.meta.env.VITE_WS_BASE_URL.replace(/\/+$/, "");
  }

  return apiBaseUrl.replace(/^http/, "ws");
}

export const API_BASE_URL = normalizeHttpBaseUrl(import.meta.env.VITE_API_BASE_URL);
export const WS_BASE_URL = buildWebSocketBaseUrl(API_BASE_URL);
