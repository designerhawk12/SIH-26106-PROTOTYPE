import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/layout/AppShell";
import { AnalyzePage } from "@/pages/AnalyzePage";

const title = "Analyze Suspicious Email — Sentinel MX";
const description =
  "Submit a raw .eml file for forensic analysis of headers, MIME structure, indicators, routing infrastructure and threat intent.";

export const Route = createFileRoute("/analyze")({
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
      <AnalyzePage />
    </AppShell>
  ),
});
