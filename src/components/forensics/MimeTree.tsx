import type { ReactElement } from "react";
import { Panel } from "@/components/ui/Panel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatBytes } from "@/lib/format";
import type { MimeNode } from "@/types/analysis";

function renderNode(
  node: MimeNode,
  depth: number,
  isLast: boolean,
  key: string,
): ReactElement[] {
  const prefix = depth === 0 ? "" : `${"    ".repeat(depth - 1)}${isLast ? "└── " : "├── "}`;
  const children = node.children ?? [];

  return [
    <div key={key} className="flex items-baseline justify-between gap-4 py-1">
      <span className="whitespace-pre font-mono text-xs text-foreground/85">
        <span className="text-muted-foreground">{prefix}</span>
        <span className={depth === 0 ? "text-accent" : undefined}>{node.content_type}</span>
        {node.filename && <span className="text-muted-foreground"> · {node.filename}</span>}
      </span>
      <span className="shrink-0 font-mono text-[11px] text-muted-foreground">
        {formatBytes(node.size_bytes)}
      </span>
    </div>,
    ...children.flatMap((child, i) =>
      renderNode(child, depth + 1, i === children.length - 1, `${key}-${i}`),
    ),
  ];
}

export function MimeTree({ root }: { root: MimeNode }) {
  return (
    <Panel className="p-6">
      <SectionHeader eyebrow="Structure" title="MIME Structure" />
      <div className="bg-dots mt-5 rounded-sm border border-border bg-background/60 p-4">
        {renderNode(root, 0, true, "root")}
      </div>
    </Panel>
  );
}
