import type { ChatResponse, SessionResponse } from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    }
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function createSession(): Promise<SessionResponse> {
  return request<SessionResponse>("/api/sessions", { method: "POST" });
}

export function sendMessage(sessionId: string, message: string): Promise<ChatResponse> {
  return request<ChatResponse>(`/api/sessions/${sessionId}/chat`, {
    method: "POST",
    body: JSON.stringify({ message })
  });
}

export function approveGate(sessionId: string, gate: string): Promise<SessionResponse> {
  return request<SessionResponse>(`/api/sessions/${sessionId}/approve`, {
    method: "POST",
    body: JSON.stringify({ gate })
  });
}

export function exportUrl(sessionId: string, file: "itinerary.md" | "calendar.ics" | "trace.json") {
  return `${API_BASE_URL}/api/sessions/${sessionId}/exports/${file}`;
}

