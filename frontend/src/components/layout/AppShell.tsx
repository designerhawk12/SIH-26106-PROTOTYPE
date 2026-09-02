import { useRouterState } from "@tanstack/react-router";
import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { useReducedMotionPreference } from "@/hooks/useReducedMotionPreference";
import { AppSidebar } from "./AppSidebar";
import { TopBar } from "./TopBar";

/** Standard analyst workstation layout: sidebar + top bar + scrollable content. */
export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const reduceMotion = useReducedMotionPreference();

  return (
    <div className="bg-noise relative flex min-h-screen bg-background">
      <div className="bg-grid pointer-events-none fixed inset-0 opacity-[0.5]" />
      <div className="pointer-events-none fixed left-1/2 top-0 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-accent/[0.045] blur-[140px]" />
      <div className="pointer-events-none fixed -right-64 top-1/3 h-[620px] w-[620px] rounded-full bg-network/[0.025] blur-[150px]" />
      <AppSidebar />
      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        <TopBar />
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
