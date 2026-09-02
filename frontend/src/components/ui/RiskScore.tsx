import { motion, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { useReducedMotionPreference } from "@/hooks/useReducedMotionPreference";
import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/types/analysis";

const levelColor: Record<RiskLevel, string> = {
  LOW: "var(--success)",
  MEDIUM: "var(--warning)",
  HIGH: "var(--danger)",
  CRITICAL: "var(--danger)",
};

const levelText: Record<RiskLevel, string> = {
  LOW: "text-success",
  MEDIUM: "text-warning",
  HIGH: "text-danger",
  CRITICAL: "text-danger",
};

/** Viewport-deferred count-up used for scores and operational statistics. */
export function CountUp({ value, className }: { value: number; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const visible = useInView(ref, { once: true, amount: 0.6 });
  const reduceMotion = useReducedMotionPreference();
  const [display, setDisplay] = useState(reduceMotion ? value : 0);

  useEffect(() => {
    if (!visible) return;
    if (reduceMotion) {
      setDisplay(value);
      return;
    }

    const startedAt = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const progress = Math.min((now - startedAt) / 760, 1);
      const eased = 1 - (1 - progress) ** 4;
      setDisplay(Math.round(value * eased));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [reduceMotion, value, visible]);

  return (
    <span ref={ref} className={className}>
      {display.toLocaleString("en-US")}
    </span>
  );
}

interface RiskScoreProps {
  score: number;
  level: RiskLevel;
  size?: number;
  className?: string;
}

/** Technical SVG risk gauge with ticks, controlled glow, and reduced-motion behavior. */
export function RiskScore({ score, level, size = 190, className }: RiskScoreProps) {
  const ref = useRef<HTMLDivElement>(null);
  const visible = useInView(ref, { once: true, amount: 0.45 });
  const reduceMotion = useReducedMotionPreference();
  const stroke = 7;
  const radius = (size - 22) / 2;
  const circumference = 2 * Math.PI * radius;
  const color = levelColor[level];
  const normalizedScore = Math.max(0, Math.min(score, 100));
  const markerAngle = (normalizedScore / 100) * Math.PI * 2 - Math.PI / 2;
  const markerX = size / 2 + Math.cos(markerAngle) * radius;
  const markerY = size / 2 + Math.sin(markerAngle) * radius;

  return (
    <div ref={ref} className={cn("relative", className)} style={{ width: size, height: size }}>
      <div className="pointer-events-none absolute inset-[18%] rounded-full bg-danger/[0.055] blur-2xl" />
      <svg width={size} height={size} className="relative overflow-visible" aria-hidden>
        {Array.from({ length: 24 }, (_, index) => {
          const angle = (index / 24) * Math.PI * 2 - Math.PI / 2;
          const outer = radius + 8;
          const inner = radius + (index % 3 === 0 ? 2 : 4);
          return (
            <line
              key={index}
              x1={size / 2 + Math.cos(angle) * inner}
              y1={size / 2 + Math.sin(angle) * inner}
              x2={size / 2 + Math.cos(angle) * outer}
              y2={size / 2 + Math.sin(angle) * outer}
              stroke="var(--border-strong)"
              strokeWidth={index % 3 === 0 ? 1.5 : 1}
              opacity={index % 3 === 0 ? 0.9 : 0.55}
            />
          );
        })}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="oklch(1 0 0 / 7%)"
          strokeWidth={stroke}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          initial={{ strokeDashoffset: circumference }}
          animate={{
            strokeDashoffset:
              visible || reduceMotion ? circumference * (1 - normalizedScore / 100) : circumference,
          }}
          transition={{ duration: reduceMotion ? 0 : 1.05, ease: [0.16, 1, 0.3, 1] }}
          style={{ filter: `drop-shadow(0 0 7px ${color})` }}
        />
        {(visible || reduceMotion) && (
          <motion.circle
            cx={markerX}
            cy={markerY}
            r="3"
            fill={color}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: reduceMotion ? 0 : 0.7, duration: 0.25 }}
            style={{ filter: `drop-shadow(0 0 6px ${color})` }}
          />
        )}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="flex items-baseline">
          <CountUp
            value={score}
            className="text-5xl font-bold leading-none tracking-tighter text-foreground"
          />
          <span className="ml-1 font-mono text-xs text-muted-foreground">/100</span>
        </div>
        <p
          className={cn(
            "mt-2 font-mono text-[11px] font-semibold uppercase tracking-[0.24em]",
            levelText[level],
          )}
        >
          {level} RISK
        </p>
      </div>
    </div>
  );
}
