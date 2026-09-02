import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Search } from "lucide-react";
import { useState } from "react";
import { Panel } from "@/components/ui/Panel";
import { ThreatBadge, riskTone } from "@/components/ui/ThreatBadge";
import { formatDateTime } from "@/lib/format";
import { listCases } from "@/services/api";
import type { RiskLevel } from "@/types/analysis";

const SEVERITIES: (RiskLevel | "ALL")[] = ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"];

export function CasesPage() {
  const navigate = useNavigate();
  const { data } = useQuery({ queryKey: ["cases"], queryFn: listCases });
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState<RiskLevel | "ALL">("ALL");

  const rows = (data ?? []).filter((item) => {
    const matchesQuery =
      query.trim() === "" ||
      `${item.subject ?? ""} ${item.original_filename ?? ""} ${item.case_id}`
        .toLowerCase()
        .includes(query.toLowerCase());
    const matchesSeverity = severity === "ALL" || item.risk_severity === severity;
    return matchesQuery && matchesSeverity;
  });

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <div>
        <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-accent">Case Queue</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight lg:text-5xl">Investigations</h1>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex flex-1 items-center gap-2 rounded-sm border border-border bg-surface px-3 py-2 md:max-w-sm">
          <Search className="h-3.5 w-3.5 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search subject, filename or case ID"
            className="w-full bg-transparent text-xs outline-none placeholder:text-muted-foreground"
          />
        </div>
        <select
          value={severity}
          onChange={(e) => setSeverity(e.target.value as RiskLevel | "ALL")}
          className="rounded-sm border border-border bg-surface px-3 py-2 text-xs text-foreground outline-none transition-colors hover:border-accent/50"
        >
          {SEVERITIES.map((level) => (
            <option key={level} value={level}>
              {level === "ALL" ? "All severities" : level}
            </option>
          ))}
        </select>
      </div>

      <Panel spotlight className="overflow-x-auto p-0">
        <table className="w-full min-w-[900px] border-collapse text-left">
          <thead>
            <tr className="border-b border-border">
              {["Risk", "Subject", "Filename", "Created", "Status"].map((h) => (
                <th
                  key={h}
                  className="px-5 py-3 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((item, i) => (
              <motion.tr
                key={item.case_id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: i * 0.04 }}
                onClick={() =>
                  void navigate({ to: "/cases/$caseId", params: { caseId: item.case_id } })
                }
                className="cursor-pointer border-b border-border/60 transition-colors duration-200 last:border-0 hover:bg-surface-hover/70"
              >
                <td className="px-5 py-4">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold">{item.risk_score ?? "—"}</span>
                    {item.risk_severity && (
                      <ThreatBadge label={item.risk_severity} tone={riskTone(item.risk_severity)} />
                    )}
                  </div>
                </td>
                <td className="max-w-[320px] px-5 py-4">
                  <p className="truncate text-sm text-foreground">
                    {item.subject ?? "Subject unavailable"}
                  </p>
                  <p className="font-mono text-[11px] text-muted-foreground">{item.case_id}</p>
                </td>
                <td className="px-5 py-4 font-mono text-xs text-muted-foreground">
                  {item.original_filename ?? "Unavailable"}
                </td>
                <td className="px-5 py-4 font-mono text-[11px] text-muted-foreground">
                  {formatDateTime(item.created_at)}
                </td>
                <td className="px-5 py-4">
                  <ThreatBadge
                    label={item.status.replace("_", " ")}
                    tone={item.status === "COMPLETED" ? "success" : "accent"}
                  />
                </td>
              </motion.tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={5} className="px-5 py-10 text-center text-xs text-muted-foreground">
                  No investigations match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}
