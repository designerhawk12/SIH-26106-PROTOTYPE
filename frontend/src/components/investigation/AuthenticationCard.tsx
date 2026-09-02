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
      <Panel
        interactive
        spotlight
        tilt
        tone={check.result === "PASS" ? "success" : check.result === "FAIL" ? "danger" : "accent"}
        className={cn(
          "h-full p-6",
          check.result === "PASS" && "border-success/25",
          check.result === "FAIL" && "border-danger/30",
        )}
      >
        <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-muted-foreground">
          {name}
        </p>
        <p
          className={cn(
            "mt-4 inline-flex rounded-sm border border-current/20 bg-current/[0.04] px-2 py-1 text-3xl font-bold tracking-tight",
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
