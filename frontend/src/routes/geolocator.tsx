import { createFileRoute } from "@tanstack/react-router";
import { DemoModuleGate } from "@/components/demo/UnderDevelopmentPage";
import { AppShell } from "@/components/layout/AppShell";
import { GeolocatorPage } from "@/pages/GeolocatorPage";

export const Route = createFileRoute("/geolocator")({
  head: () => ({ meta: [{ title: "Observed Infrastructure Map — Sentinel MX" }] }),
  component: () => (
    <AppShell>
      <DemoModuleGate moduleName="Geolocator">
        <GeolocatorPage />
      </DemoModuleGate>
    </AppShell>
  ),
});
