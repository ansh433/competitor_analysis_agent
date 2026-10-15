export interface WorkspaceSummary {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompanySummary {
  id: string;
  workspace_id: string;
  legal_name: string | null;
  display_name: string;
  website: string | null;
  domain: string | null;
  industry: string | null;
  headquarters: string | null;
  description: string | null;
  research_status: "unresearched" | "in_progress" | "researched" | "needs_refresh";
  created_at: string;
  updated_at: string;
}

export interface TrackedCompanySummary {
  id: string;
  workspace_id: string;
  company_id: string;
  monitoring_preferences: Record<string, unknown> | null;
  created_at: string;
}

