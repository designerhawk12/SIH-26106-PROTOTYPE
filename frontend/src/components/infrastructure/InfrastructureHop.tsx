import { motion } from "framer-motion";
import { ArrowDown, Globe2 } from "lucide-react";
import { Panel } from "@/components/ui/Panel";
import { ThreatBadge, reputationTone } from "@/components/ui/ThreatBadge";
import type { InfrastructureNode } from "@/types/analysis";

interface Props {
  node: InfrastructureNode;
  isLast: boolean;
  index: number;
}

export function InfrastructureHop({ node, isLast, index }: Props) {
  const fields = [
    { label: "IP", value: node.ip, mono: true },
    { label: "Country", value: node.country ?? "—" },
    { label: "Region", value: node.region ?? "—" },
    { label: "City", value: node.city ?? "—" },
    { label: "ISP", value: node.isp ?? "—" },
    { label: "ASN", value: node.asn ?? "—", mono: true },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: index * 0.1, ease: [0.22, 1, 0.36, 1] }}
    >
      <Panel interactive spotlight tilt tone="network" className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-sm border border-network/30 bg-network/10">
              <Globe2 className="h-3.5 w-3.5 text-network" />
            </span>
            <div>
              <p className="text-sm font-semibold text-foreground">{node.role}</p>
              <p className="font-mono text-[11px] text-network">{node.ip}</p>
            </div>
          </div>
          <ThreatBadge label={node.reputation} tone={reputationTone(node.reputation)} />
        </div>

        <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-3 md:grid-cols-3 lg:grid-cols-6">
          {fields.map((field) => (
            <div key={field.label}>
              <dt className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                {field.label}
              </dt>
              <dd
                className={
                  field.mono
                    ? "mt-1 truncate font-mono text-xs text-foreground/85"
                    : "mt-1 truncate text-xs text-foreground/85"
                }
              >
                {field.value}
              </dd>
            </div>
          ))}
        </dl>
      </Panel>
      {!isLast && (
        <div className="flex justify-center py-2">
          <ArrowDown className="h-4 w-4 text-border-strong" />
        </div>
      )}
    </motion.div>
  );
}
