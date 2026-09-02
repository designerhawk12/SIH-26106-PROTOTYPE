import { useQuery } from "@tanstack/react-query";
import { FileText } from "lucide-react";
import { useState } from "react";
import { ActionButton } from "@/components/ui/ActionButton";
import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatDateTime } from "@/lib/format";
import { downloadCaseReport, getErrorMessage, listCases } from "@/services/api";

export function ReportsPage() {
  const {
    data,
    error: casesError,
    isError,
    isPending,
    refetch,
  } = useQuery({
    queryKey: ["cases"],
    queryFn: listCases,
    retry: false,
  });
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);

  const handleDownload = async (caseId: string) => {
    if (activeCaseId) return;
    setActiveCaseId(caseId);
    setReportError(null);
    try {
      await downloadCaseReport(caseId);
    } catch (error) {
      setReportError(getErrorMessage(error, "The report is not available yet."));
    } finally {
      setActiveCaseId(null);
    }
  };

  return (
    <div className="mx-auto max-w-[1200px] space-y-6">
      <div>
        <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-accent">
          Documentation
        </p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight lg:text-5xl">Forensic Reports</h1>
      </div>

      <Panel sweep spotlight tilt className="p-8">
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
          <ActionButton
            arrow
            disabled={!data?.[0] || activeCaseId !== null}
            onClick={() => data?.[0] && void handleDownload(data[0].case_id)}
          >
            {activeCaseId === data?.[0]?.case_id ? "Preparing Report" : "Generate Latest Report"}
          </ActionButton>
        </div>
        {reportError && (
          <p role="alert" className="mt-4 text-xs text-danger">
            {reportError}
          </p>
        )}
      </Panel>

      <div>
        <SectionHeader eyebrow="Archive" title="Available Case Reports" className="mb-4" />
        {isPending && <p className="text-xs text-muted-foreground">Loading case reports…</p>}
        {isError && (
          <Panel className="p-6 text-center">
            <p role="alert" className="text-xs text-danger">
              {getErrorMessage(casesError, "Case reports could not be loaded.")}
            </p>
            <ActionButton variant="secondary" className="mt-4" onClick={() => void refetch()}>
              Retry
            </ActionButton>
          </Panel>
        )}
        <div className="grid gap-4 md:grid-cols-2">
          {(data ?? []).map((item) => (
            <Panel key={item.case_id} interactive spotlight tilt className="p-5">
              <div className="flex items-start gap-3">
                <FileText className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-foreground">
                    {item.subject ?? "Subject unavailable"}
                  </p>
                  <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                    {item.case_id} · {formatDateTime(item.created_at)}
                  </p>
                </div>
              </div>
              <div className="mt-4">
                <ActionButton
                  variant="secondary"
                  disabled={activeCaseId !== null}
                  onClick={() => void handleDownload(item.case_id)}
                >
                  {activeCaseId === item.case_id ? "Preparing PDF" : "Download PDF"}
                </ActionButton>
              </div>
            </Panel>
          ))}
        </div>
      </div>
    </div>
  );
}
