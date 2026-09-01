import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/layout/AppShell";
import { InvestigationPage } from "@/pages/InvestigationPage";

const title = "Investigation Workspace — Sentinel MX";
const description =
  "Full forensic breakdown of a suspicious email: risk explainability, authentication, indicators, infrastructure, AI findings, timeline and evidence.";

export const Route = createFileRoute("/cases/$caseId")({
  head: () => ({
    meta: [
      { title },
      { name: "description", content: description },
      { property: "og:title", content: title },
      { property: "og:description", content: description },
    ],
  }),
  component: InvestigationRoute,
});

function InvestigationRoute() {
  const { caseId } = Route.useParams();
  return (
    <AppShell>
      <InvestigationPage caseId={caseId} />
    </AppShell>
  );
}
