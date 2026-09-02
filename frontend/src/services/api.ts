/** Central API access and contract-to-presentation mapping. */
import { sampleAnalysis, sampleCases, sampleStats } from "@/mocks/sampleAnalysis";
import type {
  AnalysisViewModel,
  AnalyzeCaseResponse,
  AttachmentEvidence,
  AuthenticationVerdict,
  CaseListResponse,
  CaseSummary,
  DashboardStats,
  EmailAnalysis,
  ErrorResponse,
  ExtractedIOC,
  HealthResponse,
  MimeNode,
  Reputation,
  ReputationVerdict,
} from "@/types/analysis";

export const API_BASE_URL: string = (import.meta.env["VITE_API_BASE_URL"] ?? "").replace(
  /\/+$/,
  "",
);
export const USE_MOCK = import.meta.env["VITE_USE_MOCK_API"] === "true";

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code = "API_ERROR",
    readonly field: string | null = null,
    readonly requestId: string | null = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function errorFromResponse(response: Response): Promise<ApiError> {
  try {
    const payload = (await response.json()) as Partial<ErrorResponse>;
    if (payload.error?.message) {
      return new ApiError(
        payload.error.message,
        response.status,
        payload.error.code,
        payload.error.field ?? null,
        payload.request_id ?? null,
      );
    }
  } catch {
    // Non-JSON failures are normalized below without exposing response contents.
  }
  return new ApiError(
    `The server could not complete the request (${response.status}).`,
    response.status,
  );
}

async function request(path: string, init?: RequestInit, timeoutMs = 15_000): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: init?.signal ?? controller.signal,
      headers: { Accept: "application/json", ...(init?.headers ?? {}) },
    });
    if (!response.ok) throw await errorFromResponse(response);
    return response;
  } catch (error) {
    if (controller.signal.aborted) {
      throw new ApiError("The analysis service did not respond in time.", 0, "NETWORK_TIMEOUT");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

async function requestJson<T>(path: string, init?: RequestInit, timeoutMs?: number): Promise<T> {
  const response = await request(path, init, timeoutMs);
  return (await response.json()) as T;
}

export function getErrorMessage(error: unknown, fallback = "The request could not be completed.") {
  if (error instanceof ApiError) {
    return error.field ? `${error.message} (${error.field})` : error.message;
  }
  if (error instanceof TypeError) return "Unable to reach the analysis service.";
  return error instanceof Error && error.message ? error.message : fallback;
}

function authResult(value: AuthenticationVerdict) {
  return value === "PASS" || value === "FAIL" ? value : "UNKNOWN";
}

function reputation(value?: ReputationVerdict): Reputation {
  if (value === "MALICIOUS") return "malicious";
  if (value === "SUSPICIOUS") return "suspicious";
  if (value === "BENIGN") return "clean";
  return "unknown";
}

function threatVerdict(analysis: EmailAnalysis, type: ExtractedIOC["type"], value: string) {
  return analysis.threat_intel?.findings.find(
    (finding) => finding.indicator_type === type && finding.indicator === value,
  );
}

function domainFromUrl(value: string) {
  try {
    return new URL(value).hostname.toLowerCase();
  } catch {
    return "unknown";
  }
}

function buildMimeTree(
  parts: EmailAnalysis["parsed_email"] extends infer _
    ? NonNullable<EmailAnalysis["parsed_email"]>["mime_parts"]
    : never,
): MimeNode {
  const byId = new Map<string, MimeNode>();
  for (const part of parts) {
    byId.set(part.part_id, {
      content_type: part.content_type,
      size_bytes: part.decoded_size_bytes ?? 0,
      filename: part.filename,
      children: [],
    });
  }
  for (const part of parts) {
    if (part.parent_part_id) byId.get(part.parent_part_id)?.children?.push(byId.get(part.part_id)!);
  }
  const rootPart = parts.find((part) => part.parent_part_id === null);
  return (
    (rootPart && byId.get(rootPart.part_id)) ?? { content_type: "message/rfc822", size_bytes: 0 }
  );
}

function attachmentStatus(analysis: EmailAnalysis, attachment: AttachmentEvidence) {
  return reputation(threatVerdict(analysis, "ATTACHMENT_SHA256", attachment.sha256)?.verdict);
}

export function toAnalysisView(analysis: EmailAnalysis): AnalysisViewModel {
  const parsed = analysis.parsed_email;
  const authentication = parsed?.authentication;
  const iocs = parsed?.iocs ?? [];
  const lookup = (type: ExtractedIOC["type"]) => iocs.filter((ioc) => ioc.type === type);
  const findings = analysis.detection?.findings ?? [];
  const returnPath = parsed?.headers["return-path"]?.[0] ?? null;
  const classifications = Array.from(
    new Set(findings.map((finding) => finding.category.replaceAll("_", " "))),
  );

  return {
    case_id: analysis.case_id,
    created_at: analysis.created_at,
    status: analysis.status,
    email: {
      subject: parsed?.subject ?? "Subject unavailable",
      sender: parsed?.sender?.address ?? "Unknown sender",
      sender_display_name: parsed?.sender?.display_name ?? "Unknown sender",
      receiver: parsed?.to.map((mailbox) => mailbox.address).join(", ") || "Unknown recipient",
      date: parsed?.sent_at ?? analysis.created_at,
      message_id: parsed?.message_id ?? "Unavailable",
      reply_to: parsed?.reply_to.map((mailbox) => mailbox.address).join(", ") || null,
      return_path: returnPath,
    },
    risk: analysis.risk
      ? {
          score: analysis.risk.score,
          level: analysis.risk.severity,
          indicator_count: analysis.risk.reasons.length,
          classification: classifications,
          summary:
            analysis.detection?.summary ??
            "Risk values and reasons were returned by the deterministic backend risk engine.",
          signals: analysis.risk.reasons,
        }
      : null,
    authentication: {
      spf: {
        result: authResult(authentication?.spf ?? "UNKNOWN"),
        domain: authentication?.spf_domain ?? null,
        explanation: `Declared SPF result: ${authentication?.spf ?? "UNKNOWN"}.`,
      },
      dkim: {
        result: authResult(authentication?.dkim ?? "UNKNOWN"),
        domain: authentication?.dkim_domains[0] ?? null,
        explanation: `Declared DKIM result: ${authentication?.dkim ?? "UNKNOWN"}.`,
      },
      dmarc: {
        result: authResult(authentication?.dmarc ?? "UNKNOWN"),
        domain: authentication?.spf_domain ?? null,
        explanation: `Declared DMARC result: ${authentication?.dmarc ?? "UNKNOWN"}.`,
      },
    },
    mime: buildMimeTree(parsed?.mime_parts ?? []),
    received_chain: (parsed?.received_hops ?? []).map((hop) => ({
      index: hop.position,
      from_host: hop.from_host ?? "Unknown host",
      by_host: hop.by_host ?? "Unknown host",
      protocol: hop.protocol,
      timestamp: hop.timestamp ?? analysis.created_at,
      ip: hop.source_ip,
    })),
    indicators: {
      ips: lookup("IP_ADDRESS").map((ioc) => ({
        ip: ioc.normalized_value,
        reputation: reputation(
          threatVerdict(analysis, "IP_ADDRESS", ioc.normalized_value)?.verdict,
        ),
        source: ioc.source,
      })),
      domains: lookup("DOMAIN").map((ioc) => ({
        domain: ioc.normalized_value,
        reputation: reputation(threatVerdict(analysis, "DOMAIN", ioc.normalized_value)?.verdict),
        type: ioc.source,
      })),
      urls: lookup("URL").map((ioc) => ({
        url: ioc.normalized_value,
        domain: domainFromUrl(ioc.normalized_value),
        reputation: reputation(threatVerdict(analysis, "URL", ioc.normalized_value)?.verdict),
      })),
      attachments: (parsed?.attachments ?? []).map((attachment) => ({
        filename: attachment.filename ?? "Unnamed attachment",
        mime_type: attachment.content_type,
        size_bytes: attachment.size_bytes,
        sha256: attachment.sha256,
        status: attachmentStatus(analysis, attachment),
      })),
    },
    infrastructure: {
      disclaimer:
        "Infrastructure geolocation describes observed network/mail-routing infrastructure and does not establish the physical location or identity of the attacker.",
      nodes: analysis.geolocations.map((location, index) => ({
        index,
        role: index === 0 ? "Observed routing infrastructure" : "Mail routing infrastructure",
        ip: location.ip_address,
        country: location.country,
        region: location.region,
        city: location.city,
        isp: location.isp ?? location.organization,
        asn: location.asn ?? location.network,
        reputation: reputation(threatVerdict(analysis, "IP_ADDRESS", location.ip_address)?.verdict),
      })),
    },
    ai_findings: findings.map((finding) => ({
      type: finding.category.toLowerCase() as Lowercase<typeof finding.category>,
      title: finding.title,
      detected: true,
      confidence: finding.confidence,
      evidence: finding.evidence,
      explanation: finding.explanation,
    })),
    timeline: analysis.timeline.map((event) => ({
      timestamp: event.timestamp ?? analysis.created_at,
      label: event.title,
      ...(event.description ? { detail: event.description } : {}),
    })),
    evidence: {
      email_sha256: parsed?.original_sha256 ?? "Unavailable",
      attachment_hashes: (parsed?.attachments ?? []).map((attachment) => ({
        filename: attachment.filename ?? "Unnamed attachment",
        sha256: attachment.sha256,
      })),
      analyzed_at: analysis.completed_at ?? analysis.created_at,
      case_id: analysis.case_id,
      events: analysis.timeline.map((event) => ({
        timestamp: event.timestamp ?? analysis.created_at,
        label: event.title,
        ...(event.description ? { detail: event.description } : {}),
      })),
    },
  };
}

export function getMockAnalysis(): AnalysisViewModel {
  return toAnalysisView(sampleAnalysis);
}

export async function analyzeEmail(file: File): Promise<AnalysisViewModel> {
  if (USE_MOCK) {
    await delay(400);
    return getMockAnalysis();
  }
  const body = new FormData();
  body.append("file", file);
  const response = await requestJson<AnalyzeCaseResponse>(
    "/api/v1/cases/analyze",
    {
      method: "POST",
      body,
    },
    120_000,
  );
  return toAnalysisView(response.analysis);
}

export async function listCases(): Promise<CaseSummary[]> {
  if (USE_MOCK) {
    await delay(200);
    return sampleCases;
  }
  return (await requestJson<CaseListResponse>("/api/v1/cases")).items;
}

export async function getCase(caseId: string): Promise<AnalysisViewModel> {
  if (USE_MOCK) {
    await delay(200);
    return toAnalysisView({ ...sampleAnalysis, case_id: caseId });
  }
  return toAnalysisView(await requestJson<EmailAnalysis>(`/api/v1/cases/${caseId}`));
}

export async function getCaseReport(caseId: string): Promise<Blob> {
  if (USE_MOCK) {
    await delay(200);
    return new Blob([], { type: "application/pdf" });
  }
  const response = await request(`/api/v1/cases/${caseId}/report`, {
    headers: { Accept: "application/pdf" },
  });
  return response.blob();
}

export async function downloadCaseReport(caseId: string): Promise<void> {
  const report = await getCaseReport(caseId);
  const objectUrl = URL.createObjectURL(report);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = `case-${caseId}.pdf`;
  anchor.style.display = "none";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}

export async function getCaseEvidence(caseId: string): Promise<Blob> {
  if (USE_MOCK) {
    await delay(200);
    return new Blob([], { type: "application/zip" });
  }
  const response = await request(`/api/v1/cases/${caseId}/evidence`, {
    headers: { Accept: "application/zip" },
  });
  return response.blob();
}

export async function downloadCaseEvidence(caseId: string): Promise<void> {
  const zip = await getCaseEvidence(caseId);
  const objectUrl = URL.createObjectURL(zip);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = `sentinel-mx-case-${caseId}-evidence.zip`;
  anchor.style.display = "none";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}

export async function getHealth(): Promise<HealthResponse> {
  if (USE_MOCK) {
    await delay(120);
    return {
      status: "ok",
      service: "email-threat-platform",
      version: "mock",
      timestamp: new Date().toISOString(),
    };
  }
  return requestJson<HealthResponse>("/api/v1/health", undefined, 5_000);
}

export async function getDashboardStats(): Promise<DashboardStats> {
  await delay(120);
  return sampleStats;
}
