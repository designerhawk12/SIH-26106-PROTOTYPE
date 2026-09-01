/**
 * Frontend data contract for the FastAPI backend.
 *
 * These types mirror the shape of `sample_analysis.json`. Keep every type in
 * this file so the contract can be updated in one place when the backend
 * evolves. Nothing here performs logic — types only.
 */

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type AuthResult = "PASS" | "FAIL" | "UNKNOWN";

export type Reputation = "malicious" | "suspicious" | "neutral" | "clean" | "unknown";

export type CaseStatus = "open" | "in_review" | "closed";

export interface RiskSignal {
  /** Human readable reason, e.g. "SPF authentication failed" */
  label: string;
  /** Points contributed to the total risk score */
  weight: number;
  /** Longer explanation revealed on hover */
  detail: string;
  category: "authentication" | "content" | "infrastructure" | "identity" | "attachment";
}

export interface EmailHeaders {
  subject: string;
  sender: string;
  sender_display_name: string;
  receiver: string;
  date: string;
  message_id: string;
  reply_to: string | null;
  return_path: string | null;
}

export interface AuthenticationCheck {
  result: AuthResult;
  domain: string | null;
  explanation: string;
}

export interface AuthenticationSummary {
  spf: AuthenticationCheck;
  dkim: AuthenticationCheck;
  dmarc: AuthenticationCheck;
}

export interface MimeNode {
  content_type: string;
  size_bytes: number;
  filename?: string | null;
  children?: MimeNode[];
}

export interface ReceivedHop {
  index: number;
  from_host: string;
  by_host: string;
  protocol: string | null;
  timestamp: string;
  ip: string | null;
}

export interface IpIndicator {
  ip: string;
  reputation: Reputation;
  source: string;
}

export interface DomainIndicator {
  domain: string;
  reputation: Reputation;
  type: string;
}

export interface UrlIndicator {
  url: string;
  domain: string;
  reputation: Reputation;
}

export interface AttachmentIndicator {
  filename: string;
  mime_type: string;
  size_bytes: number;
  sha256: string;
  status: "clean" | "suspicious" | "malicious" | "unknown";
}

export interface Indicators {
  ips: IpIndicator[];
  domains: DomainIndicator[];
  urls: UrlIndicator[];
  attachments: AttachmentIndicator[];
}

export interface InfrastructureNode {
  /** Position in the observed routing path (0 = origin) */
  index: number;
  role: string;
  ip: string;
  country: string | null;
  region: string | null;
  city: string | null;
  isp: string | null;
  asn: string | null;
  reputation: Reputation;
}

export interface InfrastructureSummary {
  disclaimer: string;
  nodes: InfrastructureNode[];
}

export type FindingType =
  | "phishing"
  | "social_engineering"
  | "urgency"
  | "credential_request"
  | "payment_request"
  | "impersonation"
  | "business_email_compromise"
  | "suspicious_call_to_action";

export interface AiFinding {
  type: FindingType;
  title: string;
  detected: boolean;
  confidence: number;
  evidence: string[];
  explanation: string;
}

export interface TimelineEvent {
  timestamp: string;
  label: string;
  detail?: string;
}

export interface EvidenceHashEntry {
  filename: string;
  sha256: string;
}

export interface Evidence {
  email_sha256: string;
  attachment_hashes: EvidenceHashEntry[];
  analyzed_at: string;
  case_id: string;
  events: TimelineEvent[];
}

export interface RiskAssessment {
  score: number;
  level: RiskLevel;
  indicator_count: number;
  classification: string[];
  summary: string;
  signals: RiskSignal[];
}

export interface EmailAnalysis {
  case_id: string;
  created_at: string;
  status: CaseStatus;
  email: EmailHeaders;
  risk: RiskAssessment;
  authentication: AuthenticationSummary;
  mime: MimeNode;
  received_chain: ReceivedHop[];
  indicators: Indicators;
  infrastructure: InfrastructureSummary;
  ai_findings: AiFinding[];
  timeline: TimelineEvent[];
  evidence: Evidence;
}

/** Row shape returned by GET /api/v1/cases */
export interface CaseSummary {
  case_id: string;
  subject: string;
  sender: string;
  risk_score: number;
  risk_level: RiskLevel;
  classification: string[];
  created_at: string;
  status: CaseStatus;
}

/** Aggregate counters rendered on the dashboard. */
export interface DashboardStats {
  emails_analyzed: number;
  threats_detected: number;
  high_risk: number;
  phishing: number;
  business_email_compromise: number;
  suspicious_attachments: number;
  authentication_failures: { spf: number; dkim: number; dmarc: number };
  classification_breakdown: { label: string; count: number }[];
}
