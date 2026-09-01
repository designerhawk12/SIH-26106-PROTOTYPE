import { motion } from "framer-motion";
import { Panel } from "@/components/ui/Panel";
import { cn } from "@/lib/utils";
import type { AuthenticationCheck } from "@/types/analysis";

const resultColor = {
  PASS: "text-success",
  FAIL: "text-danger",
  UNKNOWN: "text-muted-foreground",
} as const;

interface Props {
  name: "SPF" | "DKIM" | "DMARC";
  check: AuthenticationCheck;
  index?: number;
}

export function AuthenticationCard({ name, check, index = 0 }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08, ease: [0.22, 1, 0.36, 1] }}
    >
      <Panel interactive className="h-full p-6">
        <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-muted-foreground">
          {name}
        </p>
        <p
          className={cn(
            "mt-4 text-4xl font-bold tracking-tight",
            resultColor[check.result],
          )}
        >
          {check.result}
        </p>
        {check.domain && (
          <p className="mt-2 truncate font-mono text-[11px] text-muted-foreground">
            {check.domain}
          </p>
        )}
        <p className="mt-4 text-xs leading-relaxed text-muted-foreground">{check.explanation}</p>
      </Panel>
    </motion.div>
  );
}
