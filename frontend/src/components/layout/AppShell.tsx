import type { ReactNode } from "react";
import { AppSidebar } from "./AppSidebar";
import { TopBar } from "./TopBar";

/** Standard analyst workstation layout: sidebar + top bar + scrollable content. */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="relative flex min-h-screen bg-background">
      <div className="bg-grid pointer-events-none fixed inset-0 opacity-[0.5]" />
      <div className="pointer-events-none fixed left-1/2 top-0 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-accent/[0.045] blur-[140px]" />
      <AppSidebar />
      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        <TopBar />
        <main className="flex-1 px-5 pb-16 pt-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
