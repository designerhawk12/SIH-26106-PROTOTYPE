/** Exact TypeScript mirror of the shared backend analysis contracts. */
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type Severity = "INFO" | RiskLevel;
export type AnalysisStatus = "RECEIVED" | "PROCESSING" | "COMPLETED" | "PARTIAL" | "FAILED";
export type AuthenticationVerdict =
  "PASS" | "FAIL" | "SOFTFAIL" | "NEUTRAL" | "TEMPERROR" | "PERMERROR" | "NONE" | "UNKNOWN";
export type IOCType = "IP_ADDRESS" | "URL" | "DOMAIN" | "EMAIL_ADDRESS" | "ATTACHMENT_SHA256";
export type IOCSource =
  "HEADER" | "BODY_TEXT" | "BODY_HTML" | "RECEIVED_HEADER" | "ATTACHMENT_METADATA";
export type DetectionCategory =
  | "PHISHING"
  | "SOCIAL_ENGINEERING"
  | "URGENCY"
  | "CREDENTIAL_REQUEST"
  | "PAYMENT_REQUEST"
  | "IMPERSONATION"
  | "BUSINESS_EMAIL_COMPROMISE"
  | "SUSPICIOUS_CALL_TO_ACTION";
export type ReputationVerdict = "MALICIOUS" | "SUSPICIOUS" | "BENIGN" | "UNKNOWN";
export type EnrichmentStatus = "COMPLETE" | "PARTIAL" | "UNAVAILABLE" | "UNKNOWN";
export type GeoLocationStatus = "FOUND" | "NOT_FOUND" | "NOT_PUBLIC" | "PROVIDER_ERROR" | "UNKNOWN";
export type TimelineEventType =
  | "MESSAGE_DATE"
  | "RECEIVED_HOP"
  | "ANALYSIS_STARTED"
  | "ANALYSIS_COMPLETED"
  | "ENRICHMENT"
  | "FINDING";

export interface MailboxAddress {
  display_name: string | null;
  address: string;
}
export interface AuthenticationResults {
  spf: AuthenticationVerdict;
  dkim: AuthenticationVerdict;
  dmarc: AuthenticationVerdict;
  spf_domain: string | null;
  dkim_domains: string[];
  dmarc_policy: string | null;
  source_headers: string[];
}
export interface ContractReceivedHop {
  position: number;
  raw_header: string;
  from_host: string | null;
  by_host: string | null;
  protocol: string | null;
  message_id: string | null;
  envelope_for: string | null;
  timestamp: string | null;
  source_ip: string | null;
  is_public_ip: boolean;
}
export interface ExtractedIOC {
  type: IOCType;
  value: string;
  normalized_value: string;
  source: IOCSource;
  occurrences: number;
}
export interface MimePart {
  part_id: string;
  parent_part_id: string | null;
  content_type: string;
  content_disposition: string | null;
  transfer_encoding: string | null;
  decoded_size_bytes: number | null;
  filename: string | null;
}
export interface AttachmentEvidence {
  attachment_id: string;
  filename: string | null;
  content_type: string;
  content_disposition: string | null;
  content_id: string | null;
  size_bytes: number;
  sha256: string;
  extracted_iocs: ExtractedIOC[];
  executed: false;
}
export interface ParsedEmail {
  original_sha256: string;
  message_id: string | null;
  sent_at: string | null;
  sender: MailboxAddress | null;
  reply_to: MailboxAddress[];
  to: MailboxAddress[];
  cc: MailboxAddress[];
  bcc: MailboxAddress[];
  subject: string | null;
  text_body: string | null;
  /** Hostile evidence. The frontend must never render this as HTML. */
  html_body_untrusted: string | null;
  headers: Record<string, string[]>;
  mime_parts: MimePart[];
  received_hops: ContractReceivedHop[];
  originating_public_ips: string[];
  authentication: AuthenticationResults;
  iocs: ExtractedIOC[];
  attachments: AttachmentEvidence[];
  parse_warnings: string[];
}
export interface DetectionFinding {
  finding_id: string;
  category: DetectionCategory;
  severity: Severity;
  confidence: number;
  title: string;
  explanation: string;
  evidence: string[];
  detector: string;
}
export interface DetectionResult {
  findings: DetectionFinding[];
  model_name: string | null;
  model_version: string | null;
  summary: string | null;
  warnings: string[];
}
export interface ThreatFinding {
  indicator_type: IOCType;
  indicator: string;
  provider: string;
  verdict: ReputationVerdict;
  confidence: number | null;
  categories: string[];
  first_seen: string | null;
  last_seen: string | null;
  reference: string | null;
  details: string | null;
}
export interface ThreatIntelResult {
  status: EnrichmentStatus;
  requested_indicators: ExtractedIOC[];
  findings: ThreatFinding[];
  unknown_indicators: ExtractedIOC[];
  provider_errors: string[];
}
export interface GeoLocationResult {
  ip_address: string;
  status: GeoLocationStatus;
  country: string | null;
  country_code: string | null;
  city: string | null;
  region: string | null;
  isp: string | null;
  asn: string | null;
  organization: string | null;
  network: string | null;
  latitude: number | null;
  longitude: number | null;
  provider: string | null;
  observed_infrastructure_only: true;
}
export interface RiskReason {
  code: string;
  description: string;
  points: number;
  evidence_refs: string[];
}
export type RiskSignal = RiskReason;
export interface RiskResult {
  score: number;
  severity: RiskLevel;
  reasons: RiskReason[];
  formula_version: string;
  unknown_inputs: string[];
}
export interface ContractTimelineEvent {
  sequence: number;
  event_type: TimelineEventType;
  timestamp: string | null;
  title: string;
  description: string | null;
  source: string;
  evidence_refs: string[];
}
export interface EmailAnalysis {
  schema_version: "1.0.0";
  case_id: string;
  status: AnalysisStatus;
  original_filename: string | null;
  created_at: string;
  completed_at: string | null;
  parsed_email: ParsedEmail | null;
  detection: DetectionResult | null;
  threat_intel: ThreatIntelResult | null;
  geolocations: GeoLocationResult[];
  risk: RiskResult | null;
  timeline: ContractTimelineEvent[];
  warnings: string[];
  errors: string[];
}
export interface CaseSummary {
  case_id: string;
  status: AnalysisStatus;
  original_filename: string | null;
  created_at: string;
  completed_at: string | null;
  risk_score: number | null;
  risk_severity: RiskLevel | null;
  subject: string | null;
}
export interface CaseListResponse {
  items: CaseSummary[];
  total: number;
  limit: number;
  offset: number;
}
export interface AnalyzeCaseResponse {
  analysis: EmailAnalysis;
}

/* Presentation-only types below are derived centrally in services/api.ts. */
export type AuthResult = "PASS" | "FAIL" | "UNKNOWN";
export type Reputation = "malicious" | "suspicious" | "neutral" | "clean" | "unknown";
export type FindingType = Lowercase<DetectionCategory>;
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
  status: Reputation;
}
export interface Indicators {
  ips: IpIndicator[];
  domains: DomainIndicator[];
  urls: UrlIndicator[];
  attachments: AttachmentIndicator[];
}
export interface InfrastructureNode {
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
  signals: RiskReason[];
}
export interface AnalysisViewModel {
  case_id: string;
  created_at: string;
  status: AnalysisStatus;
  email: EmailHeaders;
  risk: RiskAssessment | null;
  authentication: AuthenticationSummary;
  mime: MimeNode;
  received_chain: ReceivedHop[];
  indicators: Indicators;
  infrastructure: InfrastructureSummary;
  ai_findings: AiFinding[];
  timeline: TimelineEvent[];
  evidence: Evidence;
}

/** Mock-only counters; there is no backend aggregate endpoint yet. */
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
