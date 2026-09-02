import { motion } from "framer-motion";
import type { TimelineEvent as TimelineEventType } from "@/types/analysis";

interface Props {
  event: TimelineEventType;
  index: number;
  isLast: boolean;
}

export function TimelineEvent({ event, index, isLast }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08, ease: [0.22, 1, 0.36, 1] }}
      className="relative flex gap-5 pb-6 last:pb-0"
    >
      {!isLast && (
        <motion.span
          className="absolute left-[5px] top-4 h-full w-px origin-top bg-gradient-to-b from-accent/60 to-border"
          initial={{ scaleY: 0 }}
          animate={{ scaleY: 1 }}
          transition={{ duration: 0.42, delay: 0.15 + index * 0.08 }}
        />
      )}
      <span className="relative z-10 mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-accent shadow-[0_0_10px_2px_rgba(215,255,63,0.35)]" />
      <div className="min-w-0">
        <p className="font-mono text-[11px] text-accent">{event.timestamp}</p>
        <p className="mt-0.5 text-sm text-foreground/90">{event.label}</p>
        {event.detail && <p className="mt-0.5 text-xs text-muted-foreground">{event.detail}</p>}
      </div>
    </motion.div>
  );
}
