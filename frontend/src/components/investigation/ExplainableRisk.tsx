import { motion } from "framer-motion";
import { useState } from "react";
import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import type { RiskSignal } from "@/types/analysis";

export function ExplainableRisk({ signals }: { signals: RiskSignal[] }) {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <Panel className="p-6">
      <SectionHeader
        eyebrow="Explainability"
        title="Why this email was flagged"
        subtitle="Each contributing signal and the points it added to the overall risk score."
      />
      <div className="mt-5 divide-y divide-border">
        {signals.map((signal, i) => (
          <div
            key={signal.label}
            onMouseEnter={() => setOpen(i)}
            onMouseLeave={() => setOpen(null)}
            className="group cursor-default py-3 transition-colors"
          >
            <div className="flex items-center justify-between gap-4">
              <div className="flex min-w-0 items-center gap-3">
                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent/70 transition-all duration-200 group-hover:shadow-[0_0_10px_2px_rgba(215,255,63,0.5)]" />
                <span className="truncate text-sm text-foreground/90 transition-colors group-hover:text-foreground">
                  {signal.label}
                </span>
              </div>
              <span className="shrink-0 font-mono text-sm font-semibold text-accent">
                +{signal.weight}
              </span>
            </div>
            <motion.div
              initial={false}
              animate={{ height: open === i ? "auto" : 0, opacity: open === i ? 1 : 0 }}
              transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
              className="overflow-hidden"
            >
              <p className="pt-2 pl-4.5 text-xs leading-relaxed text-muted-foreground">
                <span className="font-mono uppercase tracking-widest text-muted-foreground/70">
                  {signal.category}
                </span>
                {" — "}
                {signal.detail}
              </p>
            </motion.div>
          </div>
        ))}
      </div>
    </Panel>
  );
}
