import { motion } from "framer-motion";
import { useReducedMotionPreference } from "@/hooks/useReducedMotionPreference";
import { cn } from "@/lib/utils";

export function DataPulse({ className, delay = 0 }: { className?: string; delay?: number }) {
  const reduceMotion = useReducedMotionPreference();

  return (
    <motion.span
      aria-hidden
      className={cn(
        "absolute h-1.5 w-1.5 rounded-full bg-accent shadow-[0_0_10px_var(--accent)]",
        className,
      )}
      {...(!reduceMotion ? { animate: { opacity: [0, 1, 0], scale: [0.65, 1.15, 0.65] } } : {})}
      transition={{ duration: 1.8, delay, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}
