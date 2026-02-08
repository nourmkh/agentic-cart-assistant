import { apiGet } from "./client";

export interface PinterestStatus {
  connected: boolean;
  connected_at: string | null;
}

export interface PinterestLoginResponse {
  oauth_url: string;
  state: string;
}

export async function fetchPinterestStatus(): Promise<PinterestStatus> {
  return apiGet<PinterestStatus>("/api/pinterest/status");
}

export async function fetchPinterestLoginUrl(): Promise<PinterestLoginResponse> {
  return apiGet<PinterestLoginResponse>("/api/pinterest/login");
}

export async function completePinterestCallback(code: string, state?: string): Promise<{ success: boolean }> {
  const query = new URLSearchParams({ code, ...(state ? { state } : {}) });
  return apiGet<{ success: boolean }>(`/api/pinterest/callback?${query.toString()}`);
}
