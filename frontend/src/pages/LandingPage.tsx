import { Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Fingerprint, Globe2, ScanLine, Sparkles } from "lucide-react";
import { CursorGlow } from "@/components/effects/CursorGlow";
import { ActionButton } from "@/components/ui/ActionButton";
import { CyberBlocks } from "@/components/ui/CyberBlocks";
import { Panel } from "@/components/ui/Panel";

const capabilities = [
  {
    icon: ScanLine,
    title: "Email Forensics",
    body: "Header, MIME and routing analysis of raw .eml evidence with a preserved case record.",
  },
  {
    icon: Sparkles,
    title: "AI Threat Intent",
    body: "Phishing, impersonation, urgency and BEC patterns surfaced with confidence and evidence.",
  },
  {
    icon: Globe2,
    title: "Observed Infrastructure",
    body: "Routing infrastructure mapped hop by hop with reputation and network attribution context.",
  },
  {
    icon: Fingerprint,
    title: "Evidence Integrity",
    body: "SHA-256 hashing of the original message and every attachment at the moment of intake.",
  },
];

export function LandingPage() {
  return (
    <div className="relative isolate min-h-screen overflow-hidden bg-background">
      <div className="bg-grid pointer-events-none absolute inset-0 opacity-60" />
      <div className="pointer-events-none absolute left-1/2 top-[-160px] h-[620px] w-[1100px] -translate-x-1/2 rounded-full bg-accent/[0.06] blur-[160px]" />
      <CursorGlow />

      <div className="relative z-10 mx-auto max-w-[1200px] px-6 py-10">
        <header className="flex items-center justify-between">
          <p className="text-sm font-bold tracking-tight">SENTINEL MX</p>
          <Link to="/dashboard">
            <ActionButton variant="secondary" arrow>
              Open Console
            </ActionButton>
          </Link>
        </header>

        <section className="grid items-center gap-12 py-20 lg:grid-cols-[1.1fr_0.9fr]">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          >
            <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-accent">
              AI-Powered Email Threat Detection
            </p>
            <h1 className="mt-5 text-5xl font-bold leading-[0.98] tracking-tight lg:text-7xl">
              Forensic
              <br />
              intelligence for
              <br />
              <span className="text-accent text-accent-glow">email threats</span>
            </h1>
            <p className="mt-6 max-w-xl text-sm leading-relaxed text-muted-foreground">
              Submit suspicious messages, expose authentication failures, map observed routing
              infrastructure and document every finding as defensible investigation evidence.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/analyze">
                <ActionButton arrow>Analyze Email</ActionButton>
              </Link>
              <Link to="/dashboard">
                <ActionButton variant="secondary">View Dashboard</ActionButton>
              </Link>
            </div>
          </motion.div>

          <CyberBlocks className="mx-auto h-[min(360px,86vw)] w-[min(360px,86vw)]" />
        </section>

        <section className="grid gap-4 pb-24 sm:grid-cols-2 lg:grid-cols-4">
          {capabilities.map((item, i) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.1 + i * 0.07 }}
            >
              <Panel interactive spotlight tilt className="h-full p-5">
                <item.icon className="h-4 w-4 text-accent" />
                <p className="mt-4 text-sm font-semibold">{item.title}</p>
                <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{item.body}</p>
              </Panel>
            </motion.div>
          ))}
        </section>
      </div>
    </div>
  );
}
