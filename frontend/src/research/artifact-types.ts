export interface EvidenceArtifact {
  id: string;
  research_run_id?: string;
  claim: string;
  source_title?: string;
  source_url: string;
  publisher?: string | null;
  relevant_excerpt?: string;
  evidence_type?: string;
  confidence: number;
  fact_classification?: string;
  verification_status?: string;
  rejection_reason?: string | null;
  retrieval_timestamp?: string;
}

export interface ResearchRunArtifact {
  id: string;
  workspace_id: string;
  company_id: string;
  conversation_id: string;
  objective: string;
  status: "pending" | "running" | "completed" | "failed";
  model_used: string;
  final_report: string | null;
  confidence_score: number | null;
  coverage_score: number | null;
  error_message: string | null;
  evidence: EvidenceArtifact[];
  comparison_id: string | null;
}

export interface ComparisonArtifactData {
  id: string;
  workspace_id: string;
  research_run_id: string | null;
  company_ids: string[];
  comparison_dimensions: string[];
  structured_result: Record<string, unknown>;
  generated_at: string;
}

