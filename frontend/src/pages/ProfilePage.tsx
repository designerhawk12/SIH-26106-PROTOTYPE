import { ShieldCheck, UserRound } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { useAuth } from "@/auth/AuthProvider";
import { ActionButton } from "@/components/ui/ActionButton";
import { Panel } from "@/components/ui/Panel";

function formatRole(role: string | null) {
  return role?.replaceAll("_", " ") ?? "Unavailable";
}

export function ProfilePage() {
  const { user, profile, role, error, refreshProfile, hasPermission, updateProfile } = useAuth();
  const displayName = profile?.display_name || user?.email || "Authenticated user";
  const email = profile?.email || user?.email || "Email unavailable";
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");
  const [organization, setOrganization] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setName(profile?.display_name ?? "");
    setOrganization(profile?.organization ?? "");
  }, [profile?.display_name, profile?.organization]);

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) {
      setSaveError("Display name is required.");
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      await updateProfile({
        display_name: trimmedName,
        organization: organization.trim() || null,
      });
      setEditing(false);
    } catch {
      setSaveError("Profile changes could not be saved. Please try again.");
    } finally {
      setSaving(false);
    }
  }

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

          {profile && (
            <div className="mt-7 border-t border-border pt-5">
              {!editing ? (
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold">Account details</h3>
                    <p className="mt-1 text-xs text-muted-foreground">
                      You may update your display name and organization. Your role is administrator-managed.
                    </p>
                  </div>
                  <ActionButton variant="secondary" onClick={() => setEditing(true)}>
                    Edit profile
                  </ActionButton>
                </div>
              ) : (
                <form className="space-y-4" onSubmit={(event) => void saveProfile(event)}>
                  <div>
                    <label className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground" htmlFor="display-name">
                      Display name
                    </label>
                    <input
                      id="display-name"
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      maxLength={120}
                      required
                      className="mt-2 w-full rounded-sm border border-border bg-background px-3 py-2 text-sm outline-none transition-colors focus:border-accent"
                    />
                  </div>
                  <div>
                    <label className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground" htmlFor="organization">
                      Organization / Team
                    </label>
                    <input
                      id="organization"
                      value={organization}
                      onChange={(event) => setOrganization(event.target.value)}
                      maxLength={160}
                      className="mt-2 w-full rounded-sm border border-border bg-background px-3 py-2 text-sm outline-none transition-colors focus:border-accent"
                    />
                  </div>
                  {saveError && <p role="alert" className="text-xs text-danger">{saveError}</p>}
                  <div className="flex flex-wrap gap-3">
                    <ActionButton type="submit" disabled={saving}>
                      {saving ? "Saving…" : "Save profile"}
                    </ActionButton>
                    <ActionButton
                      variant="ghost"
                      disabled={saving}
                      onClick={() => {
                        setName(profile.display_name);
                        setOrganization(profile.organization ?? "");
                        setSaveError(null);
                        setEditing(false);
                      }}
                    >
                      Cancel
                    </ActionButton>
                  </div>
                </form>
              )}
            </div>
          )}

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
            <div className="mt-5 border-t border-border pt-4 text-xs text-accent">
              <p>Administrator user-management access is enabled.</p>
              <p className="mt-1 text-muted-foreground">
                Role assignments are enforced by the backend and cannot be changed from this profile.
              </p>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
