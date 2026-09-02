import { motion } from "framer-motion";
import { CheckCircle2, MinusCircle } from "lucide-react";
import { Panel } from "@/components/ui/Panel";
import { cn } from "@/lib/utils";
import type { AiFinding } from "@/types/analysis";

export function FindingCard({ finding, index = 0 }: { finding: AiFinding; index?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05, ease: [0.22, 1, 0.36, 1] }}
    >
      <Panel
        interactive
        spotlight
        tilt
        tone="ai"
        className={cn(
          "group/finding h-full p-5",
          finding.detected && "border-ai/25 shadow-[0_0_28px_-18px_rgba(236,72,153,0.6)]",
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <p className="text-sm font-semibold text-foreground">{finding.title}</p>
          {finding.detected ? (
            <CheckCircle2 className="h-4 w-4 shrink-0 text-ai" />
          ) : (
            <MinusCircle className="h-4 w-4 shrink-0 text-muted-foreground" />
          )}
        </div>

        <p
          className={cn(
            "mt-3 font-mono text-[11px] uppercase tracking-[0.18em]",
            finding.detected ? "text-ai" : "text-muted-foreground",
          )}
        >
          {finding.detected ? "Detected" : "Not detected"}
        </p>

        <div className="mt-3">
          <div className="mb-1 flex justify-between font-mono text-[10px] text-muted-foreground">
            <span>Confidence</span>
            <span>{Math.round(finding.confidence * 100)}%</span>
          </div>
          <div className="h-1 w-full overflow-hidden rounded-full bg-muted/60">
            <motion.div
              className={cn(
                "h-full rounded-full transition-[filter] duration-200 group-hover/finding:brightness-125",
                finding.detected ? "bg-ai" : "bg-border-strong",
              )}
              initial={{ width: 0 }}
              animate={{ width: `${finding.confidence * 100}%` }}
              transition={{ duration: 0.8, delay: 0.15 + index * 0.05 }}
            />
          </div>
        </div>

        <p className="mt-4 text-xs leading-relaxed text-muted-foreground">{finding.explanation}</p>

        {finding.evidence.length > 0 && (
          <ul className="mt-3 space-y-1">
            {finding.evidence.map((item) => (
              <li key={item} className="font-mono text-[11px] text-foreground/70">
                · {item}
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </motion.div>
  );
}
