const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function apiGet<T>(path: string): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "GET",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      throw new Error(`API error: ${res.status} ${res.statusText} - ${API_BASE}${path}`);
    }
    return res.json() as Promise<T>;
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      // Network error - likely backend not running
      throw new Error(`Cannot connect to backend at ${API_BASE}. Make sure the server is running.`);
    }
    throw error;
  }
}

export async function apiPost<T>(path: string, data: any): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        Accept: "application/json" 
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      throw new Error(`API error: ${res.status} ${res.statusText} - ${API_BASE}${path}`);
    }
    return res.json() as Promise<T>;
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error(`Cannot connect to backend at ${API_BASE}. Make sure the server is running.`);
    }
    throw error;
  }
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}
