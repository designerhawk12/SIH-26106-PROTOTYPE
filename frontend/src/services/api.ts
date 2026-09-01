/**
 * Single API access layer for the platform.
 *
 * Every page/component reads data through these functions only. Today they
 * resolve mock data; to connect the FastAPI backend, flip `USE_MOCK` to false
 * (or unset it) and implement the fetch bodies already sketched below.
 *
 * Backend endpoints:
 *   POST /api/v1/cases/analyze
 *   GET  /api/v1/cases
 *   GET  /api/v1/cases/{case_id}
 *   GET  /api/v1/cases/{case_id}/report
 */
import type { CaseSummary, DashboardStats, EmailAnalysis } from "@/types/analysis";
import { sampleAnalysis, sampleCases, sampleStats } from "@/mocks/sampleAnalysis";

export const API_BASE_URL: string = import.meta.env["VITE_API_BASE_URL"] ?? "";

/** While true the UI is served from `src/mocks`. */
export const USE_MOCK = true;

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`API request failed (${response.status}): ${path}`);
  }
  return (await response.json()) as T;
}

export function getMockAnalysis(): EmailAnalysis {
  return sampleAnalysis;
}

/** POST /api/v1/cases/analyze */
export async function analyzeEmail(file: File): Promise<EmailAnalysis> {
  if (USE_MOCK) {
    await delay(400);
    return getMockAnalysis();
  }
  const body = new FormData();
  body.append("file", file);
  return request<EmailAnalysis>("/api/v1/cases/analyze", { method: "POST", body });
}

/** GET /api/v1/cases */
export async function listCases(): Promise<CaseSummary[]> {
  if (USE_MOCK) {
    await delay(200);
    return sampleCases;
  }
  return request<CaseSummary[]>("/api/v1/cases");
}

/** GET /api/v1/cases/{case_id} */
export async function getCase(caseId: string): Promise<EmailAnalysis> {
  if (USE_MOCK) {
    await delay(200);
    return { ...getMockAnalysis(), case_id: caseId };
  }
  return request<EmailAnalysis>(`/api/v1/cases/${caseId}`);
}

/** GET /api/v1/cases/{case_id}/report */
export async function getCaseReport(caseId: string): Promise<{ url: string }> {
  if (USE_MOCK) {
    await delay(200);
    return { url: `#report-${caseId}` };
  }
  return request<{ url: string }>(`/api/v1/cases/${caseId}/report`);
}

/** Dashboard aggregates. Backend endpoint TBD — mock only for now. */
export async function getDashboardStats(): Promise<DashboardStats> {
  await delay(120);
  return sampleStats;
}
