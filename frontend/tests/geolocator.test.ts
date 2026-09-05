import assert from "node:assert/strict";
import test from "node:test";
import {
  coordinates,
  emptyInfrastructureFilters,
  filterInfrastructure,
  verdictColors,
  verdictVisuals,
} from "../src/lib/infrastructure.ts";
import type { InfrastructureObservation } from "../src/types/infrastructure.ts";

const record: InfrastructureObservation = {
  id: "case-1:8.8.8.8:0",
  ip_address: "8.8.8.8",
  observed_at: "2026-09-05T00:00:00Z",
  case: { case_id: "case-1", subject: "Synthetic email", status: "PARTIAL", risk_severity: "LOW" },
  location: {
    ip_address: "8.8.8.8",
    status: "FOUND",
    latitude: 37.4,
    longitude: -122.1,
    country: "United States",
    country_code: "US",
    region: null,
    city: "Mountain View",
    isp: null,
    asn: null,
    organization: null,
    network: null,
    provider: "ipwho.is",
    observed_infrastructure_only: true,
  },
  verdict: "UNKNOWN",
  threat_intel_status: "UNAVAILABLE",
  threat_providers: [],
  demo: false,
};

test("only usable persisted coordinates generate markers; no zero fallback", () => {
  assert.deepEqual(coordinates(record), [37.4, -122.1]);
  assert.equal(coordinates({ ...record, location: null }), null);
  for (const patch of [
    { latitude: null },
    { longitude: null },
    { latitude: 0, longitude: 0 },
    { latitude: NaN },
    { longitude: Infinity },
    { latitude: 91 },
    { longitude: -181 },
    { status: "PROVIDER_ERROR" as const },
  ]) {
    assert.equal(coordinates({ ...record, location: { ...record.location!, ...patch } }), null);
  }
  assert.deepEqual(
    coordinates({ ...record, location: { ...record.location!, latitude: 0 } }),
    [0, -122.1],
  );
});

test("filters operate on persisted data, retain partial/unknown and support zero results", () => {
  const second = {
    ...record,
    id: "case-2:1.1.1.1:0",
    ip_address: "1.1.1.1",
    location: null,
    case: { ...record.case, case_id: "case-2", risk_severity: "HIGH" as const },
    verdict: "MALICIOUS" as const,
  };
  const records = [record, second];
  assert.equal(filterInfrastructure(records, emptyInfrastructureFilters).length, 2);
  for (const patch of [
    { caseId: "case-1" },
    { severity: "LOW" },
    { verdict: "UNKNOWN" },
    { country: "United States" },
    { availability: "MAPPED" },
    { search: "mountain" },
  ]) {
    assert.deepEqual(filterInfrastructure(records, { ...emptyInfrastructureFilters, ...patch }), [
      record,
    ]);
  }
  assert.deepEqual(
    filterInfrastructure(records, { ...emptyInfrastructureFilters, availability: "MISSING" }),
    [second],
  );
  assert.deepEqual(
    filterInfrastructure(records, { ...emptyInfrastructureFilters, search: "absent" }),
    [],
  );
  assert.deepEqual(filterInfrastructure([], emptyInfrastructureFilters), []);
  assert.equal(record.verdict, "UNKNOWN");
  assert.equal(record.case.status, "PARTIAL");
});

test("unknown remains visually distinct from benign", () => {
  assert.notEqual(verdictColors.UNKNOWN, verdictColors.BENIGN);
  assert.equal(new Set(Object.values(verdictColors)).size, 4);
  assert.equal(verdictVisuals.UNKNOWN.color, verdictColors.UNKNOWN);
  assert.ok(!verdictVisuals.UNKNOWN.color.toLowerCase().includes("green"));
  assert.ok(verdictVisuals.MALICIOUS.glow.includes("255, 64, 87"));
  assert.ok(verdictVisuals.SUSPICIOUS.glow.includes("255, 173, 34"));
});
