export type AIInvestigationAction =
  "SUMMARY" | "SUSPICIOUS" | "RECOMMENDED_ACTIONS" | "AUTHENTICATION" | "IOCS";

export interface AIInvestigatorResponse {
  status: "AVAILABLE" | "UNAVAILABLE";
  action: AIInvestigationAction | "ASK";
  model: string | null;
  generated_at: string;
  ai_generated: true;
  simulated: boolean;
  summary: string;
  key_findings: string[];
  risk_explanation: string;
  recommended_actions: string[];
  ioc_summary: string;
  limitations: string[];
  answer: string | null;
  disclaimer: string;
}
