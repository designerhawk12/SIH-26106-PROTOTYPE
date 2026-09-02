import { motion } from "framer-motion";
import { useReducedMotionPreference } from "@/hooks/useReducedMotionPreference";
import { cn } from "@/lib/utils";

export function AnimatedBorder({ className }: { className?: string }) {
  const reduceMotion = useReducedMotionPreference();

  return (
    <span
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-0 overflow-hidden rounded-[inherit]",
        className,
      )}
    >
      <motion.span
        className="absolute inset-x-[-35%] top-0 h-px bg-gradient-to-r from-transparent via-accent/80 to-transparent"
        {...(!reduceMotion ? { animate: { x: ["-42%", "42%"] } } : {})}
        transition={{ duration: 3.2, repeat: Infinity, repeatDelay: 1.3, ease: "easeInOut" }}
      />
    </span>
  );
}
