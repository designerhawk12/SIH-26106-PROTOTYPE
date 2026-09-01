import { createFileRoute } from "@tanstack/react-router";
import { LandingPage } from "@/pages/LandingPage";

const title = "Sentinel MX — AI Email Threat Detection & Forensic Intelligence";
const description =
  "Forensic email threat investigation: authentication analysis, indicators of compromise, observed routing infrastructure and AI threat intent findings.";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title },
      { name: "description", content: description },
      { property: "og:title", content: title },
      { property: "og:description", content: description },
    ],
  }),
  component: LandingPage,
});
