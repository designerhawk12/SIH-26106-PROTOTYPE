import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { AlertOctagon, Fish, Landmark, Mail, Paperclip, ShieldAlert } from "lucide-react";
import { AuthFailuresCard } from "@/components/dashboard/AuthFailuresCard";
import { RecentInvestigations } from "@/components/dashboard/RecentInvestigations";
import { StatCard } from "@/components/dashboard/StatCard";
import { ThreatClassificationChart } from "@/components/dashboard/ThreatClassificationChart";
import { InfrastructureHop } from "@/components/infrastructure/InfrastructureHop";
import { ActionButton } from "@/components/ui/ActionButton";
import { Panel } from "@/components/ui/Panel";
import { RiskScore } from "@/components/ui/RiskScore";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { ThreatBadge } from "@/components/ui/ThreatBadge";
import { getCase, getDashboardStats, listCases } from "@/services/api";

export function DashboardPage() {
  const stats = useQuery({ queryKey: ["dashboard-stats"], queryFn: getDashboardStats });
  const cases = useQuery({ queryKey: ["cases"], queryFn: listCases });
  const featuredCaseId = cases.data?.[0]?.case_id;
  const featured = useQuery({
    queryKey: ["case", featuredCaseId],
    queryFn: () => getCase(featuredCaseId!),
    enabled: Boolean(featuredCaseId),
  });

  const s = stats.data;

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
        className="grid items-end gap-4 lg:grid-cols-[1fr_360px]"
      >
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-accent">
            Email Security Command Center
          </p>
          <h1 className="mt-3 text-4xl font-bold leading-[1.05] tracking-tight text-foreground lg:text-5xl">
            Threat Intelligence
            <br />
            Overview
          </h1>
        </div>
        <div className="relative hidden h-44 items-end justify-end lg:flex">
          <Link to="/analyze" className="mb-2 mr-2">
            <ActionButton arrow>Analyze Email</ActionButton>
          </Link>
        </div>
        <Link to="/analyze" className="lg:hidden">
          <ActionButton arrow>Analyze Email</ActionButton>
        </Link>
      </motion.div>

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <StatCard
          className="col-span-2"
          label="Emails Analyzed"
          value={s?.emails_analyzed ?? 0}
          icon={Mail}
          index={0}
        />
        <StatCard
          label="Threats Detected"
          value={s?.threats_detected ?? 0}
          icon={ShieldAlert}
          tone="accent"
          index={1}
        />
        <StatCard
          label="High Risk"
          value={s?.high_risk ?? 0}
          icon={AlertOctagon}
          tone="danger"
          index={2}
        />
        <StatCard label="Phishing" value={s?.phishing ?? 0} icon={Fish} tone="warning" index={3} />
        <StatCard
          label="Business Email Compromise"
          value={s?.business_email_compromise ?? 0}
          icon={Landmark}
          tone="ai"
          index={4}
          className="col-span-2"
        />
        <StatCard
          label="Suspicious Attachments"
          value={s?.suspicious_attachments ?? 0}
          icon={Paperclip}
          tone="network"
          index={5}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Panel sweep spotlight tilt tone="danger" className="border-danger/15 xl:col-span-2">
          <div className="flex flex-col items-center gap-8 p-6 lg:flex-row lg:p-8">
            {featured.data?.risk && (
              <RiskScore score={featured.data.risk.score} level={featured.data.risk.level} />
            )}
            <div className="min-w-0 flex-1">
              <p className="font-mono text-[10px] uppercase tracking-[0.28em] text-accent">
                Highest priority open case
              </p>
              <h2 className="mt-3 text-2xl font-bold leading-tight tracking-tight">
                {featured.data?.email.subject ?? "Loading case…"}
              </h2>
              <p className="mt-2 font-mono text-xs text-muted-foreground">
                {featured.data?.email.sender}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {featured.data?.risk?.classification.map((item, i) => (
                  <ThreatBadge key={item} label={item} tone={i === 0 ? "danger" : "warning"} />
                ))}
              </div>
              {featured.data && (
                <Link
                  to="/cases/$caseId"
                  params={{ caseId: featured.data.case_id }}
                  className="mt-6 inline-block"
                >
                  <ActionButton variant="secondary" arrow>
                    Open Investigation
                  </ActionButton>
                </Link>
              )}
            </div>
          </div>
        </Panel>

        {s && <ThreatClassificationChart data={s.classification_breakdown} />}
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <RecentInvestigations cases={cases.data ?? []} />
        </div>
        {s && <AuthFailuresCard failures={s.authentication_failures} />}
      </div>

      <div>
        <SectionHeader
          eyebrow="Network"
          title="Infrastructure Observations"
          subtitle="Routing infrastructure most frequently observed across recent malicious submissions."
          className="mb-4"
        />
        <div className="grid gap-4 lg:grid-cols-3">
          {featured.data?.infrastructure.nodes.map((node, i) => (
            <InfrastructureHop key={node.ip} node={node} index={i} isLast />
          ))}
        </div>
      </div>
    </div>
  );
}
