import { Fingerprint } from "lucide-react";
import { Panel } from "@/components/ui/Panel";
import { CopyValue } from "@/components/ui/CopyValue";

interface Props {
  label: string;
  value: string;
  caption?: string;
}

export function EvidenceHash({ label, value, caption }: Props) {
  return (
    <Panel interactive className="p-5">
      <div className="flex items-center gap-2">
        <Fingerprint className="h-3.5 w-3.5 text-accent" />
        <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          {label}
        </p>
      </div>
      <div className="mt-3 min-w-0">
        <CopyValue value={value} truncate className="w-full" />
      </div>
      {caption && <p className="mt-2 text-xs text-muted-foreground">{caption}</p>}
    </Panel>
  );
}
