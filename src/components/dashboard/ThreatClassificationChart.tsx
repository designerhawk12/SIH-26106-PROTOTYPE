import { motion } from "framer-motion";
import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import type { DashboardStats } from "@/types/analysis";

export function ThreatClassificationChart({ data }: { data: DashboardStats["classification_breakdown"] }) {
  const max = Math.max(...data.map((d) => d.count), 1);

  return (
    <Panel interactive className="h-full p-5">
      <SectionHeader eyebrow="Distribution" title="Threat Classification" />
      <div className="mt-6 space-y-4">
        {data.map((item, i) => (
          <div key={item.label}>
            <div className="mb-1.5 flex items-center justify-between text-xs">
              <span className="text-foreground/85">{item.label}</span>
              <span className="font-mono text-muted-foreground">{item.count}</span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted/60">
              <motion.div
                className="h-full rounded-full bg-accent/80"
                initial={{ width: 0 }}
                animate={{ width: `${(item.count / max) * 100}%` }}
                transition={{ duration: 0.9, delay: 0.1 + i * 0.08, ease: [0.22, 1, 0.36, 1] }}
              />
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}
