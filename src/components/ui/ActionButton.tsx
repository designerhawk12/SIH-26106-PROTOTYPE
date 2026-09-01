import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost";

interface ActionButtonProps {
  children: ReactNode;
  variant?: Variant;
  icon?: ReactNode;
  /** Show a trailing arrow that nudges on hover. */
  arrow?: boolean;
  disabled?: boolean;
  type?: "button" | "submit";
  className?: string;
  onClick?: (() => void) | undefined;
}

const variants: Record<Variant, string> = {
  primary:
    "bg-accent text-accent-foreground font-bold hover:brightness-110 hover:shadow-[0_0_28px_-6px_rgba(215,255,63,0.55)]",
  secondary:
    "bg-surface text-foreground border border-border hover:border-accent/60 hover:bg-surface-hover",
  ghost: "text-muted-foreground hover:text-foreground hover:bg-surface-hover",
};

export function ActionButton({
  children,
  variant = "primary",
  icon,
  arrow = false,
  disabled = false,
  type = "button",
  className,
  onClick,
}: ActionButtonProps) {
  return (
    <motion.button
      type={type}
      disabled={disabled}
      onClick={onClick}
      {...(disabled ? {} : { whileHover: { scale: 1.02 }, whileTap: { scale: 0.985 } })}
      transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        "group inline-flex items-center gap-2 rounded-sm px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.12em]",
        "transition-colors duration-200 disabled:cursor-not-allowed disabled:opacity-40",
        variants[variant],
        className,
      )}
    >
      {icon}
      <span>{children}</span>
      {arrow && (
        <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-1" />
      )}
    </motion.button>
  );
}
