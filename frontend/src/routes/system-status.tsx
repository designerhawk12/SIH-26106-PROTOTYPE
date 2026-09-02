import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/layout/AppShell";
import { SystemStatusPage } from "@/pages/SystemStatusPage";

const title = "System Status — Sentinel MX";
const description = "Health of the analysis pipeline, intelligence feeds and ingestion services.";

export const Route = createFileRoute("/system-status")({
  head: () => ({
    meta: [
      { title },
      { name: "description", content: description },
      { property: "og:title", content: title },
      { property: "og:description", content: description },
    ],
  }),
  component: () => (
    <AppShell>
      <SystemStatusPage />
    </AppShell>
  ),
});
