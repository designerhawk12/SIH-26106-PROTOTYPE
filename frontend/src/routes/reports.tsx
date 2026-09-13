import { createFileRoute } from "@tanstack/react-router";
import { DemoModuleGate } from "@/components/demo/UnderDevelopmentPage";
import { AppShell } from "@/components/layout/AppShell";
import { ReportsPage } from "@/pages/ReportsPage";

const title = "Forensic Reports — Sentinel MX";
const description =
  "Generate and download structured forensic investigation reports for analyzed email cases.";

export const Route = createFileRoute("/reports")({
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
      <DemoModuleGate moduleName="Forensic Reports">
        <ReportsPage />
      </DemoModuleGate>
    </AppShell>
  ),
});
