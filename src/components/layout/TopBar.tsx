import { Bell, Search, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";

/** Top status strip: clock, system status, analyst identity. */
export function TopBar() {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between gap-4 border-b border-border bg-background/80 px-5 backdrop-blur lg:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <div className="hidden items-center gap-2 rounded-sm border border-border bg-surface px-3 py-1.5 md:flex">
          <Search className="h-3.5 w-3.5 text-muted-foreground" />
          <input
            placeholder="Search cases, senders, indicators"
            className="w-64 bg-transparent text-xs text-foreground outline-none placeholder:text-muted-foreground"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden items-center gap-2 font-mono text-[11px] text-muted-foreground sm:flex">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success/70" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-success" />
          </span>
          ALL SYSTEMS OPERATIONAL
        </div>
        <span className="hidden font-mono text-[11px] text-muted-foreground lg:block">
          {now ? now.toUTCString().replace("GMT", "UTC") : "—"}
        </span>
        <button
          type="button"
          className="rounded-sm border border-border p-1.5 text-muted-foreground transition-colors hover:border-accent/50 hover:text-accent"
          aria-label="Notifications"
        >
          <Bell className="h-3.5 w-3.5" />
        </button>
        <div className="flex items-center gap-2 border-l border-border pl-4">
          <span className="flex h-7 w-7 items-center justify-center rounded-sm bg-surface-hover">
            <ShieldCheck className="h-3.5 w-3.5 text-accent" />
          </span>
          <div className="hidden leading-tight sm:block">
            <p className="text-xs font-semibold">R. Mehta</p>
            <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Tier 2 Analyst
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
