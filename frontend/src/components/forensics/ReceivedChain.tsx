import { motion } from "framer-motion";
import { Server } from "lucide-react";
import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatDateTime } from "@/lib/format";
import type { ReceivedHop } from "@/types/analysis";

export function ReceivedChain({ hops }: { hops: ReceivedHop[] }) {
  return (
    <Panel spotlight tone="network" className="p-6">
      <SectionHeader eyebrow="Routing" title="Received Header Chain" />
      <div className="mt-6 space-y-0">
        {hops.map((hop, i) => (
          <motion.div
            key={hop.index}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: i * 0.08 }}
            className="relative flex gap-4 pb-6 last:pb-0"
          >
            {i < hops.length - 1 && (
              <motion.span
                className="absolute left-[15px] top-8 h-full w-px origin-top bg-gradient-to-b from-network/70 to-border"
                initial={{ scaleY: 0 }}
                animate={{ scaleY: 1 }}
                transition={{ duration: 0.45, delay: 0.18 + i * 0.08 }}
              />
            )}
            <span className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border border-network/30 bg-surface shadow-[0_0_20px_-12px_var(--network)]">
              <Server className="h-3.5 w-3.5 text-network" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-mono text-xs text-foreground/90">
                <span className="text-muted-foreground">from</span> {hop.from_host}
              </p>
              <p className="font-mono text-xs text-foreground/90">
                <span className="text-muted-foreground">by</span> {hop.by_host}
              </p>
              <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                {hop.ip ?? "—"} · {hop.protocol ?? "—"} · {formatDateTime(hop.timestamp)}
              </p>
            </div>
          </motion.div>
        ))}
      </div>
    </Panel>
  );
}
