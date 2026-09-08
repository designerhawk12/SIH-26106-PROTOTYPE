import { useQuery } from "@tanstack/react-query";
import { Activity, AlertTriangle, CheckCircle2 } from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";
import { Panel } from "@/components/ui/Panel";
import { ThreatBadge, type BadgeTone } from "@/components/ui/ThreatBadge";
import { useAuth } from "@/auth/AuthProvider";
import { formatDateTime } from "@/lib/format";
import {
  getErrorMessage,
  getHealth,
  getSystemStatus,
  type SystemComponentStatus,
  type SystemStatusState,
} from "@/services/api";

function toneForStatus(state: SystemStatusState): BadgeTone {
  if (state === "NOT_CONFIGURED") return "neutral";
  if (state === "SIMULATED") return "warning";
  if (state === "DISABLED") return "neutral";
  return "success";
}

function StatusItem({ item }: { item: SystemComponentStatus }) {
  return (
    <div className="rounded-sm border border-border bg-background p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">{item.label}</h2>
        <ThreatBadge label={item.state.replaceAll("_", " ")} tone={toneForStatus(item.state)} />
      </div>
      <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{item.detail}</p>
    </div>
  );
}

export function SystemStatusPage() {
  const { hasPermission } = useAuth();
  const { data, error, isError, isPending, refetch } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
    retry: 1,
  });
  const status = useQuery({
    queryKey: ["system-status"],
    queryFn: getSystemStatus,
    enabled: hasPermission("VIEW_SYSTEM_CONFIGURATION"),
    retry: false,
  });

  return (
    <div className="mx-auto max-w-[900px]">
      <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-accent">System</p>
      <h1 className="mt-3 text-4xl font-bold tracking-tight lg:text-5xl">System Status</h1>

      <Panel spotlight className="mt-8 p-8">
        {isPending && (
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <Activity className="h-4 w-4 animate-pulse text-accent" />
            Checking the backend analysis service…
          </div>
        )}

        {isError && (
          <div>
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
              <div>
                <p className="text-sm font-semibold text-danger">Backend service unavailable</p>
                <p role="alert" className="mt-1 text-xs text-muted-foreground">
                  {getErrorMessage(error, "Health status could not be loaded.")}
                </p>
              </div>
            </div>
            <ActionButton variant="secondary" className="mt-5" onClick={() => void refetch()}>
              Retry
            </ActionButton>
          </div>
        )}

        {data && (
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
              <div>
                <p className="text-sm font-semibold text-success">Backend service operational</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  The API health endpoint responded successfully.
                </p>
              </div>
            </div>
            <dl className="grid gap-4 sm:grid-cols-2">
              <div>
                <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                  Version
                </dt>
                <dd className="mt-1 font-mono text-xs text-foreground">{data.version}</dd>
              </div>
              <div>
                <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                  Last checked
                </dt>
                <dd className="mt-1 font-mono text-xs text-foreground">
                  {formatDateTime(data.timestamp)}
                </dd>
              </div>
            </dl>
          </div>
        )}
      </Panel>

      {hasPermission("VIEW_SYSTEM_CONFIGURATION") ? (
        <section className="mt-8">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-accent">Configuration</p>
              <h2 className="mt-2 text-xl font-semibold">Safe deployment status</h2>
              <p className="mt-1 text-xs text-muted-foreground">
                States only. Credentials, URLs, tokens, and provider keys are never displayed.
              </p>
            </div>
            {status.isError && (
              <ActionButton variant="secondary" onClick={() => void status.refetch()}>
                Retry status
              </ActionButton>
            )}
          </div>

          {status.isPending && (
            <Panel className="p-5 text-sm text-muted-foreground">Loading system configuration…</Panel>
          )}
          {status.isError && (
            <Panel className="p-5" role="alert">
              <p className="text-sm font-semibold text-danger">Configuration status unavailable</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {getErrorMessage(status.error, "System configuration could not be loaded.")}
              </p>
            </Panel>
          )}
          {status.data && (
            <div className="grid gap-4 md:grid-cols-2">
              <StatusItem item={status.data.backend} />
              <StatusItem item={status.data.database} />
              <StatusItem item={status.data.authentication} />
              <StatusItem item={status.data.demo_mode} />
              {status.data.threat_intelligence.map((item) => <StatusItem key={item.label} item={item} />)}
              <StatusItem item={status.data.geolocation} />
              <StatusItem item={status.data.ai_investigator} />
            </div>
          )}
        </section>
      ) : (
        <Panel className="mt-8 p-5">
          <p className="text-sm font-semibold">System configuration is administrator-only</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Your role can view the backend health check but cannot inspect deployment configuration.
          </p>
        </Panel>
      )}
    </div>
  );
}
