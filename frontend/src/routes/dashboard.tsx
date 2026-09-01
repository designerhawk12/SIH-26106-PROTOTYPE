import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardPage } from "@/pages/DashboardPage";

const title = "Threat Intelligence Overview — Sentinel MX";
const description =
  "Email security command center: analyzed volume, detected threats, phishing and BEC activity, authentication failures and infrastructure observations.";

export const Route = createFileRoute("/dashboard")({
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
      <DashboardPage />
    </AppShell>
  ),
});
