import { Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";
import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { ThreatBadge, riskTone } from "@/components/ui/ThreatBadge";
import { formatRelative } from "@/lib/format";
import type { CaseSummary } from "@/types/analysis";

export function RecentInvestigations({ cases }: { cases: CaseSummary[] }) {
  return (
    <Panel className="h-full p-5">
      <SectionHeader
        eyebrow="Queue"
        title="Recent Investigations"
        actions={
          <Link
            to="/cases"
            className="inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground transition-colors hover:text-accent"
          >
            View all <ArrowUpRight className="h-3 w-3" />
          </Link>
        }
      />
      <div className="mt-4 divide-y divide-border">
        {cases.slice(0, 5).map((item) => (
          <Link
            key={item.case_id}
            to="/cases/$caseId"
            params={{ caseId: item.case_id }}
            className="group flex items-center gap-4 py-3 transition-colors hover:bg-surface-hover/60"
          >
            <span className="w-10 shrink-0 text-center font-mono text-sm font-bold text-foreground">
              {item.risk_score}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm text-foreground group-hover:text-accent">
                {item.subject}
              </p>
              <p className="truncate font-mono text-[11px] text-muted-foreground">{item.sender}</p>
            </div>
            <ThreatBadge label={item.risk_level} tone={riskTone(item.risk_level)} />
            <span className="hidden w-16 shrink-0 text-right font-mono text-[11px] text-muted-foreground md:block">
              {formatRelative(item.created_at)}
            </span>
          </Link>
        ))}
      </div>
    </Panel>
  );
}
