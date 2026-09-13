import { Link } from "@tanstack/react-router";
import { Construction, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

import { Panel } from "@/components/ui/Panel";
import { DEMO_MODE } from "@/config/demoMode";

interface UnderDevelopmentPageProps {
  moduleName: string;
}

export function UnderDevelopmentPage({ moduleName }: UnderDevelopmentPageProps) {
  return (
    <div className="mx-auto flex min-h-[calc(100vh-10rem)] max-w-[900px] items-center justify-center py-10">
      <Panel spotlight className="relative w-full overflow-hidden p-8 text-center sm:p-12">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(215,255,63,0.08),transparent_48%)]"
        />

        <div className="relative">
          <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-sm border border-accent/30 bg-accent/10 shadow-[0_0_30px_-12px_rgba(215,255,63,0.55)]">
            <Construction className="h-6 w-6 text-accent" />
          </span>
          <p className="mt-7 font-mono text-[10px] uppercase tracking-[0.3em] text-accent">
            {moduleName}
          </p>
          <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-5xl">
            UNDER DEVELOPMENT
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">
            This module is currently under active development and will be available in a future
            Sentinel MX release.
          </p>

          <Link
            to="/dashboard"
            className="group mx-auto mt-8 inline-flex items-center gap-2 rounded-sm bg-accent px-5 py-3 text-xs font-bold uppercase tracking-[0.12em] text-accent-foreground transition-[filter,box-shadow] hover:brightness-110 hover:shadow-[0_0_28px_-6px_rgba(215,255,63,0.55)]"
          >
            <ShieldCheck className="h-4 w-4" />
            Back to Dashboard
          </Link>
        </div>
      </Panel>
    </div>
  );
}

interface DemoModuleGateProps extends UnderDevelopmentPageProps {
  children: ReactNode;
}

/** Preserve the original module and render it whenever presentation mode is off. */
export function DemoModuleGate({ children, moduleName }: DemoModuleGateProps) {
  return DEMO_MODE ? <UnderDevelopmentPage moduleName={moduleName} /> : children;
}
