export type UserRole = "ANALYST" | "SENIOR_ANALYST" | "ADMIN";

export type Permission =
  | "ANALYZE_EMAILS"
  | "INSPECT_CASES"
  | "GENERATE_REPORTS"
  | "EXPORT_EVIDENCE"
  | "CREATE_ANALYST_NOTES"
  | "REVIEW_CASES"
  | "ACCESS_CAMPAIGNS"
  | "MANAGE_USERS"
  | "VIEW_SYSTEM_CONFIGURATION";

export interface UserProfile {
  user_id: string;
  display_name: string;
  email: string;
  organization: string | null;
  role: UserRole;
  permissions: Permission[];
  created_at: string;
  updated_at: string;
}
