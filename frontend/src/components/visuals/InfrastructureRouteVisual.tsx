import { motion } from "framer-motion";
import { Building2, Globe2, Server } from "lucide-react";
import { DataPulse } from "@/components/effects/DataPulse";
import { Panel } from "@/components/ui/Panel";
import { ThreatBadge, reputationTone } from "@/components/ui/ThreatBadge";
import { useReducedMotionPreference } from "@/hooks/useReducedMotionPreference";
import type { InfrastructureNode } from "@/types/analysis";

export function InfrastructureRouteVisual({ nodes }: { nodes: InfrastructureNode[] }) {
  const reduceMotion = useReducedMotionPreference();

  return (
    <Panel className="overflow-x-auto p-5" spotlight>
      <div className="relative grid min-w-[720px] grid-flow-col auto-cols-fr items-start gap-8 pt-2">
        <motion.div
          aria-hidden
          className="absolute left-[8%] right-[8%] top-8 h-px origin-left bg-gradient-to-r from-network/30 via-network to-network/30"
          initial={{ scaleX: reduceMotion ? 1 : 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        />
        <DataPulse className="left-[29%] top-[29px] bg-network" />
        <DataPulse className="left-[62%] top-[29px] bg-network" delay={0.8} />
        {nodes.map((node, index) => {
          const Icon = index === 0 ? Server : index === nodes.length - 1 ? Building2 : Globe2;
          return (
            <motion.div
              key={node.ip}
              className="relative z-10 min-w-0 text-center"
              initial={{ opacity: 0, y: reduceMotion ? 0 : 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.38 }}
            >
              <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-sm border border-network/40 bg-surface-raised text-network shadow-[0_0_24px_-12px_var(--network)]">
                <Icon className="h-4 w-4" />
              </span>
              <p className="mt-3 font-mono text-xs text-network">{node.ip}</p>
              <p className="mt-1 text-[11px] text-muted-foreground">
                {node.city ?? "Unknown city"}, {node.country ?? "Unknown country"}
              </p>
              <p className="mt-1 truncate font-mono text-[10px] text-foreground/70">
                {node.asn ?? "ASN unknown"} · {node.isp ?? "ISP unknown"}
              </p>
              <div className="mt-2 flex justify-center">
                <ThreatBadge label={node.reputation} tone={reputationTone(node.reputation)} />
              </div>
            </motion.div>
          );
        })}
      </div>
    </Panel>
  );
}
