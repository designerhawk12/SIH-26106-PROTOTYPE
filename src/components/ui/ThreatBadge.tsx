import { cn } from "@/lib/utils";
import type { AuthResult, Reputation, RiskLevel } from "@/types/analysis";

export type BadgeTone =
  | "accent"
  | "danger"
  | "warning"
  | "success"
  | "network"
  | "ai"
  | "neutral";

const tones: Record<BadgeTone, string> = {
  accent: "border-accent/35 bg-accent/10 text-accent",
  danger: "border-danger/35 bg-danger/10 text-danger",
  warning: "border-warning/35 bg-warning/10 text-warning",
  success: "border-success/35 bg-success/10 text-success",
  network: "border-network/35 bg-network/10 text-network",
  ai: "border-ai/35 bg-ai/10 text-ai",
  neutral: "border-border bg-muted/40 text-muted-foreground",
};

export function riskTone(level: RiskLevel): BadgeTone {
  switch (level) {
    case "CRITICAL":
      return "danger";
    case "HIGH":
      return "danger";
    case "MEDIUM":
      return "warning";
    default:
      return "success";
  }
}

export function reputationTone(reputation: Reputation): BadgeTone {
  switch (reputation) {
    case "malicious":
      return "danger";
    case "suspicious":
      return "warning";
    case "clean":
      return "success";
    case "neutral":
      return "network";
    default:
      return "neutral";
  }
}

export function authTone(result: AuthResult): BadgeTone {
  if (result === "PASS") return "success";
  if (result === "FAIL") return "danger";
  return "neutral";
}

interface ThreatBadgeProps {
  label: string;
  tone?: BadgeTone;
  className?: string;
}

export function ThreatBadge({ label, tone = "neutral", className }: ThreatBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.16em]",
        tones[tone],
        className,
      )}
    >
      {label}
    </span>
  );
}
