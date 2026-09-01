import type { ReactNode } from "react";
import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";

export interface IOCColumn<T> {
  header: string;
  /** Tailwind width/alignment classes for the column. */
  className?: string;
  render: (row: T) => ReactNode;
}

interface Props<T> {
  title: string;
  eyebrow?: string;
  columns: IOCColumn<T>[];
  rows: T[];
  emptyLabel?: string;
}

/** Generic, reusable IOC table used for IPs, domains, URLs and attachments. */
export function IOCDataTable<T>({
  title,
  eyebrow,
  columns,
  rows,
  emptyLabel = "No indicators of this type were observed.",
}: Props<T>) {
  return (
    <Panel className="p-6">
      <SectionHeader {...(eyebrow ? { eyebrow } : {})} title={title} />
      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[640px] border-collapse text-left">
          <thead>
            <tr className="border-b border-border">
              {columns.map((column) => (
                <th
                  key={column.header}
                  className={`pb-3 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground ${column.className ?? ""}`}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td
                  colSpan={columns.length}
                  className="py-6 text-center text-xs text-muted-foreground"
                >
                  {emptyLabel}
                </td>
              </tr>
            )}
            {rows.map((row, i) => (
              <tr
                key={i}
                className="border-b border-border/60 transition-colors duration-200 last:border-0 hover:bg-surface-hover/70"
              >
                {columns.map((column) => (
                  <td
                    key={column.header}
                    className={`py-3 pr-4 align-middle text-sm ${column.className ?? ""}`}
                  >
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
