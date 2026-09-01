import { CyberBlocks } from "@/components/ui/CyberBlocks";
import { Panel } from "@/components/ui/Panel";

/**
 * Shared shell for navigation destinations that are not part of the initial
 * scope (Threat Intelligence, System Status, Settings).
 */
export function PlaceholderPage({ title, description }: { title: string; description: string }) {
  return (
    <div className="mx-auto max-w-[900px]">
      <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-accent">Module</p>
      <h1 className="mt-3 text-4xl font-bold tracking-tight lg:text-5xl">{title}</h1>
      <Panel className="mt-8 flex flex-col items-center gap-4 p-10 text-center">
        <CyberBlocks className="h-56 w-56" />
        <p className="max-w-md text-sm leading-relaxed text-muted-foreground">{description}</p>
      </Panel>
    </div>
  );
}
