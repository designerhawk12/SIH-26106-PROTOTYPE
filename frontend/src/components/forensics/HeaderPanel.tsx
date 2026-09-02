import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { CopyValue } from "@/components/ui/CopyValue";
import { formatDateTime } from "@/lib/format";
import type { EmailHeaders } from "@/types/analysis";

export function HeaderPanel({ email }: { email: EmailHeaders }) {
  const rows: { label: string; value: string; mono?: boolean; copy?: boolean }[] = [
    { label: "Sender", value: `${email.sender_display_name} <${email.sender}>`, mono: true },
    { label: "Receiver", value: email.receiver, mono: true },
    { label: "Subject", value: email.subject },
    { label: "Date", value: formatDateTime(email.date) },
    { label: "Message-ID", value: email.message_id, mono: true, copy: true },
    { label: "Reply-To", value: email.reply_to ?? "—", mono: true },
    { label: "Return-Path", value: email.return_path ?? "—", mono: true },
  ];

  return (
    <Panel spotlight className="p-6">
      <SectionHeader eyebrow="Headers" title="Message Attributes" />
      <dl className="mt-5 divide-y divide-border">
        {rows.map((row) => (
          <div key={row.label} className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-[160px_1fr]">
            <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              {row.label}
            </dt>
            <dd className="min-w-0">
              {row.copy ? (
                <CopyValue value={row.value} truncate />
              ) : (
                <span
                  className={
                    row.mono
                      ? "block truncate font-mono text-xs text-foreground/85"
                      : "block text-sm text-foreground/90"
                  }
                >
                  {row.value}
                </span>
              )}
            </dd>
          </div>
        ))}
      </dl>
    </Panel>
  );
}
