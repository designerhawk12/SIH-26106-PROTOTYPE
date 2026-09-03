import { Link, useNavigate } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { LockKeyhole, ShieldCheck } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "@/auth/AuthProvider";
import { ActionButton } from "@/components/ui/ActionButton";
import { Panel } from "@/components/ui/Panel";

export function LoginPage() {
  const navigate = useNavigate();
  const { session, loading, signIn, signUp } = useAuth();
  const [createAccount, setCreateAccount] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && session) void navigate({ to: "/dashboard" });
  }, [loading, navigate, session]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage(null);
    setFormError(null);
    try {
      if (createAccount) {
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
          throw new Error("Enter a valid email address.");
        }
        if (password.length < 8) {
          throw new Error("Password must contain at least 8 characters.");
        }
        if (password !== confirmPassword) {
          throw new Error("Passwords do not match.");
        }
        const result = await signUp(email.trim(), password, displayName.trim());
        if (result.requiresEmailConfirmation) {
          setMessage("Account created. Check your email to confirm your address, then sign in.");
        } else {
          await navigate({ to: "/dashboard" });
        }
      } else {
        await signIn(email.trim(), password);
        await navigate({ to: "/dashboard" });
      }
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Authentication failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="relative isolate flex min-h-screen items-center justify-center overflow-hidden bg-background px-6 py-12">
      <div className="bg-grid pointer-events-none absolute inset-0 opacity-60" />
      <div className="pointer-events-none absolute left-1/2 top-[-220px] h-[620px] w-[900px] -translate-x-1/2 rounded-full bg-accent/[0.07] blur-[160px]" />

      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md"
      >
        <Link to="/" className="mb-7 flex items-center gap-2 text-sm font-bold tracking-tight">
          <ShieldCheck className="h-5 w-5 text-accent" />
          SENTINEL MX
        </Link>

        <Panel className="p-7 sm:p-8">
          <div className="flex h-10 w-10 items-center justify-center rounded-md border border-accent/30 bg-accent/10">
            <LockKeyhole className="h-4 w-4 text-accent" />
          </div>
          <h1 className="mt-5 text-2xl font-semibold tracking-tight">
            {createAccount ? "Create analyst account" : "Sign in to the console"}
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            {createAccount
              ? "New accounts begin with the Analyst role. An administrator controls elevated access."
              : "Authenticate to analyze evidence and access forensic cases."}
          </p>

          <form className="mt-7 space-y-4" onSubmit={handleSubmit}>
            {createAccount && (
              <label className="block text-xs font-medium text-muted-foreground">
                Display name
                <input
                  required
                  maxLength={120}
                  autoComplete="name"
                  value={displayName}
                  onChange={(event) => setDisplayName(event.target.value)}
                  className="mt-2 w-full rounded-md border border-border bg-background px-3 py-2.5 text-sm text-foreground outline-none transition focus:border-accent/60"
                />
              </label>
            )}
            <label className="block text-xs font-medium text-muted-foreground">
              Email
              <input
                required
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-2 w-full rounded-md border border-border bg-background px-3 py-2.5 text-sm text-foreground outline-none transition focus:border-accent/60"
              />
            </label>
            {createAccount && (
              <label className="block text-xs font-medium text-muted-foreground">
                Confirm password
                <input
                  required
                  minLength={8}
                  type="password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  className="mt-2 w-full rounded-md border border-border bg-background px-3 py-2.5 text-sm text-foreground outline-none transition focus:border-accent/60"
                />
              </label>
            )}
            <label className="block text-xs font-medium text-muted-foreground">
              Password
              <input
                required
                minLength={8}
                type="password"
                autoComplete={createAccount ? "new-password" : "current-password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-2 w-full rounded-md border border-border bg-background px-3 py-2.5 text-sm text-foreground outline-none transition focus:border-accent/60"
              />
            </label>

            {formError && (
              <p role="alert" className="text-xs text-destructive">
                {formError}
              </p>
            )}
            {message && (
              <p role="status" className="text-xs leading-relaxed text-accent">
                {message}
              </p>
            )}

            <ActionButton type="submit" className="w-full justify-center" disabled={submitting}>
              {submitting ? "Please wait…" : createAccount ? "Create account" : "Sign in"}
            </ActionButton>
          </form>

          <button
            type="button"
            className="mt-5 w-full text-center text-xs text-muted-foreground transition hover:text-foreground"
            onClick={() => {
              setCreateAccount((value) => !value);
              setConfirmPassword("");
              setFormError(null);
              setMessage(null);
            }}
          >
            {createAccount ? "Already have an account? Sign in" : "Need an account? Create one"}
          </button>
        </Panel>
      </motion.div>
    </main>
  );
}
