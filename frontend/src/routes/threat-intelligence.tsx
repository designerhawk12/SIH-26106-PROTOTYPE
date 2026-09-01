import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/layout/AppShell";
import { PlaceholderPage } from "@/pages/PlaceholderPage";

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
      <PlaceholderPage
        title="Threat Intelligence"
        description="Enrichment feeds for observed indicators will surface here once the intelligence service is connected."
      />
    </AppShell>
  ),
});
