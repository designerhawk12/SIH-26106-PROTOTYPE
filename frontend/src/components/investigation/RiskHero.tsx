import { motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import { Panel } from "@/components/ui/Panel";
import { RiskScore } from "@/components/ui/RiskScore";
import { ThreatBadge } from "@/components/ui/ThreatBadge";
import type { RiskAssessment } from "@/types/analysis";

export function RiskHero({ risk }: { risk: RiskAssessment }) {
  return (
    <Panel sweep className="p-6 lg:p-8">
      <div className="flex flex-col items-center gap-8 lg:flex-row lg:items-center lg:gap-12">
        <RiskScore score={risk.score} level={risk.level} />

        <div className="min-w-0 flex-1">
          <p className="font-mono text-[10px] uppercase tracking-[0.28em] text-accent">
            Threat Classification
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {risk.classification.map((item, i) => (
              <motion.div
                key={item}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.15 + i * 0.07 }}
              >
                <ThreatBadge label={item} tone={i === 0 ? "danger" : "warning"} />
              </motion.div>
            ))}
          </div>

          <p className="mt-5 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            {risk.summary}
          </p>

          <div className="mt-6 inline-flex items-center gap-2 rounded-sm border border-danger/30 bg-danger/10 px-3 py-2">
            <AlertTriangle className="h-3.5 w-3.5 text-danger" />
            <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-danger">
              {risk.indicator_count} Threat Indicators Detected
            </span>
          </div>
        </div>
      </div>
    </Panel>
  );
}
