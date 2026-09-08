export type AuditAction =
  | "CASE_ANALYZED"
  | "REPORT_GENERATED"
  | "EVIDENCE_EXPORTED"
  | "NOTE_ADDED"
  | "NOTE_UPDATED"
  | "NOTE_DELETED"
  | "IOC_WATCHLISTED"
  | "IOC_UNWATCHLISTED"
  | "ROLE_CHANGED";

export interface AnalystNote {
  note_id: string;
  case_id: string;
  author_user_id: string;
  author_display_name: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface AuditEvent {
  event_id: string;
  actor_user_id: string | null;
  action: AuditAction;
  resource_type: string;
  resource_id: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}

export interface WatchlistEntry {
  watchlist_id: string;
  ioc_type: "IP_ADDRESS" | "DOMAIN" | "URL" | "ATTACHMENT_SHA256";
  value: string;
  created_by_user_id: string;
  created_by_display_name: string;
  reason: string | null;
  created_at: string;
}
