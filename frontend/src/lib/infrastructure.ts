import type { InfrastructureObservation } from "../types/infrastructure";
import type { ReputationVerdict } from "../types/analysis";

export interface VerdictVisual {
  color: string;
  glow: string;
}

export const verdictVisuals: Record<ReputationVerdict, VerdictVisual> = {
  MALICIOUS: { color: "#ff4057", glow: "rgba(255, 64, 87, 0.72)" },
  SUSPICIOUS: { color: "#ffad22", glow: "rgba(255, 173, 34, 0.58)" },
  BENIGN: { color: "#25d997", glow: "rgba(37, 217, 151, 0.45)" },
  UNKNOWN: { color: "#8da9b8", glow: "rgba(111, 187, 205, 0.3)" },
};

export const verdictColors = Object.fromEntries(
  Object.entries(verdictVisuals).map(([verdict, visual]) => [verdict, visual.color]),
) as Record<ReputationVerdict, string>;

export function coordinates(record: InfrastructureObservation): [number, number] | null {
  const location = record.location;
  if (!location || location.status !== "FOUND") return null;
  const { latitude: lat, longitude: lon } = location;
  if (
    typeof lat !== "number" ||
    typeof lon !== "number" ||
    !Number.isFinite(lat) ||
    !Number.isFinite(lon) ||
    lat < -90 ||
    lat > 90 ||
    lon < -180 ||
    lon > 180 ||
    (lat === 0 && lon === 0)
  )
    return null;
  return [lat, lon];
}

export interface InfrastructureFilters {
  search: string;
  caseId: string;
  severity: string;
  verdict: string;
  country: string;
  availability: string;
}

export const emptyInfrastructureFilters: InfrastructureFilters = {
  search: "",
  caseId: "ALL",
  severity: "ALL",
  verdict: "ALL",
  country: "ALL",
  availability: "ALL",
};

export function filterInfrastructure(
  records: InfrastructureObservation[],
  filters: InfrastructureFilters,
): InfrastructureObservation[] {
  const search = filters.search.trim().toLowerCase();
  return records.filter((record) => {
    const available = coordinates(record) !== null;
    const fields = [
      record.ip_address,
      record.case.subject,
      record.case.case_id,
      record.location?.city,
      record.location?.country,
      record.location?.isp,
      record.location?.organization,
      record.location?.asn,
      record.location?.provider,
    ];
    return (
      (!search || fields.some((value) => value?.toLowerCase().includes(search))) &&
      (filters.caseId === "ALL" || record.case.case_id === filters.caseId) &&
      (filters.severity === "ALL" ||
        (record.case.risk_severity ?? "UNKNOWN") === filters.severity) &&
      (filters.verdict === "ALL" || record.verdict === filters.verdict) &&
      (filters.country === "ALL" || (record.location?.country ?? "UNKNOWN") === filters.country) &&
      (filters.availability === "ALL" ||
        (filters.availability === "MAPPED" && available) ||
        (filters.availability === "MISSING" && !available) ||
        (filters.availability === "UNAVAILABLE" && record.location?.status === "PROVIDER_ERROR"))
    );
  });
}
