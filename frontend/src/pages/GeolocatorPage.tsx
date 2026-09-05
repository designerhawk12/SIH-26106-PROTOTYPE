import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { Globe2, Search } from "lucide-react";
import { lazy, Suspense, useMemo, useState } from "react";
import { Panel } from "@/components/ui/Panel";
import { ActionButton } from "@/components/ui/ActionButton";
import { ThreatBadge } from "@/components/ui/ThreatBadge";
import { getErrorMessage, getInfrastructure } from "@/services/api";
import {
  coordinates,
  emptyInfrastructureFilters,
  filterInfrastructure,
  verdictColors,
} from "@/lib/infrastructure";
import type { InfrastructureObservation } from "@/types/infrastructure";

// Leaflet accesses window on import. AppShell only mounts this page after the
// client session is restored; the lazy boundary keeps Leaflet out of SSR.
const InfrastructureMap = lazy(() => import("@/components/geolocator/InfrastructureMap"));
const disclaimer =
  "Observed infrastructure geolocation does not establish the physical location or identity of an attacker.";
const filterClass =
  "min-w-0 w-full rounded-sm border border-border bg-background px-3 py-2 text-xs text-foreground";

function ReputationBadge({ record }: { record: InfrastructureObservation }) {
  const tone =
    record.verdict === "MALICIOUS"
      ? "danger"
      : record.verdict === "SUSPICIOUS"
        ? "warning"
        : record.verdict === "BENIGN"
          ? "success"
          : "neutral";
  return <ThreatBadge tone={tone} label={record.verdict} />;
}

function Details({
  record,
  all,
}: {
  record: InfrastructureObservation;
  all: InfrastructureObservation[];
}) {
  const related = all.filter((item) => item.ip_address === record.ip_address);
  const cases = [...new Map(related.map((item) => [item.case.case_id, item.case])).values()];
  const times = related
    .map((item) => item.observed_at)
    .sort((a, b) => Date.parse(a) - Date.parse(b));
  const location = record.location;
  const fields = [
    ["Threat Reputation", record.verdict],
    ["Country", location?.country],
    ["Region", location?.region],
    ["City", location?.city],
    ["ISP", location?.isp],
    ["ASN", location?.asn],
    ["Organization", location?.organization],
    ["Network", location?.network],
    ["Geolocation provider", location?.provider],
    ["Geolocation status", location?.status ?? "UNKNOWN"],
    ["Reputation provider", record.threat_providers.join(", ") || null],
    ["Intelligence availability", record.threat_intel_status],
    ["Case risk severity", record.case.risk_severity ?? "UNKNOWN"],
    ["First observed by platform", new Date(times[0] ?? record.observed_at).toLocaleString()],
    [
      "Last observed by platform",
      new Date(times[times.length - 1] ?? record.observed_at).toLocaleString(),
    ],
  ];
  return (
    <Panel className="min-w-0 p-5">
      <p className="text-xs uppercase tracking-widest text-muted-foreground">
        Infrastructure details
      </p>
      <h2 className="mt-2 break-all font-mono text-lg">{record.ip_address}</h2>
      <div className="mt-3 flex flex-wrap gap-2">
        <ReputationBadge record={record} />
        {record.demo && <ThreatBadge tone="warning" label="SIMULATED EVIDENCE" />}
        {record.case.status === "PARTIAL" && <ThreatBadge tone="warning" label="PARTIAL CASE" />}
      </div>
      <p className="mt-3 text-xs text-muted-foreground">
        Metadata from case {record.case.case_id.slice(0, 8)}. Separate observations retain their
        original provider data.
      </p>
      <dl className="mt-4 space-y-3 text-xs">
        {fields.map(([label, value]) => (
          <div key={label}>
            <dt className="text-muted-foreground">{label}</dt>
            <dd className="mt-0.5 break-words">{value || "Not recorded"}</dd>
          </div>
        ))}
      </dl>
      <h3 className="mt-5 text-xs font-semibold">Related Cases ({cases.length})</h3>
      <div className="mt-2 flex flex-col gap-2">
        {cases.map((item) => (
          <Link
            key={item.case_id}
            to="/cases/$caseId"
            params={{ caseId: item.case_id }}
            className="break-words rounded-sm border border-border p-2 text-xs hover:border-accent/40 hover:text-accent"
          >
            <span className="font-mono">{item.case_id.slice(0, 8)}</span> ·{" "}
            {item.subject ?? "Subject unavailable"}
          </Link>
        ))}
      </div>
    </Panel>
  );
}

export function GeolocatorPage() {
  const query = useQuery({
    queryKey: ["infrastructure"],
    queryFn: getInfrastructure,
    refetchOnWindowFocus: false,
  });
  const [filters, setFilters] = useState(emptyInfrastructureFilters);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showRouting, setShowRouting] = useState(false);
  const records = useMemo(() => query.data?.observations ?? [], [query.data]);
  const filtered = useMemo(() => filterInfrastructure(records, filters), [records, filters]);
  const selected = filtered.find((record) => record.id === selectedId);
  const cases = [...new Map(records.map((record) => [record.case.case_id, record.case])).values()];
  const countries = [
    ...new Set(records.map((record) => record.location?.country ?? "UNKNOWN")),
  ].sort();
  const mapped = filtered.filter((record) => coordinates(record));
  const segments =
    showRouting && filters.caseId !== "ALL"
      ? (query.data?.route_segments ?? []).filter((segment) => segment.case_id === filters.caseId)
      : [];
  const setFilter = (key: keyof typeof filters, value: string) =>
    setFilters((current) => ({ ...current, [key]: value }));

  return (
    <div className="mx-auto max-w-[1600px] space-y-5">
      <header>
        <p className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-accent">
          <Globe2 className="h-4 w-4" />
          Geolocator
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
          Observed Infrastructure Map
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
          Explore public IP infrastructure observed during email investigations. Locations and
          reputation reflect stored analysis results.
        </p>
      </header>
      <p className="rounded-sm border border-network/25 bg-network/5 p-3 text-xs text-muted-foreground">
        {disclaimer}
      </p>
      {query.isPending ? (
        <Panel className="p-8">
          <p role="status">Loading observed infrastructure…</p>
        </Panel>
      ) : query.isError ? (
        <Panel className="p-6">
          <p role="alert">{getErrorMessage(query.error)}</p>
          <ActionButton className="mt-4" onClick={() => void query.refetch()}>
            Retry
          </ActionButton>
        </Panel>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {[
              ["Public IPs", new Set(records.map((record) => record.ip_address)).size],
              ["Mapped observations", records.filter((record) => coordinates(record)).length],
              ["Without coordinates", records.filter((record) => !coordinates(record)).length],
              ["Associated cases", cases.length],
            ].map(([label, value]) => (
              <Panel key={label} className="p-4">
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="mt-2 font-mono text-2xl">{value}</p>
              </Panel>
            ))}
          </div>
          {records.some((record) => record.demo) && (
            <p className="rounded-sm border border-warning/30 bg-warning/5 p-3 text-xs text-warning">
              Simulated demo observations are present and labeled. Their locations and reputation
              are not verified live provider results.
            </p>
          )}
          <Panel className="space-y-3 p-4">
            <label className="flex items-center gap-2">
              <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
              <input
                aria-label="Search infrastructure"
                className={filterClass}
                placeholder="Search IP, city, organization or case…"
                value={filters.search}
                onChange={(event) => setFilter("search", event.target.value)}
              />
            </label>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-5">
              <select
                aria-label="Case filter"
                className={filterClass}
                value={filters.caseId}
                onChange={(event) => setFilter("caseId", event.target.value)}
              >
                <option value="ALL">All Cases</option>
                {cases.map((item) => (
                  <option key={item.case_id} value={item.case_id}>
                    {item.case_id.slice(0, 8)} · {item.subject ?? "Subject unavailable"}
                  </option>
                ))}
              </select>
              <select
                aria-label="Risk severity filter"
                className={filterClass}
                value={filters.severity}
                onChange={(event) => setFilter("severity", event.target.value)}
              >
                <option value="ALL">All Risk Severities</option>
                {["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"].map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
              <select
                aria-label="IOC verdict filter"
                className={filterClass}
                value={filters.verdict}
                onChange={(event) => setFilter("verdict", event.target.value)}
              >
                <option value="ALL">All IOC Verdicts</option>
                {Object.keys(verdictColors).map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
              <select
                aria-label="Country filter"
                className={filterClass}
                value={filters.country}
                onChange={(event) => setFilter("country", event.target.value)}
              >
                <option value="ALL">All Countries</option>
                {countries.map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
              <select
                aria-label="Data availability filter"
                className={filterClass}
                value={filters.availability}
                onChange={(event) => setFilter("availability", event.target.value)}
              >
                <option value="ALL">All Data Availability</option>
                <option value="MAPPED">Coordinates available</option>
                <option value="MISSING">Coordinates unavailable</option>
                <option value="UNAVAILABLE">Provider unavailable</option>
              </select>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
              <label className="flex items-center gap-2 text-muted-foreground">
                <input
                  type="checkbox"
                  checked={showRouting}
                  disabled={filters.caseId === "ALL"}
                  onChange={(event) => setShowRouting(event.target.checked)}
                />
                Observed Mail Routing · select a case
              </label>
              <button
                className="text-accent"
                onClick={() => {
                  setFilters(emptyInfrastructureFilters);
                  setShowRouting(false);
                }}
              >
                Reset filters
              </button>
            </div>
            {showRouting && filters.caseId !== "ALL" && (
              <p className="text-xs text-muted-foreground">
                Lines follow adjacent, timestamped Received hops with persisted coordinates. Gaps
                remain unconnected.{" "}
                {segments.length === 0 ? "No supported routing segments for this case." : ""}
              </p>
            )}
          </Panel>
          <div className="grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1fr)_300px]">
            <div className="min-w-0 space-y-3">
              <Suspense
                fallback={
                  <Panel className="flex h-[420px] items-center justify-center">
                    <p role="status">Loading map…</p>
                  </Panel>
                }
              >
                <InfrastructureMap
                  records={filtered}
                  segments={segments}
                  selectedId={selected?.id ?? null}
                  onSelect={setSelectedId}
                />
              </Suspense>
              <p className="text-xs text-muted-foreground">
                {mapped.length} mapped of {filtered.length} observations. UNKNOWN reputation is not
                a benign verdict. Base map © OpenStreetMap contributors.
              </p>
            </div>
            {selected ? (
              <Details record={selected} all={records} />
            ) : (
              <Panel className="p-5">
                <h2 className="text-sm font-semibold">Observed Email Infrastructure</h2>
                <p className="mt-3 text-sm text-muted-foreground">
                  Select a marker or an observation below to inspect its metadata and related cases.
                </p>
                <p className="mt-3 text-xs text-muted-foreground">
                  Overlapping locations remain separate observations in the list.
                </p>
              </Panel>
            )}
          </div>
          {!filtered.length ? (
            <Panel className="p-8 text-center">
              <h2 className="font-semibold">
                {records.length
                  ? "No infrastructure matches these filters"
                  : "No public infrastructure observed"}
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {records.length
                  ? "Adjust the filters to see other persisted observations."
                  : "Analyze an email containing public routing IPs to populate this workspace."}
              </p>
            </Panel>
          ) : (
            <Panel className="overflow-hidden">
              <div className="border-b border-border p-4">
                <h2 className="text-sm font-semibold">Persisted observations</h2>
                {!mapped.length && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    No usable coordinates in this selection. Observations remain available below; no
                    markers are placed.
                  </p>
                )}
              </div>
              <ul className="max-h-[420px] divide-y divide-border overflow-y-auto">
                {filtered.map((record) => (
                  <li key={record.id}>
                    <button
                      onClick={() => setSelectedId(record.id)}
                      aria-pressed={selected?.id === record.id}
                      className="flex w-full flex-wrap items-center justify-between gap-3 p-4 text-left transition hover:bg-surface-hover aria-pressed:bg-surface-hover"
                    >
                      <span className="min-w-0">
                        <span className="break-all font-mono text-sm">{record.ip_address}</span>
                        <span className="mt-1 block text-xs text-muted-foreground">
                          {[record.location?.city, record.location?.country]
                            .filter(Boolean)
                            .join(", ") || "Location not recorded"}{" "}
                          · Case {record.case.case_id.slice(0, 8)} · {record.case.status}
                        </span>
                      </span>
                      <span className="flex flex-wrap items-center gap-2">
                        <ReputationBadge record={record} />
                        {record.demo && <ThreatBadge tone="warning" label="SIMULATED" />}
                        <span className="text-xs text-muted-foreground">
                          {coordinates(record)
                            ? "Mapped"
                            : record.location?.status === "PROVIDER_ERROR"
                              ? "Provider unavailable"
                              : "Coordinates unavailable"}
                        </span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </>
      )}
    </div>
  );
}
