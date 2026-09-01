/**
 * Mock data matching the frontend data contract in `src/types/analysis.ts`.
 * Replace consumption of these objects by real API calls in `src/services/api.ts`.
 */
import type { CaseSummary, DashboardStats, EmailAnalysis } from "@/types/analysis";

export const sampleAnalysis: EmailAnalysis = {
  case_id: "CASE-2026-0417",
  created_at: "2026-08-31T14:03:11Z",
  status: "in_review",
  email: {
    subject: "URGENT: Updated wire instructions for invoice INV-88214",
    sender: "accounts@vendor-payments-secure.com",
    sender_display_name: "Laura Whitfield (Finance)",
    receiver: "finance@northbridge-industrial.com",
    date: "2026-08-31T13:58:02Z",
    message_id: "<9f2c1a44-3b17-4d8a-91cc-0f7f2ad0a1e5@vendor-payments-secure.com>",
    reply_to: "l.whitfield@secure-vendor-mail.net",
    return_path: "bounce@mail-relay-77.hostcluster.ru",
  },
  risk: {
    score: 87,
    level: "HIGH",
    indicator_count: 6,
    classification: ["Phishing", "Business Email Compromise", "Social Engineering"],
    summary:
      "The message impersonates a known finance contact, fails all sender authentication checks and requests an urgent change of payment destination. Routing infrastructure has negative reputation.",
    signals: [
      {
        label: "SPF authentication failed",
        weight: 10,
        detail:
          "The sending IP is not authorised to send mail for vendor-payments-secure.com according to the published SPF record.",
        category: "authentication",
      },
      {
        label: "DMARC authentication failed",
        weight: 12,
        detail:
          "DMARC alignment failed for both SPF and DKIM identifiers, meaning the visible From domain could not be validated.",
        category: "authentication",
      },
      {
        label: "Display-name impersonation detected",
        weight: 12,
        detail:
          "The display name matches an internal finance contact while the underlying address belongs to an unrelated external domain.",
        category: "identity",
      },
      {
        label: "Urgent payment request",
        weight: 10,
        detail:
          "Message body applies time pressure and requests immediate action on a financial transaction.",
        category: "content",
      },
      {
        label: "Business Email Compromise pattern",
        weight: 15,
        detail:
          "Combination of vendor impersonation, changed bank details and urgency matches known BEC tradecraft.",
        category: "content",
      },
      {
        label: "Suspicious URL",
        weight: 10,
        detail:
          "A link points to a lookalike domain registered 6 days ago serving a credential collection page.",
        category: "content",
      },
      {
        label: "Negative infrastructure reputation",
        weight: 12,
        detail:
          "Two observed relay addresses appear on multiple abuse feeds associated with credential phishing campaigns.",
        category: "infrastructure",
      },
    ],
  },
  authentication: {
    spf: {
      result: "FAIL",
      domain: "vendor-payments-secure.com",
      explanation: "Sending IP 185.203.116.44 is not listed in the SPF record for the From domain.",
    },
    dkim: {
      result: "PASS",
      domain: "secure-vendor-mail.net",
      explanation:
        "A valid DKIM signature was found, but it was signed by a domain unrelated to the visible sender.",
    },
    dmarc: {
      result: "FAIL",
      domain: "vendor-payments-secure.com",
      explanation: "No DMARC alignment achieved; the published policy requests quarantine.",
    },
  },
  mime: {
    content_type: "multipart/mixed",
    size_bytes: 184320,
    children: [
      { content_type: "text/plain", size_bytes: 1842 },
      { content_type: "text/html", size_bytes: 9214 },
      {
        content_type: "application/pdf",
        size_bytes: 172_104,
        filename: "Invoice_INV-88214_Updated.pdf",
      },
    ],
  },
  received_chain: [
    {
      index: 0,
      from_host: "mail-relay-77.hostcluster.ru",
      by_host: "edge-04.transit-net.io",
      protocol: "ESMTP",
      timestamp: "2026-08-31T13:58:02Z",
      ip: "185.203.116.44",
    },
    {
      index: 1,
      from_host: "edge-04.transit-net.io",
      by_host: "mx-inbound-2.protection.mailgate.net",
      protocol: "ESMTPS",
      timestamp: "2026-08-31T13:58:05Z",
      ip: "45.147.230.19",
    },
    {
      index: 2,
      from_host: "mx-inbound-2.protection.mailgate.net",
      by_host: "mx1.northbridge-industrial.com",
      protocol: "ESMTPS",
      timestamp: "2026-08-31T13:58:09Z",
      ip: "104.47.55.108",
    },
  ],
  indicators: {
    ips: [
      { ip: "185.203.116.44", reputation: "malicious", source: "Abuse feed / passive DNS" },
      { ip: "45.147.230.19", reputation: "suspicious", source: "Transit relay telemetry" },
      { ip: "104.47.55.108", reputation: "clean", source: "Recipient gateway" },
    ],
    domains: [
      { domain: "vendor-payments-secure.com", reputation: "malicious", type: "sender" },
      { domain: "secure-vendor-mail.net", reputation: "suspicious", type: "reply-to" },
      { domain: "northbridge-industrial.com", reputation: "clean", type: "recipient" },
    ],
    urls: [
      {
        url: "https://vendor-payments-secure.com/portal/verify?ref=INV88214",
        domain: "vendor-payments-secure.com",
        reputation: "malicious",
      },
      {
        url: "https://cdn.transit-net.io/assets/logo.png",
        domain: "cdn.transit-net.io",
        reputation: "neutral",
      },
    ],
    attachments: [
      {
        filename: "Invoice_INV-88214_Updated.pdf",
        mime_type: "application/pdf",
        size_bytes: 172_104,
        sha256: "9f8b2c1e4a77d3b0c5e6f1a9d84b7c2e35f60a91cc7d4e28b3a5f0d6172c94ab",
        status: "suspicious",
      },
    ],
  },
  infrastructure: {
    disclaimer:
      "Observed infrastructure information represents routing/network infrastructure associated with the email and does not establish the physical location or identity of the attacker.",
    nodes: [
      {
        index: 0,
        role: "Observed origin",
        ip: "185.203.116.44",
        country: "Netherlands",
        region: "North Holland",
        city: "Amsterdam",
        isp: "Hostcluster B.V.",
        asn: "AS210644",
        reputation: "malicious",
      },
      {
        index: 1,
        role: "Transit relay",
        ip: "45.147.230.19",
        country: "Germany",
        region: "Hesse",
        city: "Frankfurt",
        isp: "Transit Networks GmbH",
        asn: "AS49505",
        reputation: "suspicious",
      },
      {
        index: 2,
        role: "Receiving mail server",
        ip: "104.47.55.108",
        country: "Ireland",
        region: "Leinster",
        city: "Dublin",
        isp: "Mailgate Protection",
        asn: "AS8075",
        reputation: "clean",
      },
    ],
  },
  ai_findings: [
    {
      type: "phishing",
      title: "Phishing",
      detected: true,
      confidence: 0.94,
      evidence: ["Credential portal link", "Lookalike sender domain"],
      explanation: "Message directs the recipient to a credential collection page styled as a vendor portal.",
    },
    {
      type: "social_engineering",
      title: "Social Engineering",
      detected: true,
      confidence: 0.88,
      evidence: ["Authority cue", "Confidentiality request"],
      explanation: "Sender leverages authority and confidentiality to discourage verification.",
    },
    {
      type: "urgency",
      title: "Urgency",
      detected: true,
      confidence: 0.91,
      evidence: ["\"before end of day\"", "\"final notice\""],
      explanation: "Time pressure is applied to reduce the likelihood of out-of-band validation.",
    },
    {
      type: "credential_request",
      title: "Credential Request",
      detected: false,
      confidence: 0.21,
      evidence: [],
      explanation: "No direct request for account credentials was present in the message body.",
    },
    {
      type: "payment_request",
      title: "Payment Request",
      detected: true,
      confidence: 0.96,
      evidence: ["Updated IBAN provided", "Invoice reference INV-88214"],
      explanation: "The message asks for an outstanding invoice to be paid to a new bank account.",
    },
    {
      type: "impersonation",
      title: "Impersonation",
      detected: true,
      confidence: 0.9,
      evidence: ["Display name matches internal finance staff"],
      explanation: "Display name spoofing of a known internal contact was observed.",
    },
    {
      type: "business_email_compromise",
      title: "Business Email Compromise",
      detected: true,
      confidence: 0.93,
      evidence: ["Vendor impersonation", "Bank detail change", "Urgency"],
      explanation: "The message matches the standard vendor-invoice BEC pattern.",
    },
    {
      type: "suspicious_call_to_action",
      title: "Suspicious Call-to-Action",
      detected: true,
      confidence: 0.85,
      evidence: ["\"Confirm payment details here\" button"],
      explanation: "A prominent CTA routes to an untrusted external destination.",
    },
  ],
  timeline: [
    { timestamp: "14:03:11", label: "Email received for analysis" },
    { timestamp: "14:03:11", label: "SHA-256 evidence hash calculated" },
    { timestamp: "14:03:12", label: "MIME structure parsed" },
    { timestamp: "14:03:12", label: "Routing headers extracted" },
    { timestamp: "14:03:13", label: "Threat analysis completed" },
    { timestamp: "14:03:14", label: "Threat intelligence completed" },
    { timestamp: "14:03:14", label: "Risk score calculated" },
  ],
  evidence: {
    email_sha256: "c41d8fa3b17e9d0a5628f4b7cc19e0d3a6f28b45d7e1c9302f5a8b6d4e7091cf",
    attachment_hashes: [
      {
        filename: "Invoice_INV-88214_Updated.pdf",
        sha256: "9f8b2c1e4a77d3b0c5e6f1a9d84b7c2e35f60a91cc7d4e28b3a5f0d6172c94ab",
      },
    ],
    analyzed_at: "2026-08-31T14:03:14Z",
    case_id: "CASE-2026-0417",
    events: [
      { timestamp: "14:03:11", label: "Evidence acquired", detail: "Original .eml stored read-only" },
      { timestamp: "14:03:11", label: "Integrity hash computed", detail: "SHA-256" },
      { timestamp: "14:03:14", label: "Analysis sealed", detail: "Case snapshot written" },
    ],
  },
};

export const sampleCases: CaseSummary[] = [
  {
    case_id: "CASE-2026-0417",
    subject: "URGENT: Updated wire instructions for invoice INV-88214",
    sender: "accounts@vendor-payments-secure.com",
    risk_score: 87,
    risk_level: "HIGH",
    classification: ["Phishing", "Business Email Compromise"],
    created_at: "2026-08-31T14:03:11Z",
    status: "in_review",
  },
  {
    case_id: "CASE-2026-0416",
    subject: "Your mailbox storage is full — reactivate access",
    sender: "no-reply@mail-quota-alerts.net",
    risk_score: 94,
    risk_level: "CRITICAL",
    classification: ["Phishing", "Credential Harvesting"],
    created_at: "2026-08-31T11:47:02Z",
    status: "open",
  },
  {
    case_id: "CASE-2026-0415",
    subject: "Contract review — signed copy attached",
    sender: "legal@brightwater-partners.com",
    risk_score: 41,
    risk_level: "MEDIUM",
    classification: ["Suspicious Attachment"],
    created_at: "2026-08-30T16:22:40Z",
    status: "in_review",
  },
  {
    case_id: "CASE-2026-0414",
    subject: "Payroll adjustment confirmation",
    sender: "hr@northbridge-industrial.com",
    risk_score: 12,
    risk_level: "LOW",
    classification: ["Benign"],
    created_at: "2026-08-30T09:05:18Z",
    status: "closed",
  },
  {
    case_id: "CASE-2026-0413",
    subject: "RE: Q3 supplier onboarding — action required today",
    sender: "procurement@supplier-onboard-desk.com",
    risk_score: 78,
    risk_level: "HIGH",
    classification: ["Business Email Compromise", "Social Engineering"],
    created_at: "2026-08-29T18:44:09Z",
    status: "open",
  },
  {
    case_id: "CASE-2026-0412",
    subject: "Security alert: unusual sign-in blocked",
    sender: "alerts@identity-protection-mail.com",
    risk_score: 66,
    risk_level: "MEDIUM",
    classification: ["Phishing"],
    created_at: "2026-08-29T07:31:55Z",
    status: "closed",
  },
];

export const sampleStats: DashboardStats = {
  emails_analyzed: 12_483,
  threats_detected: 1_942,
  high_risk: 318,
  phishing: 1_104,
  business_email_compromise: 267,
  suspicious_attachments: 412,
  authentication_failures: { spf: 486, dkim: 233, dmarc: 571 },
  classification_breakdown: [
    { label: "Phishing", count: 1104 },
    { label: "BEC", count: 267 },
    { label: "Malware", count: 188 },
    { label: "Spoofing", count: 241 },
    { label: "Spam", count: 142 },
  ],
};
