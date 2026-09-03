import { useNavigate, useRouterState } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useEffect, type ReactNode } from "react";
import { useAuth } from "@/auth/AuthProvider";
import { useReducedMotionPreference } from "@/hooks/useReducedMotionPreference";
import { AppSidebar } from "./AppSidebar";
import { TopBar } from "./TopBar";

/** Standard analyst workstation layout: sidebar + top bar + scrollable content. */
export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const navigate = useNavigate();
  const { session, profile, loading, error } = useAuth();
  const reduceMotion = useReducedMotionPreference();

  useEffect(() => {
    if (!loading && !session) {
      void navigate({ to: "/login", replace: true });
    }
  }, [loading, navigate, session]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background font-mono text-xs uppercase tracking-[0.24em] text-muted-foreground">
        Restoring secure session…
      </div>
    );
  }

  if (!session) return null;

  return (
    <div className="bg-noise relative flex min-h-screen bg-background">
      <div className="bg-grid pointer-events-none fixed inset-0 opacity-[0.5]" />
      <div className="pointer-events-none fixed left-1/2 top-0 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-accent/[0.045] blur-[140px]" />
      <div className="pointer-events-none fixed -right-64 top-1/3 h-[620px] w-[620px] rounded-full bg-network/[0.025] blur-[150px]" />
      <AppSidebar />
      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        <TopBar />
        {!profile && (
          <div
            role="status"
            className="border-b border-warning/30 bg-warning/5 px-5 py-2 text-xs text-warning lg:px-8"
          >
            {error ?? "Your application profile is temporarily unavailable."} Session identity is
            shown as a safe fallback.
          </div>
        )}
        <motion.main
          key={pathname}
          initial={reduceMotion ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0 : 0.28, ease: [0.16, 1, 0.3, 1] }}
          className="flex-1 px-4 pb-16 pt-6 sm:px-5 lg:px-8"
        >
          {children}
        </motion.main>
      </div>
    </div>
  );
}
