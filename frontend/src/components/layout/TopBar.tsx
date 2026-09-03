import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { Bell, LogOut, Search, Settings, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "@/auth/AuthProvider";
import { getHealth } from "@/services/api";

/** Top status strip: clock, system status, analyst identity. */
export function TopBar() {
  const [now, setNow] = useState<Date | null>(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [signOutError, setSignOutError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { profile, role, signOut, user } = useAuth();
  const identity = profile?.display_name || user?.email || "Authenticated user";
  const email = profile?.email || user?.email || "Email unavailable";
  const health = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
    retry: 1,
  });

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
        <div
          className={`hidden items-center gap-2 font-mono text-[11px] sm:flex ${
            health.isError ? "text-danger" : "text-muted-foreground"
          }`}
        >
          <span className="relative flex h-1.5 w-1.5">
            {!health.isError && (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success/70" />
            )}
            <span
              className={`relative inline-flex h-1.5 w-1.5 rounded-full ${
                health.isError
                  ? "bg-danger"
                  : health.isPending
                    ? "bg-muted-foreground"
                    : "bg-success"
              }`}
            />
          </span>
          {health.isPending
            ? "CHECKING API"
            : health.isError
              ? "API UNAVAILABLE"
              : "API OPERATIONAL"}
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
        <div className="relative border-l border-border pl-4">
          <button
            type="button"
            onClick={() => setProfileOpen((open) => !open)}
            className="flex items-center gap-2 text-left"
            aria-expanded={profileOpen}
            aria-label="User profile menu"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-sm bg-surface-hover">
              <ShieldCheck className="h-3.5 w-3.5 text-accent" />
            </span>
            <span className="hidden leading-tight sm:block">
              <span className="block max-w-36 truncate text-xs font-semibold">{identity}</span>
              <span className="block font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                {role?.replaceAll("_", " ") ?? "Profile unavailable"}
              </span>
            </span>
          </button>
          {profileOpen && (
            <div className="absolute right-0 top-10 w-56 rounded-sm border border-border bg-surface p-2 shadow-xl">
              <p className="truncate px-2 py-1 text-xs font-medium text-foreground">{identity}</p>
              <p className="truncate px-2 pb-2 text-[11px] text-muted-foreground">{email}</p>
              <p className="border-y border-border px-2 py-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                Role: {role?.replaceAll("_", " ") ?? "Unavailable"}
              </p>
              <Link
                to="/settings"
                onClick={() => setProfileOpen(false)}
                className="mt-1 flex w-full items-center gap-2 rounded-sm px-2 py-2 text-xs text-foreground hover:bg-surface-hover"
              >
                <Settings className="h-3.5 w-3.5" />
                Profile / Settings
              </Link>
              <button
                type="button"
                onClick={() => {
                  setSignOutError(null);
                  void signOut()
                    .then(() => navigate({ to: "/login", replace: true }))
                    .catch(() => setSignOutError("Sign out could not be completed."));
                }}
                className="mt-1 flex w-full items-center gap-2 rounded-sm px-2 py-2 text-xs text-foreground hover:bg-surface-hover"
              >
                <LogOut className="h-3.5 w-3.5" />
                Sign out
              </button>
              {signOutError && (
                <p role="alert" className="px-2 py-1 text-[11px] text-danger">
                  {signOutError}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
