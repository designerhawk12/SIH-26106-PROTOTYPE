import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/layout/AppShell";
import { PlaceholderPage } from "@/pages/PlaceholderPage";

const title = "Settings — Sentinel MX";
const description = "Workspace, analyst and integration settings for the investigation console.";

export const Route = createFileRoute("/settings")({
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
        title="Settings"
        description="Workspace preferences, analyst profile and backend integration configuration will live here."
      />
    </AppShell>
  ),
});
