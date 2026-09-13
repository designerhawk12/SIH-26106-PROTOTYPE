import { createFileRoute } from "@tanstack/react-router";
import { DemoModuleGate } from "@/components/demo/UnderDevelopmentPage";
import { AppShell } from "@/components/layout/AppShell";
import { CasesPage } from "@/pages/CasesPage";

const title = "Investigations — Sentinel MX";
const description =
  "Review the email investigation queue with risk scores, threat classification, sender detail and case status.";

export const Route = createFileRoute("/cases/")({
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
      <DemoModuleGate moduleName="Investigations">
        <CasesPage />
      </DemoModuleGate>
    </AppShell>
  ),
});
