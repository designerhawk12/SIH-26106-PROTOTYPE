import { useQuery } from "@tanstack/react-query";
import { Activity, AlertTriangle, CheckCircle2 } from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";
import { Panel } from "@/components/ui/Panel";
import { formatDateTime } from "@/lib/format";
import { getErrorMessage, getHealth } from "@/services/api";

export function SystemStatusPage() {
  const { data, error, isError, isPending, refetch } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
    retry: 1,
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
    </div>
  );
}
