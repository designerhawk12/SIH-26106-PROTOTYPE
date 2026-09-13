import { Link } from "@tanstack/react-router";
import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowDown,
  ArrowUpRight,
  ArrowRight,
  Fingerprint,
  Globe2,
  ScanLine,
  Sparkles,
} from "lucide-react";
import { HeroScene } from "@/components/landing/HeroScene";
import { LandingCursorLight } from "@/components/landing/LandingCursorLight";
import "@/components/landing/landing.css";

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
  const reduced = useReducedMotion();
  const reveal = (delay: number) => ({
    initial: { opacity: 0, y: reduced ? 0 : 20 },
    animate: { opacity: 1, y: 0 },
    transition: {
      duration: reduced ? 0 : 0.75,
      delay: reduced ? 0 : delay,
      ease: [0.22, 1, 0.36, 1] as const,
    },
  });
  return (
    <div className="sentinel-landing">
      <LandingCursorLight />
      <a href="#landing-main" className="landing-skip">
        Skip to content
      </a>
      <header className="landing-header landing-container">
        <Link to="/" className="landing-brand" aria-label="Sentinel MX home">
          <span className="landing-brand-mark" aria-hidden="true">
            <ScanLine size={19} strokeWidth={1.7} />
          </span>
          SENTINEL <span>MX</span>
        </Link>
        <nav aria-label="Homepage navigation" className="landing-nav">
          <a href="#capabilities">
            Platform capabilities <ArrowDown size={12} />
          </a>
        </nav>
        <Link to="/dashboard" className="landing-button landing-button-primary landing-console">
          Open Console <ArrowUpRight size={15} />
        </Link>
      </header>
      <main id="landing-main">
        <section className="landing-hero landing-container" aria-labelledby="hero-title">
          <div className="landing-hero-grid">
            <div className="landing-copy">
              <motion.p {...reveal(0.05)} className="landing-eyebrow">
                <span /> AI-POWERED EMAIL THREAT DETECTION
              </motion.p>
              <motion.h1 {...reveal(0.13)} id="hero-title">
                Forensic
                <br />
                intelligence for
                <br />
                <span>email threats</span>
              </motion.h1>
              <motion.p {...reveal(0.21)} className="landing-description">
                Submit suspicious messages, expose authentication failures, map observed routing
                infrastructure and document every finding as defensible investigation evidence.
              </motion.p>
            </div>
            <div className="landing-visual">
              <HeroScene />
            </div>
            <motion.div {...reveal(0.29)} className="landing-actions">
              <Link to="/analyze" className="landing-button landing-button-primary">
                Analyze Email <ArrowRight size={16} />
              </Link>
              <Link to="/dashboard" className="landing-button landing-button-secondary">
                View Dashboard <ArrowUpRight size={15} />
              </Link>
            </motion.div>
          </div>
          <div className="landing-statement">
            <span className="landing-section-number">01 / THE PLATFORM</span>
            <p>
              <span>Deterministic forensics.</span> Threat intelligence.
              <br className="landing-statement-break" /> AI-assisted investigation.
            </p>
            <a href="#capabilities" aria-label="Explore platform capabilities">
              <ArrowDown size={20} />
            </a>
          </div>
        </section>
        <section
          id="capabilities"
          className="landing-capabilities landing-container"
          aria-labelledby="capabilities-title"
        >
          <div className="landing-section-heading">
            <div>
              <p className="landing-eyebrow">FROM MESSAGE TO EVIDENCE</p>
              <h2 id="capabilities-title">
                Every signal.
                <br />
                <span>A clearer investigation.</span>
              </h2>
            </div>
            <p>
              Inspect the message. Connect the signals.
              <br />
              Keep the evidence intact.
            </p>
          </div>
          <div className="landing-card-grid">
            {capabilities.map((item, i) => (
              <motion.article
                key={item.title}
                className="landing-feature-card"
                initial={{ opacity: 0, y: reduced ? 0 : 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.15 }}
                transition={{ duration: reduced ? 0 : 0.5, delay: reduced ? 0 : i * 0.07 }}
              >
                <div className="landing-card-top">
                  <item.icon size={21} strokeWidth={1.5} />
                  <span>0{i + 1}</span>
                </div>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </motion.article>
            ))}
          </div>
        </section>
      </main>
      <footer className="landing-footer landing-container">
        <span>SENTINEL MX</span>
        <p>Email threat detection &amp; forensic intelligence</p>
        <a href="#landing-main">Back to top ↑</a>
      </footer>
    </div>
  );
}
