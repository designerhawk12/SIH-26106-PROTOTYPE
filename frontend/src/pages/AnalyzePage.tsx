import { useNavigate } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import { Check, FileText, Loader2, UploadCloud, X } from "lucide-react";
import { useRef, useState } from "react";
import { ActionButton } from "@/components/ui/ActionButton";
import { CyberBlocks } from "@/components/ui/CyberBlocks";
import { Panel } from "@/components/ui/Panel";
import { formatBytes } from "@/lib/format";
import { analyzeEmail } from "@/services/api";

const STAGES = [
  "Reading Email",
  "Parsing MIME Structure",
  "Extracting Headers",
  "Extracting Indicators",
  "Analyzing Threat Intent",
  "Checking Threat Intelligence",
  "Mapping Infrastructure",
  "Calculating Risk",
  "Complete",
] as const;

export function AnalyzePage() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [stage, setStage] = useState<number | null>(null);

  const running = stage !== null;

  /** Visual-only staged progress. Real analysis happens in the backend. */
  const runAnalysis = async () => {
    if (!file || running) return;
    setStage(0);
    const analysis = analyzeEmail(file);
    for (let i = 1; i < STAGES.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, 520));
      setStage(i);
    }
    const result = await analysis;
    await new Promise((resolve) => setTimeout(resolve, 500));
    void navigate({ to: "/cases/$caseId", params: { caseId: result.case_id } });
  };

  return (
    <div className="mx-auto max-w-[1200px] space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      >
        <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-accent">
          Forensic Intake
        </p>
        <h1 className="mt-3 text-4xl font-bold leading-[1.05] tracking-tight lg:text-5xl">
          Analyze Suspicious Email
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Submit a raw <span className="font-mono text-foreground/80">.eml</span> file for forensic
          analysis. Headers, MIME structure, indicators, routing infrastructure and threat intent
          are examined and preserved as a case record.
        </p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Panel className="relative p-6">
          <div className="bg-grid pointer-events-none absolute inset-0 opacity-40" />
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              const dropped = e.dataTransfer.files?.[0];
              if (dropped) setFile(dropped);
            }}
            className={`relative flex flex-col items-center justify-center rounded-sm border border-dashed px-6 py-16 text-center transition-colors duration-300 ${
              dragging ? "border-accent bg-accent/[0.04]" : "border-border-strong"
            }`}
          >
            <span className="flex h-12 w-12 items-center justify-center rounded-sm border border-border bg-surface">
              <UploadCloud className="h-5 w-5 text-accent" />
            </span>
            <p className="mt-5 text-sm font-semibold">Drag and drop an .EML file</p>
            <p className="mt-1 text-xs text-muted-foreground">Maximum file size 25 MB</p>
            <input
              ref={inputRef}
              type="file"
              accept=".eml,message/rfc822"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <div className="mt-6">
              <ActionButton variant="secondary" onClick={() => inputRef.current?.click()}>
                Select .EML File
              </ActionButton>
            </div>
          </div>

          <AnimatePresence>
            {file && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className="relative mt-4 flex items-center gap-3 rounded-sm border border-border bg-surface-raised px-4 py-3"
              >
                <FileText className="h-4 w-4 shrink-0 text-accent" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-foreground">{file.name}</p>
                  <p className="font-mono text-[11px] text-muted-foreground">
                    {formatBytes(file.size)}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setFile(null)}
                  aria-label="Remove file"
                  className="rounded-sm border border-border p-1 text-muted-foreground transition-colors hover:border-danger/60 hover:text-danger"
                >
                  <X className="h-3 w-3" />
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="relative mt-6 flex justify-end">
            <ActionButton arrow disabled={!file || running} onClick={runAnalysis}>
              {running ? "Analyzing" : "Analyze Email"}
            </ActionButton>
          </div>
        </Panel>

        <Panel className="relative overflow-hidden p-6">
          <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-muted-foreground">
            Analysis Pipeline
          </p>

          {!running ? (
            <div className="mt-4 flex flex-col items-center">
              <CyberBlocks className="h-56 w-56" />
              <p className="mt-2 text-center text-xs leading-relaxed text-muted-foreground">
                Awaiting evidence. Submit an email to start a forensic case.
              </p>
            </div>
          ) : (
            <div className="relative mt-5">
              <motion.div
                className="scan-line absolute inset-x-0 h-px"
                initial={{ top: 0 }}
                animate={{ top: ["0%", "100%", "0%"] }}
                transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
              />
              <ol className="space-y-3">
                {STAGES.map((label, i) => {
                  const done = stage !== null && i < stage;
                  const active = stage === i;
                  return (
                    <li key={label} className="flex items-center gap-3">
                      <span
                        className={`flex h-5 w-5 items-center justify-center rounded-sm border text-[10px] ${
                          done
                            ? "border-accent/40 bg-accent/10 text-accent"
                            : active
                              ? "border-accent bg-accent text-accent-foreground"
                              : "border-border text-muted-foreground"
                        }`}
                      >
                        {done ? (
                          <Check className="h-3 w-3" />
                        ) : active ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          i + 1
                        )}
                      </span>
                      <span
                        className={`text-xs ${
                          active
                            ? "text-accent text-accent-glow"
                            : done
                              ? "text-foreground/80"
                              : "text-muted-foreground"
                        }`}
                      >
                        {label}
                      </span>
                    </li>
                  );
                })}
              </ol>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
