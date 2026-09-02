import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Download, FileText, Info } from "lucide-react";
import { useState } from "react";
import { FindingCard } from "@/components/findings/FindingCard";
import { HeaderPanel } from "@/components/forensics/HeaderPanel";
import { MimeTree } from "@/components/forensics/MimeTree";
import { ReceivedChain } from "@/components/forensics/ReceivedChain";
import { IOCDataTable } from "@/components/indicators/IOCDataTable";
import { InfrastructureHop } from "@/components/infrastructure/InfrastructureHop";
import { AuthenticationCard } from "@/components/investigation/AuthenticationCard";
import { ExplainableRisk } from "@/components/investigation/ExplainableRisk";
import {
  InvestigationTabs,
  type InvestigationTab,
} from "@/components/investigation/InvestigationTabs";
import { RiskHero } from "@/components/investigation/RiskHero";
import { TimelineEvent } from "@/components/timeline/TimelineEvent";
import { ActionButton } from "@/components/ui/ActionButton";
import { CopyValue } from "@/components/ui/CopyValue";
import { EvidenceHash } from "@/components/ui/EvidenceHash";
import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { ThreatBadge, reputationTone } from "@/components/ui/ThreatBadge";
import { InfrastructureRouteVisual } from "@/components/visuals/InfrastructureRouteVisual";
import { formatBytes, formatDateTime } from "@/lib/format";
import { getCase } from "@/services/api";
import type { AnalysisViewModel } from "@/types/analysis";

export function InvestigationPage({ caseId }: { caseId: string }) {
  const { data } = useQuery({ queryKey: ["case", caseId], queryFn: () => getCase(caseId) });
  const [tab, setTab] = useState<InvestigationTab>("Overview");

  if (!data) {
    return (
      <div className="flex h-64 items-center justify-center font-mono text-xs text-muted-foreground">
        Loading case {caseId}…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <CaseHeader analysis={data} />
      {data.risk ? (
        <>
          <RiskHero risk={data.risk} />
          <ExplainableRisk signals={data.risk.signals} />
        </>
      ) : (
        <Panel className="p-6 text-sm text-muted-foreground">
          Risk scoring is not available for this partial analysis. Missing data is not treated as
          safe.
        </Panel>
      )}

      <div>
        <InvestigationTabs active={tab} onChange={setTab} />
        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            className="pt-6"
          >
            {tab === "Overview" && <OverviewTab analysis={data} />}
            {tab === "Email Forensics" && <ForensicsTab analysis={data} />}
            {tab === "Authentication" && <AuthenticationTab analysis={data} />}
            {tab === "Indicators" && <IndicatorsTab analysis={data} />}
            {tab === "Infrastructure" && <InfrastructureTab analysis={data} />}
            {tab === "AI Findings" && <FindingsTab analysis={data} />}
            {tab === "Timeline" && <TimelineTab analysis={data} />}
            {tab === "Evidence" && <EvidenceTab analysis={data} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

function CaseHeader({ analysis }: { analysis: AnalysisViewModel }) {
  const meta = [
    { label: "Subject", value: analysis.email.subject },
    { label: "Sender", value: analysis.email.sender },
    { label: "Receiver", value: analysis.email.receiver },
    { label: "Timestamp", value: formatDateTime(analysis.email.date) },
  ];

  return (
    <div className="flex flex-wrap items-start justify-between gap-6">
      <div className="min-w-0">
        <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-accent">
          {analysis.case_id}
        </p>
        <h1 className="mt-3 max-w-3xl text-3xl font-bold leading-tight tracking-tight lg:text-4xl">
          {analysis.email.subject}
        </h1>
        <dl className="mt-4 grid gap-x-8 gap-y-2 sm:grid-cols-2 lg:grid-cols-4">
          {meta.map((item) => (
            <div key={item.label} className="min-w-0">
              <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                {item.label}
              </dt>
              <dd className="truncate font-mono text-xs text-foreground/85">{item.value}</dd>
            </div>
          ))}
        </dl>
      </div>
      <div className="flex flex-wrap gap-2">
        <ActionButton icon={<FileText className="h-3.5 w-3.5" />} arrow>
          Generate Report
        </ActionButton>
        <ActionButton variant="secondary" icon={<Download className="h-3.5 w-3.5" />}>
          Export Evidence
        </ActionButton>
      </div>
    </div>
  );
}

function OverviewTab({ analysis }: { analysis: AnalysisViewModel }) {
  const auth = analysis.authentication;
  const detected = analysis.ai_findings.filter((f) => f.detected);

  return (
    <div className="grid gap-4 xl:grid-cols-3">
      <Panel spotlight tilt className="p-6 xl:col-span-2">
        <SectionHeader eyebrow="Assessment" title="Threat Summary" />
        <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
          {analysis.risk?.summary ?? "Risk scoring is unavailable for this partial analysis."}
        </p>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              Key Findings
            </p>
            <ul className="mt-2 space-y-1.5">
              {detected.slice(0, 5).map((f) => (
                <li key={f.type} className="text-xs text-foreground/85">
                  · {f.title} — {Math.round(f.confidence * 100)}% confidence
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              Risk Breakdown
            </p>
            <ul className="mt-2 space-y-1.5">
              {(analysis.risk?.signals ?? []).slice(0, 5).map((s) => (
                <li key={s.code} className="flex justify-between text-xs text-foreground/85">
                  <span className="truncate pr-3">{s.description}</span>
                  <span className="font-mono text-accent">+{s.points}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Panel>

      <Panel spotlight tilt className="p-6">
        <SectionHeader eyebrow="Message" title="Email Summary" />
        <dl className="mt-4 space-y-3">
          {[
            { label: "From", value: `${analysis.email.sender_display_name}` },
            { label: "Address", value: analysis.email.sender },
            { label: "To", value: analysis.email.receiver },
            { label: "Received", value: formatDateTime(analysis.email.date) },
          ].map((row) => (
            <div key={row.label}>
              <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                {row.label}
              </dt>
              <dd className="truncate font-mono text-xs text-foreground/85">{row.value}</dd>
            </div>
          ))}
        </dl>
      </Panel>

      <Panel spotlight tone="danger" className="p-6">
        <SectionHeader eyebrow="Sender validation" title="Authentication Summary" />
        <div className="mt-4 grid grid-cols-3 divide-x divide-border text-center">
          {(
            [
              ["SPF", auth.spf.result],
              ["DKIM", auth.dkim.result],
              ["DMARC", auth.dmarc.result],
            ] as const
          ).map(([label, result]) => (
            <div key={label} className="px-2">
              <p
                className={`text-lg font-bold ${
                  result === "PASS"
                    ? "text-success"
                    : result === "FAIL"
                      ? "text-danger"
                      : "text-muted-foreground"
                }`}
              >
                {result}
              </p>
              <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                {label}
              </p>
            </div>
          ))}
        </div>
      </Panel>

      <Panel spotlight tone="network" className="p-6 xl:col-span-2">
        <SectionHeader eyebrow="Network" title="Infrastructure Summary" />
        <div className="mt-4 space-y-2">
          {analysis.infrastructure.nodes.map((node) => (
            <div
              key={node.ip}
              className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 py-2 last:border-0"
            >
              <div className="min-w-0">
                <p className="font-mono text-xs text-network">{node.ip}</p>
                <p className="text-[11px] text-muted-foreground">
                  {node.role} · {node.city ?? "—"}, {node.country ?? "—"} · {node.isp ?? "—"}
                </p>
              </div>
              <ThreatBadge label={node.reputation} tone={reputationTone(node.reputation)} />
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function ForensicsTab({ analysis }: { analysis: AnalysisViewModel }) {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <HeaderPanel email={analysis.email} />
      <div className="space-y-4">
        <MimeTree root={analysis.mime} />
        <ReceivedChain hops={analysis.received_chain} />
      </div>
    </div>
  );
}

function AuthenticationTab({ analysis }: { analysis: AnalysisViewModel }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <AuthenticationCard name="SPF" check={analysis.authentication.spf} index={0} />
      <AuthenticationCard name="DKIM" check={analysis.authentication.dkim} index={1} />
      <AuthenticationCard name="DMARC" check={analysis.authentication.dmarc} index={2} />
    </div>
  );
}

function IndicatorsTab({ analysis }: { analysis: AnalysisViewModel }) {
  const { ips, domains, urls, attachments } = analysis.indicators;

  return (
    <div className="space-y-4">
      <IOCDataTable
        eyebrow="IOC"
        title="IP Addresses"
        rows={ips}
        columns={[
          {
            header: "IP Address",
            render: (r) => <span className="font-mono text-xs">{r.ip}</span>,
          },
          {
            header: "Reputation",
            render: (r) => <ThreatBadge label={r.reputation} tone={reputationTone(r.reputation)} />,
          },
          {
            header: "Source",
            render: (r) => <span className="text-xs text-muted-foreground">{r.source}</span>,
          },
          {
            header: "Actions",
            render: (r) => <CopyValue value={r.ip} revealOnRowHover />,
          },
        ]}
      />

      <IOCDataTable
        eyebrow="IOC"
        title="Domains"
        rows={domains}
        columns={[
          {
            header: "Domain",
            render: (r) => <span className="font-mono text-xs">{r.domain}</span>,
          },
          {
            header: "Reputation",
            render: (r) => <ThreatBadge label={r.reputation} tone={reputationTone(r.reputation)} />,
          },
          {
            header: "Type",
            render: (r) => <span className="text-xs text-muted-foreground">{r.type}</span>,
          },
        ]}
      />

      <IOCDataTable
        eyebrow="IOC"
        title="URLs"
        rows={urls}
        columns={[
          {
            header: "URL",
            className: "max-w-[420px]",
            render: (r) => (
              <span className="block truncate font-mono text-xs" title={r.url}>
                {r.url}
              </span>
            ),
          },
          {
            header: "Domain",
            render: (r) => <span className="font-mono text-xs">{r.domain}</span>,
          },
          {
            header: "Reputation",
            render: (r) => <ThreatBadge label={r.reputation} tone={reputationTone(r.reputation)} />,
          },
        ]}
      />

      <IOCDataTable
        eyebrow="IOC"
        title="Attachments"
        rows={attachments}
        columns={[
          { header: "Filename", render: (r) => <span className="text-xs">{r.filename}</span> },
          {
            header: "MIME Type",
            render: (r) => (
              <span className="font-mono text-xs text-muted-foreground">{r.mime_type}</span>
            ),
          },
          {
            header: "Size",
            render: (r) => (
              <span className="font-mono text-xs text-muted-foreground">
                {formatBytes(r.size_bytes)}
              </span>
            ),
          },
          {
            header: "SHA-256",
            className: "max-w-[260px]",
            render: (r) => <CopyValue value={r.sha256} truncate revealOnRowHover />,
          },
          {
            header: "Status",
            render: (r) => <ThreatBadge label={r.status} tone={reputationTone(r.status)} />,
          },
        ]}
      />
    </div>
  );
}

function InfrastructureTab({ analysis }: { analysis: AnalysisViewModel }) {
  return (
    <div className="space-y-4">
      <SectionHeader eyebrow="Network" title="Observed Email Infrastructure" />
      <Panel className="flex items-start gap-3 border-network/25 bg-network/[0.04] p-4">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-network" />
        <p className="text-xs leading-relaxed text-muted-foreground">
          {analysis.infrastructure.disclaimer}
        </p>
      </Panel>
      <InfrastructureRouteVisual nodes={analysis.infrastructure.nodes} />
      <div>
        {analysis.infrastructure.nodes.map((node, i) => (
          <InfrastructureHop
            key={node.ip}
            node={node}
            index={i}
            isLast={i === analysis.infrastructure.nodes.length - 1}
          />
        ))}
      </div>
    </div>
  );
}

function FindingsTab({ analysis }: { analysis: AnalysisViewModel }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {analysis.ai_findings.map((finding, i) => (
        <FindingCard key={finding.type} finding={finding} index={i} />
      ))}
    </div>
  );
}

function TimelineTab({ analysis }: { analysis: AnalysisViewModel }) {
  return (
    <Panel spotlight className="max-w-2xl p-6">
      <SectionHeader eyebrow="Chronology" title="Forensic Timeline" />
      <div className="mt-6">
        {analysis.timeline.map((event, i) => (
          <TimelineEvent
            key={`${event.timestamp}-${event.label}`}
            event={event}
            index={i}
            isLast={i === analysis.timeline.length - 1}
          />
        ))}
      </div>
    </Panel>
  );
}

function EvidenceTab({ analysis }: { analysis: AnalysisViewModel }) {
  const { evidence } = analysis;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-2">
        <EvidenceHash
          label="Original Email SHA-256"
          value={evidence.email_sha256}
          caption="Integrity hash computed at intake."
        />
        {evidence.attachment_hashes.map((item) => (
          <EvidenceHash
            key={item.sha256}
            label={`Attachment SHA-256 · ${item.filename}`}
            value={item.sha256}
          />
        ))}
        <EvidenceHash label="Case ID" value={evidence.case_id} />
        <EvidenceHash label="Analysis Timestamp" value={formatDateTime(evidence.analyzed_at)} />
      </div>

      <Panel className="p-6">
        <SectionHeader eyebrow="Chain of custody" title="Evidence Events" />
        <div className="mt-6">
          {evidence.events.map((event, i) => (
            <TimelineEvent
              key={`${event.timestamp}-${event.label}`}
              event={event}
              index={i}
              isLast={i === evidence.events.length - 1}
            />
          ))}
        </div>
      </Panel>
    </div>
  );
}
