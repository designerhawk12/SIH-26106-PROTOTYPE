import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { Panel } from "@/components/ui/Panel";
import { CountUp } from "@/components/ui/RiskScore";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: number;
  icon: LucideIcon;
  delta?: string;
  tone?: "accent" | "danger" | "warning" | "network" | "ai" | "neutral";
  index?: number;
  className?: string;
}

const toneText: Record<NonNullable<StatCardProps["tone"]>, string> = {
  accent: "text-accent",
  danger: "text-danger",
  warning: "text-warning",
  network: "text-network",
  ai: "text-ai",
  neutral: "text-muted-foreground",
};

export function StatCard({
  label,
  value,
  icon: Icon,
  delta,
  tone = "neutral",
  index = 0,
  className,
}: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05, ease: [0.22, 1, 0.36, 1] }}
    >
      <Panel interactive spotlight className={cn("h-full p-5", className)}>
        <div className="flex items-start justify-between">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            {label}
          </p>
          <Icon className={cn("h-4 w-4", toneText[tone])} />
        </div>
        <CountUp
          value={value}
          className="mt-6 block text-3xl font-bold tracking-tight text-foreground"
        />
        {delta && <p className="mt-1 font-mono text-[11px] text-muted-foreground">{delta}</p>}
      </Panel>
    </motion.div>
  );
}
