import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { Database, FileKey2, Globe2, Link2, Radar, Search, ServerCog } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { Panel } from "@/components/ui/Panel";
import { ThreatBadge, type BadgeTone } from "@/components/ui/ThreatBadge";
import { getErrorMessage, getThreatIntelligenceWorkspace } from "@/services/api";
import type {
  IntelligenceStatus,
  IOCType,
  ProviderWorkspaceStatus,
  ThreatIOCRecord,
} from "@/types/analysis";

const IOC_FILTERS: Array<{ label: string; value: IOCType | "ALL" }> = [
  { label: "All IOC types", value: "ALL" },
  { label: "IP addresses", value: "IP_ADDRESS" },
  { label: "Domains", value: "DOMAIN" },
  { label: "URLs", value: "URL" },
  { label: "Attachment hashes", value: "ATTACHMENT_SHA256" },
];

const STATUS_FILTERS: Array<IntelligenceStatus | "ALL"> = [
  "ALL",
  "MALICIOUS",
  "SUSPICIOUS",
  "BENIGN",
  "UNKNOWN",
  "UNAVAILABLE",
];

function intelligenceTone(status: IntelligenceStatus): BadgeTone {
  if (status === "MALICIOUS") return "danger";
  if (status === "SUSPICIOUS") return "warning";
  if (status === "BENIGN") return "success";
  if (status === "UNAVAILABLE") return "network";
  return "neutral";
}

function providerTone(status: ProviderWorkspaceStatus): BadgeTone {
  if (status === "AVAILABLE") return "success";
  if (status === "PARTIAL") return "warning";
  if (status === "UNAVAILABLE") return "danger";
  return "neutral";
}

function domainFromUrl(value: string) {
  try {
    return new URL(value).hostname || "Unknown domain";
  } catch {
    return "Unknown domain";
  }
}

function SummaryCard({
  label,
  value,
  tone = "text-foreground",
}: {
  label: string;
  value: number;
  tone?: string;
}) {
  return (
    <Panel className="p-4">
      <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </p>
      <p className={`mt-2 font-mono text-2xl font-bold ${tone}`}>{value}</p>
    </Panel>
  );
}

function CaseLinks({ record }: { record: ThreatIOCRecord }) {
  return (
    <div className="flex max-w-64 flex-wrap gap-1.5">
      {record.associated_cases.map((item) => (
        <Link
          key={item.case_id}
          to="/cases/$caseId"
          params={{ caseId: item.case_id }}
          title={item.subject ?? item.original_filename ?? item.case_id}
          className="rounded-sm border border-border px-2 py-1 font-mono text-[10px] text-muted-foreground transition hover:border-accent/40 hover:text-accent"
        >
          {item.case_id.slice(0, 8)}
        </Link>
      ))}
    </div>
  );
}

function IntelligenceTable({
  title,
  icon,
  rows,
  valueHeading,
  secondary,
}: {
  title: string;
  icon: ReactNode;
  rows: ThreatIOCRecord[];
  valueHeading: string;
  secondary?(record: ThreatIOCRecord): ReactNode;
}) {
  return (
    <Panel className="overflow-hidden p-0">
      <div className="flex items-center gap-2 border-b border-border px-5 py-4">
        <span className="text-accent">{icon}</span>
        <h2 className="text-sm font-semibold">{title}</h2>
        <span className="ml-auto font-mono text-[10px] text-muted-foreground">
          {rows.length} OBSERVED
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[900px] border-collapse text-left">
          <thead>
            <tr className="border-b border-border">
              {[valueHeading, "Reputation", "Provider", "Intelligence", "Associated cases"].map(
                (heading) => (
                  <th
                    key={heading}
                    className="px-5 py-3 font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground"
                  >
                    {heading}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {rows.map((record) => (
              <tr
                key={`${record.ioc_type}:${record.value}`}
                className="border-b border-border/60 align-top last:border-0"
              >
                <td className="max-w-md px-5 py-4">
                  {record.filename && (
                    <p className="mb-1 text-xs font-medium text-foreground">{record.filename}</p>
                  )}
                  <p className="break-all font-mono text-[11px] text-muted-foreground">
                    {record.value}
                  </p>
                  {secondary?.(record)}
                </td>
                <td className="px-5 py-4">
                  <div className="flex flex-wrap gap-1.5">
                    <ThreatBadge label={record.status} tone={intelligenceTone(record.status)} />
                    {record.demo && <ThreatBadge label="SIMULATED" tone="ai" />}
                  </div>
                </td>
                <td className="px-5 py-4 text-xs text-muted-foreground">
                  {record.providers.length
                    ? record.providers.join(", ")
                    : "No verified provider result"}
                </td>
                <td className="max-w-sm px-5 py-4 text-xs leading-relaxed text-muted-foreground">
                  {record.confidence !== null && (
                    <p>Confidence: {Math.round(record.confidence * 100)}%</p>
                  )}
                  {record.categories.length > 0 && <p>{record.categories.join(", ")}</p>}
                  {record.details.length > 0 ? (
                    record.details.map((detail) => <p key={detail}>{detail}</p>)
                  ) : (
                    <p>No additional provider detail persisted.</p>
                  )}
                </td>
                <td className="px-5 py-4">
                  <CaseLinks record={record} />
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={5} className="px-5 py-9 text-center text-xs text-muted-foreground">
                  No persisted indicators match this section and the active filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

export function ThreatIntelligencePage() {
  const [query, setQuery] = useState("");
  const [iocType, setIocType] = useState<IOCType | "ALL">("ALL");
  const [status, setStatus] = useState<IntelligenceStatus | "ALL">("ALL");
  const workspace = useQuery({
    queryKey: ["threat-intelligence", "persisted"],
    queryFn: getThreatIntelligenceWorkspace,
    retry: false,
  });

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return (workspace.data?.indicators ?? []).filter((record) => {
      const haystack = [
        record.value,
        record.filename ?? "",
        ...record.providers,
        ...record.categories,
        ...record.associated_cases.flatMap((item) => [
          item.case_id,
          item.subject ?? "",
          item.original_filename ?? "",
        ]),
      ]
        .join(" ")
        .toLowerCase();
      return (
        (iocType === "ALL" || record.ioc_type === iocType) &&
        (status === "ALL" || record.status === status) &&
        (!needle || haystack.includes(needle))
      );
    });
  }, [iocType, query, status, workspace.data?.indicators]);

  if (workspace.isPending) {
    return (
      <div className="flex min-h-[55vh] items-center justify-center font-mono text-xs uppercase tracking-[0.22em] text-muted-foreground">
        Loading persisted intelligence…
      </div>
    );
  }

  if (workspace.isError || !workspace.data) {
    return (
      <div className="mx-auto max-w-2xl py-20 text-center">
        <Radar className="mx-auto h-8 w-8 text-danger" />
        <h1 className="mt-5 text-2xl font-semibold">Threat intelligence unavailable</h1>
        <p role="alert" className="mt-3 text-sm text-muted-foreground">
          {getErrorMessage(workspace.error, "Persisted intelligence could not be loaded.")}
        </p>
        <ActionButton variant="secondary" className="mt-5" onClick={() => void workspace.refetch()}>
          Retry
        </ActionButton>
      </div>
    );
  }

  const { summary, providers } = workspace.data;
  const demoPresent =
    workspace.data.indicators.some((item) => item.demo) || providers.some((item) => item.demo);
  const rowsFor = (type: IOCType) => filtered.filter((record) => record.ioc_type === type);
  const show = (type: IOCType) => iocType === "ALL" || iocType === type;

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <div>
        <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-accent">
          Persisted IOC workspace
        </p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight lg:text-5xl">Threat Intelligence</h1>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted-foreground">
          Aggregated from {workspace.data.cases_scanned} persisted case
          {workspace.data.cases_scanned === 1 ? "" : "s"}. Opening this view does not query
          reputation or geolocation providers.
        </p>
      </div>

      {demoPresent && (
        <Panel tone="ai" className="border-ai/35 bg-ai/5 p-4">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-ai">
            Simulated demo intelligence present
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            Demo results are synthetic and not verified VirusTotal or AbuseIPDB intelligence.
          </p>
        </Panel>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <SummaryCard label="Unique observed IOCs" value={summary.total_observed_iocs} />
        <SummaryCard
          label="Suspicious / malicious"
          value={summary.suspicious_or_malicious}
          tone="text-danger"
        />
        <SummaryCard label="Clean / no adverse result" value={summary.benign} tone="text-success" />
        <SummaryCard label="Unknown" value={summary.unknown} tone="text-muted-foreground" />
        <SummaryCard label="Unavailable" value={summary.unavailable} tone="text-network" />
      </div>

      <Panel className="p-4">
        <div className="flex flex-wrap gap-3">
          <label className="flex min-w-64 flex-1 items-center gap-2 rounded-sm border border-border bg-background px-3 py-2">
            <Search className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="sr-only">Search intelligence</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search IOC, filename, provider or case"
              className="w-full bg-transparent text-xs outline-none placeholder:text-muted-foreground"
            />
          </label>
          <select
            value={iocType}
            onChange={(event) => setIocType(event.target.value as IOCType | "ALL")}
            className="rounded-sm border border-border bg-background px-3 py-2 text-xs outline-none"
          >
            {IOC_FILTERS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value as IntelligenceStatus | "ALL")}
            className="rounded-sm border border-border bg-background px-3 py-2 text-xs outline-none"
          >
            {STATUS_FILTERS.map((item) => (
              <option key={item} value={item}>
                {item === "ALL" ? "All reputations" : item}
              </option>
            ))}
          </select>
        </div>
      </Panel>

      {summary.total_observed_iocs === 0 && (
        <Panel className="py-12 text-center">
          <Database className="mx-auto h-7 w-7 text-muted-foreground" />
          <p className="mt-4 text-sm font-medium">No persisted IOCs yet</p>
          <p className="mt-2 text-xs text-muted-foreground">
            Analyze an .eml file to populate this workspace.
          </p>
        </Panel>
      )}

      {summary.total_observed_iocs > 0 && filtered.length === 0 && (
        <Panel className="py-10 text-center text-xs text-muted-foreground">
          No indicators match the active search and filters.
        </Panel>
      )}

      {summary.total_observed_iocs > 0 &&
        show("IP_ADDRESS") &&
        (iocType !== "ALL" || rowsFor("IP_ADDRESS").length > 0) && (
          <IntelligenceTable
            title="IP Intelligence"
            icon={<Globe2 className="h-4 w-4" />}
            rows={rowsFor("IP_ADDRESS")}
            valueHeading="IP address"
          />
        )}
      {summary.total_observed_iocs > 0 &&
        show("DOMAIN") &&
        (iocType !== "ALL" || rowsFor("DOMAIN").length > 0) && (
          <IntelligenceTable
            title="Domain Intelligence"
            icon={<Radar className="h-4 w-4" />}
            rows={rowsFor("DOMAIN")}
            valueHeading="Domain"
          />
        )}
      {summary.total_observed_iocs > 0 &&
        show("URL") &&
        (iocType !== "ALL" || rowsFor("URL").length > 0) && (
          <IntelligenceTable
            title="URL Intelligence"
            icon={<Link2 className="h-4 w-4" />}
            rows={rowsFor("URL")}
            valueHeading="URL"
            secondary={(record) => (
              <p className="mt-1 text-[11px] text-muted-foreground">
                Domain: {domainFromUrl(record.value)}
              </p>
            )}
          />
        )}
      {summary.total_observed_iocs > 0 &&
        show("ATTACHMENT_SHA256") &&
        (iocType !== "ALL" || rowsFor("ATTACHMENT_SHA256").length > 0) && (
          <IntelligenceTable
            title="Hash / Attachment Intelligence"
            icon={<FileKey2 className="h-4 w-4" />}
            rows={rowsFor("ATTACHMENT_SHA256")}
            valueHeading="SHA-256"
          />
        )}

      <section>
        <div className="mb-3 flex items-center gap-2">
          <ServerCog className="h-4 w-4 text-accent" />
          <h2 className="text-sm font-semibold">Provider status from persisted results</h2>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {providers.map((provider) => (
            <Panel key={`${provider.category}:${provider.name}`} className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold">{provider.name}</p>
                  <p className="mt-1 font-mono text-[9px] uppercase tracking-widest text-muted-foreground">
                    {provider.category.replace("_", " ")}
                  </p>
                </div>
                <ThreatBadge label={provider.status} tone={providerTone(provider.status)} />
              </div>
              {provider.demo && (
                <ThreatBadge label="SIMULATED — NOT LIVE VERIFIED" tone="ai" className="mt-3" />
              )}
              {provider.messages.map((message) => (
                <p key={message} className="mt-3 text-[11px] leading-relaxed text-muted-foreground">
                  {message}
                </p>
              ))}
              {!provider.messages.length && (
                <p className="mt-3 text-[11px] text-muted-foreground">
                  Status reflects stored analysis results, not a live health check.
                </p>
              )}
            </Panel>
          ))}
        </div>
      </section>
    </div>
  );
}
