import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/layout/AppShell";
import { ThreatIntelligencePage } from "@/pages/ThreatIntelligencePage";

const title = "Threat Intelligence — Sentinel MX";
const description =
  "Threat intelligence enrichment feeds for indicators observed across analyzed email cases.";

export const Route = createFileRoute("/threat-intelligence")({
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
      <ThreatIntelligencePage />
    </AppShell>
  ),
});
