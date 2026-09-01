import { motion, type HTMLMotionProps } from "framer-motion";
import { useRef, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

type PanelProps = Omit<HTMLMotionProps<"div">, "children"> & {
  children?: ReactNode;
  /** Enable hover lift + border illumination. */
  interactive?: boolean;
  /** Enable a mouse-following spotlight highlight. */
  spotlight?: boolean;
  /** Show a slow animated lime border sweep (use sparingly). */
  sweep?: boolean;
};

/**
 * The core "technical module" surface used across the platform.
 * Nearly black fill, thin border, restrained hover motion.
 */
export function Panel({
  className,
  children,
  interactive = false,
  spotlight = false,
  sweep = false,
  ...props
}: PanelProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);

  return (
    <motion.div
      ref={ref}
      onMouseMove={
        spotlight
          ? (event) => {
              const rect = ref.current?.getBoundingClientRect();
              if (!rect) return;
              setPos({ x: event.clientX - rect.left, y: event.clientY - rect.top });
            }
          : undefined
      }
      onMouseLeave={spotlight ? () => setPos(null) : undefined}
      {...(interactive ? { whileHover: { y: -3 } } : {})}
      transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        "relative overflow-hidden rounded-md border border-border bg-surface",
        "shadow-[0_1px_0_0_rgba(255,255,255,0.03)_inset,0_12px_30px_-18px_rgba(0,0,0,0.9)]",
        interactive &&
          "transition-colors duration-300 hover:border-border-strong hover:shadow-[0_0_0_1px_rgba(215,255,63,0.14),0_18px_46px_-24px_rgba(215,255,63,0.28)]",
        className,
      )}
      {...props}
    >
      {sweep && (
        <span className="pointer-events-none absolute inset-x-0 top-0 h-px overflow-hidden">
          <span className="scan-line animate-sweep block h-px w-full opacity-70" />
        </span>
      )}
      {spotlight && pos && (
        <span
          aria-hidden
          className="pointer-events-none absolute h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full opacity-60 transition-opacity"
          style={{
            left: pos.x,
            top: pos.y,
            background:
              "radial-gradient(circle, oklch(0.92 0.21 118 / 8%) 0%, transparent 70%)",
          }}
        />
      )}
      {children}
    </motion.div>
  );
}
