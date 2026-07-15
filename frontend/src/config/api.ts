function getDefaultApiBaseUrl(): string {
  if (import.meta.env.DEV) {
    return "http://127.0.0.1:8000";
  }

  if (typeof window !== "undefined" && window.location.origin) {
    return window.location.origin;
  }

  return "http://127.0.0.1:8000";
}

function normalizeHttpBaseUrl(value: string | undefined): string {
  return (value || getDefaultApiBaseUrl()).replace(/\/+$/, "");
}

function buildWebSocketBaseUrl(apiBaseUrl: string): string {
  return apiBaseUrl.replace(/^http/, "ws");
}

export const API_BASE_URL = normalizeHttpBaseUrl(import.meta.env.VITE_API_BASE_URL);
export const WS_BASE_URL = buildWebSocketBaseUrl(API_BASE_URL);
