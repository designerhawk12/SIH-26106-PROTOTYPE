import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { CountUp } from "@/components/ui/RiskScore";
import type { DashboardStats } from "@/types/analysis";

export function AuthFailuresCard({
  failures,
}: {
  failures: DashboardStats["authentication_failures"];
}) {
  const rows = [
    { label: "SPF", value: failures.spf },
    { label: "DKIM", value: failures.dkim },
    { label: "DMARC", value: failures.dmarc },
  ];

  return (
    <Panel interactive className="h-full p-5">
      <SectionHeader eyebrow="Last 30 days" title="Authentication Failures" />
      <div className="mt-6 grid grid-cols-3 divide-x divide-border">
        {rows.map((row) => (
          <div key={row.label} className="px-2 text-center first:pl-0 last:pr-0">
            <CountUp value={row.value} className="block text-2xl font-bold text-danger" />
            <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              {row.label}
            </p>
          </div>
        ))}
      </div>
      <p className="mt-5 text-xs leading-relaxed text-muted-foreground">
        Sender authentication failures remain the highest-yield early signal for impersonation
        driven campaigns.
      </p>
    </Panel>
  );
}
