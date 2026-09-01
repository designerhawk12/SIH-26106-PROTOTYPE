import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/types/analysis";

const levelColor: Record<RiskLevel, string> = {
  LOW: "var(--success)",
  MEDIUM: "var(--warning)",
  HIGH: "var(--warning)",
  CRITICAL: "var(--danger)",
};

const levelText: Record<RiskLevel, string> = {
  LOW: "text-success",
  MEDIUM: "text-warning",
  HIGH: "text-danger",
  CRITICAL: "text-danger",
};

/** Animated count-up used for scores and statistics. */
export function CountUp({ value, className }: { value: number; className?: string }) {
  const motionValue = useMotionValue(0);
  const spring = useSpring(motionValue, { duration: 1200, bounce: 0 });
  const rounded = useTransform(spring, (latest) => Math.round(latest).toLocaleString("en-US"));
  const [display, setDisplay] = useState("0");

  useEffect(() => {
    motionValue.set(value);
    return rounded.on("change", (latest) => setDisplay(latest));
  }, [motionValue, rounded, value]);

  return <span className={className}>{display}</span>;
}

interface RiskScoreProps {
  score: number;
  level: RiskLevel;
  size?: number;
  className?: string;
}

/** Animated circular risk indicator. */
export function RiskScore({ score, level, size = 190, className }: RiskScoreProps) {
  const stroke = 8;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const color = levelColor[level];

  return (
    <div className={cn("relative", className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="oklch(1 0 0 / 8%)"
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
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference * (1 - score / 100) }}
          transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
          style={{ filter: `drop-shadow(0 0 10px ${color})` }}
        />
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
