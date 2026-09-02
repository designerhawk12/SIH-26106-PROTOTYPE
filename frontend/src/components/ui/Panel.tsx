import { motion, useMotionValue, useSpring, type HTMLMotionProps } from "framer-motion";
import { useEffect, useRef, type ReactNode } from "react";
import { AnimatedBorder } from "@/components/effects/AnimatedBorder";
import { useReducedMotionPreference } from "@/hooks/useReducedMotionPreference";
import { cn } from "@/lib/utils";

type PanelProps = Omit<HTMLMotionProps<"div">, "children"> & {
  children?: ReactNode;
  /** Enable hover lift + border illumination. */
  interactive?: boolean;
  /** Enable a mouse-following spotlight highlight. */
  spotlight?: boolean;
  /** Add restrained perspective response on pointer-capable devices. */
  tilt?: boolean;
  /** Show a slow animated lime border sweep (use sparingly). */
  sweep?: boolean;
  /** Color used by the local spotlight. */
  tone?: "accent" | "network" | "ai" | "danger" | "success";
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
  tilt = false,
  sweep = false,
  tone = "accent",
  onPointerMove,
  onPointerLeave,
  style,
  ...props
}: PanelProps) {
  const ref = useRef<HTMLDivElement>(null);
  const animationFrame = useRef<number | null>(null);
  const reduceMotion = useReducedMotionPreference();
  const rotateXValue = useMotionValue(0);
  const rotateYValue = useMotionValue(0);
  const rotateX = useSpring(rotateXValue, { stiffness: 170, damping: 24, mass: 0.5 });
  const rotateY = useSpring(rotateYValue, { stiffness: 170, damping: 24, mass: 0.5 });
  const spotlightColor = `var(--${tone})`;

  useEffect(
    () => () => {
      if (animationFrame.current !== null) cancelAnimationFrame(animationFrame.current);
    },
    [],
  );

  return (
    <motion.div
      ref={ref}
      onPointerMove={(event) => {
        onPointerMove?.(event);
        if ((!spotlight && !tilt) || reduceMotion || event.pointerType === "touch") return;
        const element = event.currentTarget;
        const clientX = event.clientX;
        const clientY = event.clientY;
        if (animationFrame.current !== null) cancelAnimationFrame(animationFrame.current);
        animationFrame.current = requestAnimationFrame(() => {
          const rect = element.getBoundingClientRect();
          const x = clientX - rect.left;
          const y = clientY - rect.top;
          element.style.setProperty("--spot-x", `${x}px`);
          element.style.setProperty("--spot-y", `${y}px`);
          if (tilt) {
            rotateXValue.set((y / rect.height - 0.5) * -2 * 2.2);
            rotateYValue.set((x / rect.width - 0.5) * 2 * 2.8);
          }
        });
      }}
      onPointerLeave={(event) => {
        onPointerLeave?.(event);
        rotateXValue.set(0);
        rotateYValue.set(0);
      }}
      {...(interactive && !reduceMotion ? { whileHover: { y: -3 } } : {})}
      transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
      style={{
        ...style,
        ...(tilt && !reduceMotion
          ? { rotateX, rotateY, transformPerspective: 900, transformStyle: "preserve-3d" }
          : {}),
      }}
      className={cn(
        "group/surface relative overflow-hidden rounded-md border border-border bg-surface",
        "shadow-[0_1px_0_0_rgba(255,255,255,0.03)_inset,0_12px_30px_-18px_rgba(0,0,0,0.9)]",
        interactive &&
          "transition-colors duration-300 hover:border-border-strong hover:shadow-[0_0_0_1px_rgba(215,255,63,0.14),0_18px_46px_-24px_rgba(215,255,63,0.28)]",
        className,
      )}
      {...props}
    >
      {sweep && <AnimatedBorder />}
      {spotlight && (
        <span
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover/surface:opacity-100"
          style={{
            background: `radial-gradient(320px circle at var(--spot-x, 50%) var(--spot-y, 50%), color-mix(in oklch, ${spotlightColor} 10%, transparent), transparent 68%)`,
          }}
        />
      )}
      {children}
    </motion.div>
  );
}
