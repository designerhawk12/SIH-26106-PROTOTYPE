import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export const INVESTIGATION_TABS = [
  "Overview",
  "Email Forensics",
  "Authentication",
  "Indicators",
  "Infrastructure",
  "AI Findings",
  "Timeline",
  "Evidence",
] as const;

export type InvestigationTab = (typeof INVESTIGATION_TABS)[number];

interface Props {
  active: InvestigationTab;
  onChange: (tab: InvestigationTab) => void;
}

export function InvestigationTabs({ active, onChange }: Props) {
  return (
    <div className="flex gap-1 overflow-x-auto border-b border-border">
      {INVESTIGATION_TABS.map((tab) => (
        <button
          key={tab}
          type="button"
          onClick={() => onChange(tab)}
          className={cn(
            "relative whitespace-nowrap px-4 py-3 text-xs font-medium transition-colors duration-200",
            active === tab ? "text-foreground" : "text-muted-foreground hover:text-foreground",
          )}
        >
          {tab}
          {active === tab && (
            <motion.span
              layoutId="tab-underline"
              className="absolute inset-x-2 -bottom-px h-[2px] rounded-full bg-accent shadow-[0_0_12px_1px_rgba(215,255,63,0.5)]"
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            />
          )}
        </button>
      ))}
    </div>
  );
}
