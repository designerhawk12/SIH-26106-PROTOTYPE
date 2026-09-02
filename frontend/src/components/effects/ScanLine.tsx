import { motion } from "framer-motion";
import { useReducedMotionPreference } from "@/hooks/useReducedMotionPreference";
import { cn } from "@/lib/utils";

export function ScanLine({ active = true, className }: { active?: boolean; className?: string }) {
  const reduceMotion = useReducedMotionPreference();
  if (!active) return null;

  return (
    <motion.span
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-x-0 top-0 z-20 h-px bg-gradient-to-r from-transparent via-accent to-transparent shadow-[0_0_18px_2px_rgba(215,255,63,0.32)]",
        className,
      )}
      initial={{ opacity: 0.35, y: "0%" }}
      animate={reduceMotion ? { opacity: 0.5 } : { opacity: [0.2, 0.85, 0.2], y: ["0%", "280px"] }}
      transition={{ duration: 2.6, repeat: Infinity, ease: "linear" }}
    />
  );
}
