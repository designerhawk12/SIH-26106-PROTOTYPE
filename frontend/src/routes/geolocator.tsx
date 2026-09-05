import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/layout/AppShell";
import { GeolocatorPage } from "@/pages/GeolocatorPage";

export const Route = createFileRoute("/geolocator")({
  head: () => ({ meta: [{ title: "Observed Infrastructure Map — Sentinel MX" }] }),
  component: () => (
    <AppShell>
      <GeolocatorPage />
    </AppShell>
  ),
});
