import { ShieldCheck, UserRound } from "lucide-react";

import { useAuth } from "@/auth/AuthProvider";
import { ActionButton } from "@/components/ui/ActionButton";
import { Panel } from "@/components/ui/Panel";

function formatRole(role: string | null) {
  return role?.replaceAll("_", " ") ?? "Unavailable";
}

export function ProfilePage() {
  const { user, profile, role, error, refreshProfile, hasPermission } = useAuth();
  const displayName = profile?.display_name || user?.email || "Authenticated user";
  const email = profile?.email || user?.email || "Email unavailable";

  return (
    <div className="mx-auto max-w-[900px]">
      <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-accent">Identity</p>
      <h1 className="mt-3 text-4xl font-bold tracking-tight lg:text-5xl">Profile & Settings</h1>
      <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
        Your identity is authenticated by Supabase. Application permissions are assigned by Sentinel
        MX administrators.
      </p>

      <div className="mt-8 grid gap-4 md:grid-cols-[1.2fr_0.8fr]">
        <Panel className="p-6">
          <div className="flex items-start gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md border border-accent/30 bg-accent/10">
              <UserRound className="h-5 w-5 text-accent" />
            </span>
            <div className="min-w-0">
              <h2 className="truncate text-lg font-semibold">{displayName}</h2>
              <p className="mt-1 truncate text-sm text-muted-foreground">{email}</p>
            </div>
          </div>

          <dl className="mt-7 grid gap-5 border-t border-border pt-6 sm:grid-cols-2">
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                Role
              </dt>
              <dd className="mt-2 text-sm font-semibold">{formatRole(role)}</dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                Organization / Team
              </dt>
              <dd className="mt-2 text-sm">{profile?.organization || "Not provided"}</dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                User ID
              </dt>
              <dd className="mt-2 break-all font-mono text-xs text-muted-foreground">
                {profile?.user_id ?? user?.id ?? "Unavailable"}
              </dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                Member since
              </dt>
              <dd className="mt-2 text-sm">
                {profile?.created_at
                  ? new Date(profile.created_at).toLocaleDateString()
                  : "Unavailable"}
              </dd>
            </div>
          </dl>

          {!profile && (
            <div className="mt-6 border-t border-border pt-5">
              <p className="text-xs leading-relaxed text-warning">
                {error ?? "The application profile is temporarily unavailable."}
              </p>
              <ActionButton
                variant="secondary"
                className="mt-3"
                onClick={() => void refreshProfile()}
              >
                Retry profile
              </ActionButton>
            </div>
          )}
        </Panel>

        <Panel className="p-6">
          <ShieldCheck className="h-5 w-5 text-accent" />
          <h2 className="mt-4 text-sm font-semibold">Authorized capabilities</h2>
          <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
            These permissions come from the backend role assignment and cannot be changed from this
            profile.
          </p>
          <ul className="mt-5 space-y-2 text-xs text-muted-foreground">
            {(profile?.permissions ?? []).map((permission) => (
              <li
                key={permission}
                className="rounded-sm border border-border bg-background px-3 py-2 font-mono"
              >
                {permission.replaceAll("_", " ")}
              </li>
            ))}
            {!profile && <li>Permission details unavailable.</li>}
          </ul>
          {hasPermission("MANAGE_USERS") && (
            <p className="mt-5 border-t border-border pt-4 text-xs text-accent">
              Administrator user-management access is enabled.
            </p>
          )}
        </Panel>
      </div>
    </div>
  );
}
