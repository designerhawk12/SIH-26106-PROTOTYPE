import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { resolveDemoMode } from "../src/config/demoMode.ts";

test("demo mode is explicit opt-in and reversible", () => {
  assert.equal(resolveDemoMode("true"), true);
  assert.equal(resolveDemoMode("false"), false);
  assert.equal(resolveDemoMode(undefined), false);
  assert.equal(resolveDemoMode("TRUE"), false);
  assert.equal(resolveDemoMode("1"), false);
});

test("only presentation modules are gated and case analysis remains available", () => {
  for (const route of [
    "cases.index.tsx",
    "geolocator.tsx",
    "reports.tsx",
    "threat-intelligence.tsx",
  ]) {
    const source = readFileSync(new URL(`../src/routes/${route}`, import.meta.url), "utf8");
    assert.match(source, /DemoModuleGate/);
  }

  const analysisRoute = readFileSync(
    new URL("../src/routes/cases.$caseId.tsx", import.meta.url),
    "utf8",
  );
  assert.doesNotMatch(analysisRoute, /DemoModuleGate|UnderDevelopmentPage/);
  assert.match(analysisRoute, /InvestigationPage/);
});

test("all existing detailed analysis tabs remain present", () => {
  const tabs = readFileSync(
    new URL("../src/components/investigation/InvestigationTabs.tsx", import.meta.url),
    "utf8",
  );
  for (const label of [
    "Overview",
    "Email Forensics",
    "Authentication",
    "Indicators",
    "Infrastructure",
    "AI Findings",
    "AI Investigator",
    "Analyst Notes",
    "Audit Trail",
    "Evidence",
  ]) {
    assert.match(tabs, new RegExp(`"${label}"`));
  }
});
