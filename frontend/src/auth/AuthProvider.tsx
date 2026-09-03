import type { Session, User } from "@supabase/supabase-js";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { supabase } from "@/integrations/supabase/client";
import { getCurrentUser } from "@/services/api";
import type { Permission, UserProfile, UserRole } from "@/types/auth";

interface SignUpResult {
  requiresEmailConfirmation: boolean;
}

interface AuthContextValue {
  session: Session | null;
  user: User | null;
  profile: UserProfile | null;
  role: UserRole | null;
  loading: boolean;
  error: string | null;
  hasPermission(permission: Permission): boolean;
  signIn(email: string, password: string): Promise<void>;
  signUp(email: string, password: string, displayName: string): Promise<SignUpResult>;
  signOut(): Promise<void>;
  refreshProfile(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function safeAuthMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message.includes("Missing Supabase environment")) {
    return "Authentication is not configured for this deployment.";
  }
  return fallback;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProfile = useCallback(async (nextSession: Session | null) => {
    setSession(nextSession);
    if (!nextSession) {
      setProfile(null);
      setError(null);
      return;
    }
    try {
      setProfile(await getCurrentUser());
      setError(null);
    } catch (loadError) {
      setProfile(null);
      setError(safeAuthMessage(loadError, "Your authenticated profile could not be loaded."));
    }
  }, []);

  useEffect(() => {
    let active = true;
    let unsubscribe: (() => void) | undefined;
    try {
      const auth = supabase.auth;
      void auth
        .getSession()
        .then(async ({ data, error: sessionError }) => {
          if (!active) return;
          if (sessionError) throw sessionError;
          await loadProfile(data.session);
        })
        .catch((sessionError: unknown) => {
          if (active) {
            setError(safeAuthMessage(sessionError, "The saved session could not be restored."));
          }
        })
        .finally(() => {
          if (active) setLoading(false);
        });

      const { data } = auth.onAuthStateChange((_event, nextSession) => {
        if (!active) return;
        setLoading(true);
        window.setTimeout(() => {
          void loadProfile(nextSession).finally(() => active && setLoading(false));
        }, 0);
      });
      unsubscribe = () => data.subscription.unsubscribe();
    } catch (configurationError) {
      setError(safeAuthMessage(configurationError, "Authentication could not be initialized."));
      setLoading(false);
    }

    return () => {
      active = false;
      unsubscribe?.();
    };
  }, [loadProfile]);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      user: session?.user ?? null,
      profile,
      role: profile?.role ?? null,
      loading,
      error,
      hasPermission(permission) {
        return profile?.permissions.includes(permission) ?? false;
      },
      async signIn(email, password) {
        const { data, error: signInError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (signInError || !data.session) {
          throw new Error("Unable to sign in with those credentials.");
        }
        await loadProfile(data.session);
      },
      async signUp(email, password, displayName) {
        const { data, error: signUpError } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { display_name: displayName } },
        });
        if (signUpError) throw new Error("Unable to create the account.");
        if (data.session) await loadProfile(data.session);
        return { requiresEmailConfirmation: !data.session };
      },
      async signOut() {
        const { error: signOutError } = await supabase.auth.signOut();
        if (signOutError) throw new Error("Unable to sign out.");
        setSession(null);
        setProfile(null);
        setError(null);
      },
      async refreshProfile() {
        await loadProfile(session);
      },
    }),
    [error, loadProfile, loading, profile, session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider.");
  return value;
}
