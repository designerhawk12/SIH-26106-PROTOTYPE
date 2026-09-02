import { useNavigate } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import { Check, FileText, Loader2, UploadCloud, X } from "lucide-react";
import { useRef, useState } from "react";
import { ScanLine } from "@/components/effects/ScanLine";
import { ActionButton } from "@/components/ui/ActionButton";
import { CyberBlocks } from "@/components/ui/CyberBlocks";
import { Panel } from "@/components/ui/Panel";
import { useReducedMotionPreference } from "@/hooks/useReducedMotionPreference";
import { formatBytes } from "@/lib/format";
import { analyzeEmail, getErrorMessage } from "@/services/api";

const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;

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
  const [error, setError] = useState<string | null>(null);
  const reduceMotion = useReducedMotionPreference();

  const running = stage !== null;

  const selectFile = (candidate: File | null) => {
    setError(null);
    if (!candidate) {
      setFile(null);
      return;
    }
    if (!candidate.name.trim()) {
      setFile(null);
      setError("The selected file must have a filename.");
      return;
    }
    if (!candidate.name.toLowerCase().endsWith(".eml")) {
      setFile(null);
      setError("Only raw .eml email files are accepted.");
      return;
    }
    if (candidate.size === 0) {
      setFile(null);
      setError("The selected .eml file is empty.");
      return;
    }
    if (candidate.size > MAX_UPLOAD_BYTES) {
      setFile(null);
      setError("The selected .eml file exceeds the 25 MB upload limit.");
      return;
    }
    setFile(candidate);
  };

  /** Visual-only staged progress. Real analysis happens in the backend. */
  const runAnalysis = async () => {
    if (!file || running) return;
    setError(null);
    setStage(0);
    const progressTimer = window.setInterval(
      () =>
        setStage((current) => (current === null ? null : Math.min(current + 1, STAGES.length - 2))),
      reduceMotion ? 80 : 650,
    );
    try {
      const result = await analyzeEmail(file);
      window.clearInterval(progressTimer);
      setStage(STAGES.length - 1);
      await new Promise((resolve) => setTimeout(resolve, reduceMotion ? 35 : 350));
      await navigate({ to: "/cases/$caseId", params: { caseId: result.case_id } });
    } catch (requestError) {
      window.clearInterval(progressTimer);
      setStage(null);
      setError(getErrorMessage(requestError, "The email could not be analyzed."));
    }
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
        <Panel spotlight tilt sweep className="relative p-6">
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
              selectFile(dropped ?? null);
            }}
            className={`relative flex flex-col items-center justify-center overflow-hidden rounded-sm border border-dashed px-6 py-16 text-center transition-all duration-300 ${
              dragging
                ? "scale-[1.01] border-accent bg-accent/[0.055] shadow-[inset_0_0_42px_-28px_var(--accent)]"
                : "border-border-strong"
            }`}
          >
            {dragging && <ScanLine />}
            <motion.span
              {...(dragging && !reduceMotion ? { animate: { y: [0, -5, 0] } } : {})}
              transition={{ duration: 1.2, repeat: Infinity }}
              className="flex h-12 w-12 items-center justify-center rounded-sm border border-border bg-surface"
            >
              <UploadCloud className="h-5 w-5 text-accent" />
            </motion.span>
            <p className="mt-5 text-sm font-semibold">Drag and drop an .EML file</p>
            <p className="mt-1 text-xs text-muted-foreground">Maximum file size 25 MB</p>
            <input
              ref={inputRef}
              type="file"
              accept=".eml,message/rfc822"
              className="hidden"
              onChange={(e) => selectFile(e.target.files?.[0] ?? null)}
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
                className="relative mt-4 flex items-center gap-3 overflow-hidden rounded-sm border border-success/25 bg-success/[0.035] px-4 py-3"
              >
                <motion.span
                  aria-hidden
                  className="absolute inset-y-0 left-0 w-px bg-success"
                  initial={{ scaleY: 0 }}
                  animate={{ scaleY: 1 }}
                />
                <FileText className="h-4 w-4 shrink-0 text-accent" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-foreground">{file.name}</p>
                  <p className="font-mono text-[11px] text-muted-foreground">
                    {formatBytes(file.size)}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    selectFile(null);
                    if (inputRef.current) inputRef.current.value = "";
                  }}
                  aria-label="Remove file"
                  className="rounded-sm border border-border p-1 text-muted-foreground transition-colors hover:border-danger/60 hover:text-danger"
                >
                  <X className="h-3 w-3" />
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {error && (
            <p
              role="alert"
              className="relative mt-4 rounded-sm border border-danger/30 bg-danger/[0.06] px-4 py-3 text-xs text-danger"
            >
              {error}
            </p>
          )}

          <div className="relative mt-6 flex justify-end">
            <ActionButton arrow disabled={!file || running} onClick={runAnalysis}>
              {running ? "Analyzing" : "Analyze Email"}
            </ActionButton>
          </div>
        </Panel>

        <Panel spotlight tone="ai" className="relative overflow-hidden p-6">
          <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-muted-foreground">
            Analysis Pipeline
          </p>

          {!running ? (
            <div className="mt-4 flex flex-col items-center">
              <CyberBlocks className="w-full max-w-[280px]" />
              <p className="mt-2 text-center text-xs leading-relaxed text-muted-foreground">
                Awaiting evidence. Submit an email to start a forensic case.
              </p>
            </div>
          ) : (
            <div className="relative mt-5">
              <ScanLine />
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
