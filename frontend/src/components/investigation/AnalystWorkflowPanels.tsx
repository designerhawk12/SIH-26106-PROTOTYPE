import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ClipboardList, MessageSquarePlus, Send } from "lucide-react";
import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatDateTime } from "@/lib/format";
import { createCaseNote, getCaseAudit, getCaseNotes, getErrorMessage } from "@/services/api";

export function AnalystNotesPanel({ caseId }: { caseId: string }) {
  const [content, setContent] = useState("");
  const queryClient = useQueryClient();
  const notes = useQuery({ queryKey: ["case-notes", caseId], queryFn: () => getCaseNotes(caseId) });
  const create = useMutation({
    mutationFn: (value: string) => createCaseNote(caseId, value),
    onSuccess: () => {
      setContent("");
      void queryClient.invalidateQueries({ queryKey: ["case-notes", caseId] });
      void queryClient.invalidateQueries({ queryKey: ["case-audit", caseId] });
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const note = content.trim();
    if (note && !create.isPending) create.mutate(note);
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
      <Panel spotlight className="p-6">
        <SectionHeader
          eyebrow="Human assessment"
          title="Analyst Notes"
          subtitle="Notes are separate from original forensic evidence."
        />
        <form className="mt-5 space-y-3" onSubmit={submit}>
          <label className="sr-only" htmlFor="case-analyst-note">
            Add analyst note
          </label>
          <textarea
            id="case-analyst-note"
            value={content}
            onChange={(event) => setContent(event.target.value)}
            maxLength={5000}
            placeholder="Record an analyst observation, decision, or follow-up…"
            className="min-h-32 w-full rounded-sm border border-border bg-background p-3 text-sm outline-none focus:border-accent/60"
          />
          <div className="flex items-center justify-between gap-3">
            <span className="font-mono text-[10px] text-muted-foreground">
              {content.length}/5000
            </span>
            <ActionButton
              type="submit"
              disabled={!content.trim() || create.isPending}
              icon={<Send className="h-3.5 w-3.5" />}
            >
              {create.isPending ? "Saving…" : "Add Note"}
            </ActionButton>
          </div>
        </form>
        {create.isError && (
          <p role="alert" className="mt-3 text-xs text-danger">
            {getErrorMessage(create.error, "The analyst note could not be saved.")}
          </p>
        )}
      </Panel>
      <Panel className="p-6">
        <div className="flex items-center gap-2">
          <MessageSquarePlus className="h-4 w-4 text-accent" />
          <h2 className="text-sm font-semibold">Persisted Notes</h2>
        </div>
        {notes.isPending && (
          <p className="mt-5 text-xs text-muted-foreground">Loading analyst notes…</p>
        )}
        {notes.isError && (
          <p role="alert" className="mt-5 text-xs text-danger">
            {getErrorMessage(notes.error, "Notes could not be loaded.")}
          </p>
        )}
        {!notes.isPending && !notes.isError && notes.data?.length === 0 && (
          <p className="mt-5 text-sm text-muted-foreground">
            No analyst notes have been added to this case.
          </p>
        )}
        <div className="mt-4 max-h-96 space-y-3 overflow-y-auto pr-1">
          {notes.data?.map((note) => (
            <article
              key={note.note_id}
              className="rounded-sm border border-border/70 bg-background/40 p-4"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-medium">{note.author_display_name}</p>
                <time className="font-mono text-[10px] text-muted-foreground">
                  {formatDateTime(note.updated_at)}
                </time>
              </div>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-foreground/85">
                {note.content}
              </p>
            </article>
          ))}
        </div>
      </Panel>
    </div>
  );
}

export function AuditTrailPanel({ caseId }: { caseId: string }) {
  const audit = useQuery({ queryKey: ["case-audit", caseId], queryFn: () => getCaseAudit(caseId) });
  return (
    <Panel spotlight className="p-6">
      <SectionHeader
        eyebrow="Application activity"
        title="Audit Trail"
        subtitle="Audit events are separate from forensic evidence and analyst notes."
      />
      {audit.isPending && (
        <p className="mt-5 text-xs text-muted-foreground">Loading audit events…</p>
      )}
      {audit.isError && (
        <p role="alert" className="mt-5 text-xs text-danger">
          {getErrorMessage(audit.error, "Audit events could not be loaded.")}
        </p>
      )}
      {!audit.isPending && !audit.isError && audit.data?.length === 0 && (
        <p className="mt-5 text-sm text-muted-foreground">No audit events are available.</p>
      )}
      <div className="mt-5 space-y-2">
        {audit.data?.map((event) => (
          <div
            key={event.event_id}
            className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 py-3 last:border-0"
          >
            <div className="flex items-center gap-3">
              <ClipboardList className="h-4 w-4 text-accent" />
              <span className="font-mono text-xs text-foreground/85">
                {event.action.replaceAll("_", " ")}
              </span>
            </div>
            <time className="font-mono text-[10px] text-muted-foreground">
              {formatDateTime(event.timestamp)}
            </time>
          </div>
        ))}
      </div>
    </Panel>
  );
}
