import { useQuery } from "@tanstack/react-query";
import { FileText } from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";
import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatDateTime } from "@/lib/format";
import { listCases } from "@/services/api";

export function ReportsPage() {
  const { data } = useQuery({ queryKey: ["cases"], queryFn: listCases });

  return (
    <div className="mx-auto max-w-[1200px] space-y-6">
      <div>
        <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-accent">Documentation</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight lg:text-5xl">Forensic Reports</h1>
      </div>

      <Panel sweep className="p-8">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div className="max-w-2xl">
            <h2 className="text-2xl font-bold tracking-tight">Generate Forensic Report</h2>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              The platform compiles a structured investigation report containing message headers,
              MIME structure, authentication results, indicators of compromise, observed routing
              infrastructure, AI findings, the forensic timeline and evidence hashes. Reports are
              intended to support internal investigation and escalation workflows; they do not by
              themselves establish legal admissibility.
            </p>
          </div>
          <ActionButton arrow>Generate Report</ActionButton>
        </div>
      </Panel>

      <div>
        <SectionHeader eyebrow="Archive" title="Available Case Reports" className="mb-4" />
        <div className="grid gap-4 md:grid-cols-2">
          {(data ?? []).map((item) => (
            <Panel key={item.case_id} interactive spotlight className="p-5">
              <div className="flex items-start gap-3">
                <FileText className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-foreground">{item.subject}</p>
                  <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                    {item.case_id} · {formatDateTime(item.created_at)}
                  </p>
                </div>
              </div>
              <div className="mt-4">
                <ActionButton variant="secondary">Download PDF</ActionButton>
              </div>
            </Panel>
          ))}
        </div>
      </div>
    </div>
  );
}
