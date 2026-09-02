import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface CopyValueProps {
  value: string;
  /** Visually truncate long hashes while still copying the full value. */
  truncate?: boolean;
  className?: string;
  revealOnRowHover?: boolean;
}

export function CopyValue({
  value,
  truncate = false,
  className,
  revealOnRowHover = false,
}: CopyValueProps) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  return (
    <span className={cn("group inline-flex max-w-full items-center gap-2", className)}>
      <span
        className={cn("font-mono text-xs text-foreground/85", truncate && "block truncate")}
        title={value}
      >
        {value}
      </span>
      <button
        type="button"
        onClick={copy}
        aria-label="Copy to clipboard"
        className={cn(
          "shrink-0 rounded-sm border border-border p-1 text-muted-foreground transition-all duration-200 hover:border-accent/60 hover:text-accent focus-visible:opacity-100",
          revealOnRowHover && "opacity-0 group-hover/ioc:opacity-100",
        )}
      >
        {copied ? <Check className="h-3 w-3 text-accent" /> : <Copy className="h-3 w-3" />}
      </button>
    </span>
  );
}
