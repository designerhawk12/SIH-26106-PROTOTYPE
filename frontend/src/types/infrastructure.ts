import type {
  AnalysisStatus,
  EnrichmentStatus,
  GeoLocationResult,
  ReputationVerdict,
  RiskLevel,
} from "./analysis";

export interface InfrastructureCase {
  case_id: string;
  subject: string | null;
  status: AnalysisStatus;
  risk_severity: RiskLevel | null;
}

export interface InfrastructureObservation {
  id: string;
  ip_address: string;
  case: InfrastructureCase;
  observed_at: string;
  location: GeoLocationResult | null;
  verdict: ReputationVerdict;
  threat_intel_status: EnrichmentStatus;
  threat_providers: string[];
  demo: boolean;
}

export interface InfrastructureRouteSegment {
  case_id: string;
  from_observation_id: string;
  to_observation_id: string;
  from_timestamp: string;
  to_timestamp: string;
}

export interface InfrastructureWorkspace {
  observations: InfrastructureObservation[];
  route_segments: InfrastructureRouteSegment[];
  cases_scanned: number;
  disclaimer: string;
}
