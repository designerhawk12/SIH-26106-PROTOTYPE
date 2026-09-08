/** Exact wire contracts for persisted, deterministic cross-case correlation. */

import type { RiskLevel } from "@/types/analysis";

export type CorrelationIndicatorType =
  | "SENDER_EMAIL"
  | "SENDER_DOMAIN"
  | "REPLY_TO"
  | "REPLY_TO_DOMAIN"
  | "IP_ADDRESS"
  | "DOMAIN"
  | "URL"
  | "ATTACHMENT_SHA256"
  | "ASN"
  | "NORMALIZED_SUBJECT";

export type CorrelationStrength = "LOW" | "MEDIUM" | "HIGH";

export interface SharedIndicator {
  indicator_type: CorrelationIndicatorType;
  value: string;
  reason: string;
}

export interface RelatedCase {
  case_id: string;
  subject: string | null;
  risk_score: number | null;
  risk_severity: RiskLevel | null;
  shared_indicators: SharedIndicator[];
  shared_indicator_count: number;
  correlation_strength: CorrelationStrength;
  relationship_reasons: string[];
}

export interface RelatedCasesResponse {
  case_id: string;
  items: RelatedCase[];
  total: number;
  limit: number;
  offset: number;
  disclaimer: string;
}
