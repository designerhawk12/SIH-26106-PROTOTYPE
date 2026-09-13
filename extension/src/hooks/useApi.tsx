const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export interface EmailSummary {
  id: string;
  subject: string;
  sender: string;
  to: string | null;
  date: string | null;
  message_id: string | null;
  internal_date?: number;
}

export interface EmailPage {
  emails: EmailSummary[];
  next_page_token: string | null;
  result_size_estimate: number;
}

export interface GeoLocation {
  ip: string;
  country: string | null;
  city: string | null;
  lat: number | null;
  lon: number | null;
  isp?: string | null;
  source?: string;
  ok: boolean;
}

export interface Hop {
  raw: string;
  from_host: string | null;
  by_host: string | null;
  ip: string | null;
  geo?: GeoLocation | null;
}

export interface ScanResult {
  email: {
    subject: string | null;
    from: string | null;
    to: string[];
    date: string | null;
    message_id: string | null;
  };

  headers: {
    reply_to: string | null;
    return_path: string | null;
    reply_to_mismatch: boolean;
  };

  received_chain: Hop[];

  authentication: {
    spf: string;
    dkim: string;
    dmarc: string;
  };

  indicators: {
    urls: string[];
    domains: string[];
    ips: string[];
  };

  geolocation: GeoLocation[];

  verdict: "clean" | "suspicious";

  parse_warnings: string[];
}

export async function fetchEmails(
  limit = 10,
  pageToken?: string | null,
): Promise<EmailPage> {
  const params = new URLSearchParams();

  params.set("limit", String(limit));

  if (pageToken) {
    params.set("page_token", pageToken);
  }

  const response = await fetch(
    `${API_BASE}/api/v1/extension/emails?${params.toString()}`,
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch emails (${response.status})`);
  }

  return response.json();
}

export async function scanEmail(messageId: string): Promise<ScanResult> {
  const response = await fetch(
    `${API_BASE}/api/v1/extension/emails/${encodeURIComponent(messageId)}/scan`,
    {
      method: "POST",
    },
  );

  if (!response.ok) {
    let message = `Scan failed (${response.status})`;

    try {
      const data = await response.json();

      if (data?.detail) {
        message = data.detail;
      }
    } catch {
      // Ignore response parsing errors.
    }

    throw new Error(message);
  }

  return response.json();
}
