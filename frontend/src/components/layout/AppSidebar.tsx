import { Link, useRouterState } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  Activity,
  ChevronsLeft,
  ChevronsRight,
  FileText,
  FolderSearch,
  LayoutDashboard,
  Radar,
  ScanLine,
  Settings,
  ShieldCheck,
} from "lucide-react";
import { useState } from "react";
import { useReducedMotionPreference } from "@/hooks/useReducedMotionPreference";
import { cn } from "@/lib/utils";

const primaryNav = [
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
  { label: "Analyze Email", to: "/analyze", icon: ScanLine },
  { label: "Investigations", to: "/cases", icon: FolderSearch },
  { label: "Threat Intelligence", to: "/threat-intelligence", icon: Radar },
  { label: "Reports", to: "/reports", icon: FileText },
] as const;

const secondaryNav = [
  { label: "System Status", to: "/system-status", icon: Activity },
  { label: "Settings", to: "/settings", icon: Settings },
] as const;

export function AppSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const reduceMotion = useReducedMotionPreference();

  const isActive = (to: string) => pathname === to || pathname.startsWith(`${to}/`);

  const renderItem = (item: { label: string; to: string; icon: typeof Radar }) => {
    const active = isActive(item.to);
    const Icon = item.icon;
    return (
      <Link
        key={item.to}
        to={item.to}
        className={cn(
          "group relative flex items-center gap-3 rounded-sm px-3 py-2.5 text-sm transition-colors duration-200",
          active
            ? "bg-surface-hover text-foreground"
            : "text-muted-foreground hover:bg-surface hover:text-foreground",
        )}
      >
        {active && (
          <motion.span
            layoutId="nav-indicator"
            className="absolute left-0 top-1/2 h-6 w-[2px] -translate-y-1/2 rounded-full bg-accent shadow-[0_0_12px_2px_rgba(215,255,63,0.5)]"
            transition={{ duration: reduceMotion ? 0 : 0.28, ease: [0.22, 1, 0.36, 1] }}
          />
        )}
        <Icon
          className={cn(
            "h-4 w-4 shrink-0 transition-all duration-200",
            active
              ? "translate-x-0.5 text-accent"
              : "text-muted-foreground group-hover:translate-x-0.5 group-hover:text-foreground",
          )}
        />
        {!collapsed && <span className="max-md:hidden truncate">{item.label}</span>}
      </Link>
    );
  };

  return (
    <aside
      className={cn(
        "sticky top-0 z-30 flex h-screen shrink-0 flex-col border-r border-border bg-background/95 backdrop-blur transition-[width] duration-300 max-md:w-[68px]",
        collapsed ? "w-[68px]" : "w-[248px]",
      )}
    >
      <Link
        to="/"
        aria-label="Sentinel MX Forensic Intel home"
        className="flex cursor-pointer items-center gap-2.5 px-4 py-5"
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-sm bg-accent">
          <ShieldCheck className="h-4 w-4 text-accent-foreground" />
        </span>
        {!collapsed && (
          <div className="min-w-0 max-md:hidden">
            <p className="truncate text-sm font-bold tracking-tight">SENTINEL MX</p>
            <p className="truncate font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
              Forensic Intel
            </p>
          </div>
        )}
      </Link>

      <nav className="flex flex-1 flex-col gap-1 px-2.5">
        {!collapsed && (
          <p className="px-3 pb-2 pt-3 font-mono text-[10px] uppercase tracking-[0.24em] text-muted-foreground/70 max-md:hidden">
            Operations
          </p>
        )}
        {primaryNav.map(renderItem)}
      </nav>

      <div className="flex flex-col gap-1 border-t border-border px-2.5 py-3">
        {secondaryNav.map(renderItem)}
        <button
          type="button"
          onClick={() => setCollapsed((v) => !v)}
          className="mt-1 flex items-center gap-3 rounded-sm px-3 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-surface hover:text-foreground"
        >
          {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
          {!collapsed && <span className="max-md:hidden">Collapse</span>}
        </button>
      </div>
    </aside>
  );
}
