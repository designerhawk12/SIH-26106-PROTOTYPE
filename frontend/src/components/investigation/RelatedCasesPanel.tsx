import { useQuery } from "@tanstack/react-query";
import { Link, Network } from "lucide-react";
import { Link as RouterLink } from "@tanstack/react-router";

import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { ThreatBadge, riskTone, type BadgeTone } from "@/components/ui/ThreatBadge";
import { getErrorMessage, getRelatedCases } from "@/services/api";
import type { CorrelationStrength, RelatedCase } from "@/types/correlation";

function strengthTone(value: CorrelationStrength): BadgeTone {
  if (value === "HIGH") return "danger";
  if (value === "MEDIUM") return "warning";
  return "neutral";
}

function RelatedCaseRow({ item }: { item: RelatedCase }) {
  return (
    <li className="border-b border-border/60 px-5 py-4 last:border-0">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <RouterLink
            to="/cases/$caseId"
            params={{ caseId: item.case_id }}
            className="font-mono text-xs text-accent transition hover:text-accent/80"
          >
            CASE {item.case_id.slice(0, 8)}
          </RouterLink>
          <p className="mt-1 text-sm text-foreground">{item.subject ?? "Subject unavailable"}</p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <ThreatBadge label={`${item.shared_indicator_count} SHARED`} tone="network" />
          <ThreatBadge label={`${item.correlation_strength} CORRELATION`} tone={strengthTone(item.correlation_strength)} />
          {item.risk_severity && <ThreatBadge label={item.risk_severity} tone={riskTone(item.risk_severity)} />}
        </div>
      </div>

      <div className="mt-3 grid gap-3 lg:grid-cols-2">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Relationship reasons
          </p>
          <ul className="mt-1.5 space-y-1 text-xs leading-relaxed text-muted-foreground">
            {item.relationship_reasons.map((reason) => <li key={reason}>• {reason}</li>)}
          </ul>
        </div>
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Shared indicators
          </p>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {item.shared_indicators.map((indicator) => (
              <ThreatBadge
                key={`${indicator.indicator_type}:${indicator.value}`}
                label={`${indicator.indicator_type.replaceAll("_", " ")}: ${indicator.value}`}
                tone="neutral"
                className="max-w-full break-all normal-case tracking-normal"
              />
            ))}
          </div>
        </div>
      </div>
    </li>
  );
}

export function RelatedCasesPanel({ caseId }: { caseId: string }) {
  const related = useQuery({
    queryKey: ["case-related", caseId],
    queryFn: () => getRelatedCases(caseId),
    retry: false,
  });

  if (related.isPending) {
    return <Panel className="p-6 font-mono text-xs text-muted-foreground">Comparing persisted forensic evidence…</Panel>;
  }

  if (related.isError) {
    const message = getErrorMessage(related.error, "Potentially related cases are unavailable.");
    return (
      <Panel className="p-6">
        <p className="text-sm text-muted-foreground" role="alert">{message}</p>
        <p className="mt-2 text-xs text-muted-foreground">
          Cross-case correlation is restricted to Senior Analysts and Administrators.
        </p>
      </Panel>
    );
  }

  const workspace = related.data;
  return (
    <Panel className="overflow-hidden p-0">
      <div className="p-6">
        <SectionHeader
          eyebrow="Deterministic correlation"
          title="Potentially Related Cases"
          subtitle="Shared indicators are persisted forensic observations, not attacker attribution or a confirmed campaign."
          actions={<ThreatBadge label={`${workspace?.total ?? 0} RELATED`} tone="network" />}
        />
        <div className="mt-4 flex items-start gap-2 rounded-md border border-network/20 bg-network/[0.04] p-3 text-xs leading-relaxed text-muted-foreground">
          <Network className="mt-0.5 h-4 w-4 shrink-0 text-network" />
          <p>{workspace?.disclaimer}</p>
        </div>
      </div>

      {workspace?.items.length ? (
        <ul>{workspace.items.map((item) => <RelatedCaseRow key={item.case_id} item={item} />)}</ul>
      ) : (
        <div className="border-t border-border px-6 py-10 text-center text-sm text-muted-foreground">
          No potentially related persisted cases were found for the available forensic indicators.
        </div>
      )}
    </Panel>
  );
}
