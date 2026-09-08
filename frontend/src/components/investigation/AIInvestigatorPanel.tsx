import { useMutation } from "@tanstack/react-query";
import { Bot, Send, ShieldAlert, Sparkles } from "lucide-react";
import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { ThreatBadge } from "@/components/ui/ThreatBadge";
import { formatDateTime } from "@/lib/format";
import { askAIInvestigator, getErrorMessage, investigateCase } from "@/services/api";
import type { AIInvestigationAction, AIInvestigatorResponse } from "@/types/aiInvestigator";

const ACTIONS: { action: AIInvestigationAction; label: string }[] = [
  { action: "SUMMARY", label: "Summarize Investigation" },
  { action: "SUSPICIOUS", label: "Why Is This Suspicious?" },
  { action: "RECOMMENDED_ACTIONS", label: "Recommended Analyst Actions" },
  { action: "AUTHENTICATION", label: "Explain Authentication" },
  { action: "IOCS", label: "Summarize IOCs" },
];

export function AIInvestigatorPanel({ caseId }: { caseId: string }) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AIInvestigatorResponse | null>(null);

  const investigate = useMutation({
    mutationFn: (action: AIInvestigationAction) => investigateCase(caseId, action),
    onSuccess: setResult,
  });
  const ask = useMutation({
    mutationFn: (value: string) => askAIInvestigator(caseId, value),
    onSuccess: setResult,
  });
  const pending = investigate.isPending || ask.isPending;
  const error = investigate.error ?? ask.error;

  function handleAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = question.trim();
    if (!normalized || pending) return;
    ask.mutate(normalized);
  }

  return (
    <div className="space-y-4">
      <Panel spotlight className="overflow-hidden p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <SectionHeader
            eyebrow="Assistive analysis"
            title="AI Investigator"
            subtitle="Powered by Groq · grounded in persisted case evidence."
          />
          <div className="flex items-center gap-2">
            <ThreatBadge label="GROQ" tone="ai" />
            <ThreatBadge label="AI ASSISTED" tone="accent" />
          </div>
        </div>

        <div className="mt-5 flex items-start gap-3 rounded-xl border border-warning/20 bg-warning/[0.05] p-4">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
          <p className="text-xs leading-relaxed text-muted-foreground">
            AI is assistive only. It cannot change the official risk score, authentication results,
            hashes, IOCs, provider verdicts, or deterministic findings.
          </p>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          {ACTIONS.map(({ action, label }) => (
            <ActionButton
              key={action}
              variant="secondary"
              disabled={pending}
              icon={<Sparkles className="h-3.5 w-3.5" />}
              onClick={() => investigate.mutate(action)}
            >
              {label}
            </ActionButton>
          ))}
        </div>

        <form className="mt-6" onSubmit={handleAsk}>
          <label
            htmlFor="ai-case-question"
            className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground"
          >
            Ask About This Case
          </label>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row">
            <textarea
              id="ai-case-question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              maxLength={1000}
              rows={2}
              placeholder="What should I validate next?"
              className="min-h-20 flex-1 resize-y rounded-xl border border-border bg-background/70 px-4 py-3 text-sm text-foreground outline-none transition focus:border-accent/50 focus:ring-2 focus:ring-accent/10"
            />
            <ActionButton
              type="submit"
              disabled={pending || !question.trim()}
              icon={<Send className="h-3.5 w-3.5" />}
            >
              {ask.isPending ? "Asking" : "Ask Investigator"}
            </ActionButton>
          </div>
        </form>

        {pending && (
          <p className="mt-4 font-mono text-xs text-accent" role="status">
            Reviewing persisted case evidence…
          </p>
        )}
        {error && (
          <p className="mt-4 text-sm text-danger" role="alert">
            {getErrorMessage(error, "AI Investigator unavailable.")}
          </p>
        )}
      </Panel>

      {result && <AIResult result={result} />}
    </div>
  );
}

function AIResult({ result }: { result: AIInvestigatorResponse }) {
  if (result.status === "UNAVAILABLE") {
    return (
      <Panel className="p-6">
        <div className="flex items-start gap-3">
          <Bot className="mt-0.5 h-5 w-5 text-muted-foreground" />
          <div>
            <h3 className="font-semibold">AI Investigator unavailable</h3>
            <p className="mt-2 text-sm text-muted-foreground">{result.summary}</p>
            {result.limitations[0] && (
              <p className="mt-2 text-xs text-warning">{result.limitations[0]}</p>
            )}
            <p className="mt-2 text-xs text-muted-foreground">
              Case evidence, reporting, and deterministic assessment remain available.
            </p>
          </div>
        </div>
      </Panel>
    );
  }

  return (
    <Panel className="p-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-accent" />
          <h3 className="font-semibold">AI-generated interpretation</h3>
          {result.simulated && <ThreatBadge label="DEMO / SIMULATED" tone="warning" />}
        </div>
        <p className="font-mono text-[10px] text-muted-foreground">
          {result.model ?? "Model unavailable"} · {formatDateTime(result.generated_at)}
        </p>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <AISection title="Summary" content={result.summary} />
        <AISection title="Official risk context" content={result.risk_explanation} />
        <AISection title="IOC summary" content={result.ioc_summary} />
        {result.answer && <AISection title="Answer" content={result.answer} />}
        {result.key_findings.length > 0 && (
          <AIList title="Key findings" items={result.key_findings} />
        )}
        {result.recommended_actions.length > 0 && (
          <AIList title="Recommended analyst actions" items={result.recommended_actions} />
        )}
        {result.limitations.length > 0 && <AIList title="Limitations" items={result.limitations} />}
      </div>

      <p className="mt-5 border-t border-border pt-4 text-xs leading-relaxed text-muted-foreground">
        {result.disclaimer}
      </p>
    </Panel>
  );
}

function AISection({ title, content }: { title: string; content: string }) {
  return (
    <section>
      <h4 className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent">{title}</h4>
      <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
        {content}
      </p>
    </section>
  );
}

function AIList({ title, items }: { title: string; items: string[] }) {
  return (
    <section>
      <h4 className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent">{title}</h4>
      <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
        {items.map((item, index) => (
          <li key={`${index}-${item}`} className="flex gap-2">
            <span className="text-accent">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
