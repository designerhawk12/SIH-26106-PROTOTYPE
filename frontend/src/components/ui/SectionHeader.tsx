import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  actions?: ReactNode;
  className?: string;
}

export function SectionHeader({
  title,
  subtitle,
  eyebrow,
  actions,
  className,
}: SectionHeaderProps) {
  return (
    <div className={cn("flex flex-wrap items-end justify-between gap-4", className)}>
      <div>
        {eyebrow && (
          <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.28em] text-accent">
            {eyebrow}
          </p>
        )}
        <h2 className="text-xl font-bold leading-tight tracking-tight text-foreground">{title}</h2>
        {subtitle && <p className="mt-1.5 max-w-2xl text-sm text-muted-foreground">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
