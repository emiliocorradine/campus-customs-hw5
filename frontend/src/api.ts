import { API_BASE } from "./config";
import type {
  ApprovalsResponse,
  Cash,
  DecisionResult,
  EventsResponse,
  RunRecord,
  Ticket,
} from "./types";

/** Turn FastAPI error bodies ({detail: {...}} or {detail: [...]}) into one readable line. */
function errorText(status: number, body: unknown): string {
  const detail = (body as { detail?: unknown })?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d?.msg ?? String(d)).join("; ");
  if (detail && typeof detail === "object") {
    const d = detail as Record<string, unknown>;
    return String(d.detail ?? d.error ?? JSON.stringify(d));
  }
  return `HTTP ${status}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(errorText(res.status, body));
  return body as T;
}

export const api = {
  tickets: () => request<{ count: number; tickets: Ticket[] }>("/tickets"),
  runTicket: (id: number) =>
    request<{ ticket_id: number; run_id: string; status: string }>(`/tickets/${id}/run`, { method: "POST" }),
  run: (runId: string) => request<RunRecord>(`/runs/${runId}`),
  events: (since: number) => request<EventsResponse>(`/events?since=${since}`),
  approvals: () => request<ApprovalsResponse>("/approvals"),
  approve: (id: number, approvedBy: string) =>
    request<DecisionResult>(`/approvals/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ approved_by: approvedBy }),
    }),
  reject: (id: number, approvedBy: string) =>
    request<DecisionResult>(`/approvals/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ approved_by: approvedBy }),
    }),
  cash: () => request<Cash>("/cash"),
  reset: () => request<{ status: string; detail: string }>("/reset", { method: "POST" }),
};
