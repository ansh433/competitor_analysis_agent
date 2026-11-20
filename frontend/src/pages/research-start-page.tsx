import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowRight } from "lucide-react";
import { type FormEvent, useState } from "react";

import { apiRequest } from "../api/client";
import {
  ResearchProgress,
  type ResearchStageView,
  type ToolExecutionView,
} from "../components/research-progress";
import type { ResearchEventPayload } from "../proto/competitor-events";
import { useQuotaStatus } from "../quotas/use-quota";
import type {
  EvidenceArtifact,
  ResearchRunArtifact,
} from "../research/artifact-types";
import {
  clearResearchCompanyPrefill,
  getResearchCompanyPrefill,
} from "../research/prefill";
import type { WorkspaceSummary } from "../research/types";
import { postResearchStream } from "../streaming/research-stream";

interface ResearchViewState {
  stages: ResearchStageView[];
  tools: ToolExecutionView[];
  sources: Array<{ sourceId: string; title: string; publisher: string }>;
  streamedText: string;
  isFinished: boolean;
  error: string | null;
  evidence: EvidenceArtifact[];
  gaps: Array<{ gapId: string; question: string; reportSection: string }>;
  comparison: Record<string, unknown> | null;
  conversationId: string | null;
  researchRunId: string | null;
  isPaused: boolean;
}

const initialResearchState: ResearchViewState = {
  stages: [],
  tools: [],
  sources: [],
  streamedText: "",
  isFinished: false,
  error: null,
  evidence: [],
  gaps: [],
  comparison: null,
  conversationId: null,
  researchRunId: null,
  isPaused: false,
};

export function ResearchStartPage(): React.JSX.Element {
  const quota = useQuotaStatus();
  const queryClient = useQueryClient();
  const workspaces = useQuery({
    queryKey: ["workspaces"],
    queryFn: () =>
      apiRequest<{ workspaces: WorkspaceSummary[]; total: number }>(
        "/workspaces",
      ),
  });
  const [research, setResearch] =
    useState<ResearchViewState>(initialResearchState);
  const [isRunning, setIsRunning] = useState(false);
  const isDisabled = !quota.isLoading && !quota.data?.can_start_research;

  async function handleStartResearch(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    setResearch(initialResearchState);
    setIsRunning(true);
    const data = new FormData(event.currentTarget);
    const company = String(data.get("company") ?? "");
    const objective = String(data.get("objective") ?? "");
    clearResearchCompanyPrefill();
    try {
      const researchRun = await apiRequest<ResearchRunArtifact>(
        "/research-runs",
        {
          method: "POST",
          body: JSON.stringify({
            workspace_id: String(data.get("workspaceId") ?? ""),
            company_name_or_url: company,
            objective,
            model_tier: String(data.get("modelTier") ?? "standard"),
          }),
        },
      );
      setResearch((current) => ({
        ...current,
        researchRunId: researchRun.id,
        conversationId: researchRun.conversation_id,
      }));
      for await (const event of postResearchStream(
        `/research-runs/${researchRun.id}/stream`,
        {},
      )) {
        setResearch((current) => applyPayload(current, event.payload));
      }
      void queryClient.invalidateQueries({ queryKey: ["quota-status"] });
    } catch (error) {
      setResearch((current) => ({
        ...current,
        error: error instanceof Error ? error.message : "Research failed",
      }));
    } finally {
      setIsRunning(false);
    }
  }

  async function handleResumeResearch(): Promise<void> {
    if (!research.researchRunId) return;
    setIsRunning(true);
    setResearch((current) => ({
      ...current,
      error: null,
      isPaused: false,
      isFinished: false,
    }));
    try {
      for await (const event of postResearchStream(
        `/research-runs/${research.researchRunId}/resume`,
        {},
      )) {
        setResearch((current) => applyPayload(current, event.payload));
      }
    } catch (error) {
      setResearch((current) => ({
        ...current,
        error: error instanceof Error ? error.message : "Resume failed",
      }));
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <section className="mx-auto max-w-5xl">
      <header>
        <h1 className="page-title">Start research</h1>
        <p className="mt-3 max-w-xl text-sm leading-6 text-ink-secondary">
          Define the company and the decision to investigate.
        </p>
      </header>

      {isDisabled ? (
        <div
          role="alert"
          className="mt-6 flex gap-3 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm leading-6 text-amber-950 shadow-quiet"
        >
          <AlertTriangle
            className="mt-0.5 shrink-0"
            aria-hidden="true"
            size={20}
          />
          Daily research allowance exhausted. Existing dossiers remain available
          until the quota resets.
        </div>
      ) : null}

      <div className="mt-8">
        <div className="min-w-0">
          <form
            onSubmit={handleStartResearch}
            aria-label="Research brief"
            className="surface-card space-y-6 p-5 sm:p-7"
          >
            <div className="grid gap-5 sm:grid-cols-2">
              <label className="block min-w-0 text-sm font-medium">
                Workspace
                <select
                  name="workspaceId"
                  required
                  className="form-input"
                  disabled={isDisabled}
                >
                  <option value="">Select a workspace</option>
                  {workspaces.data?.workspaces.map((workspace) => (
                    <option key={workspace.id} value={workspace.id}>
                      {workspace.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block min-w-0 text-sm font-medium">
                Model tier
                <select
                  name="modelTier"
                  className="form-input"
                  disabled={isDisabled}
                >
                  <option value="standard">Standard research</option>
                  <option value="upgraded">Upgraded model</option>
                </select>
              </label>
            </div>
            <label className="block text-sm font-medium">
              Company name or website
              <input
                name="company"
                required
                className="form-input"
                defaultValue={getResearchCompanyPrefill()}
                placeholder="Example: Linear or linear.app"
                disabled={isDisabled}
              />
            </label>
            <label className="block text-sm font-medium">
              Research objective
              <textarea
                name="objective"
                required
                className="form-input min-h-36 resize-y"
                placeholder="Assess differentiation and pricing for a market-entry decision."
                disabled={isDisabled}
              />
            </label>
            <div className="border-t border-hairline pt-6">
              <button
                type="submit"
                disabled={isDisabled || quota.isLoading || isRunning}
                className="button-primary min-h-12 w-full px-5 sm:w-auto"
              >
                {isRunning ? "Researching…" : "Begin research"}{" "}
                <ArrowRight aria-hidden="true" size={18} />
              </button>
            </div>
          </form>
        </div>
      </div>
      {research.error ? (
        <div
          role="alert"
          className="mt-6 rounded-xl border border-amber-300 bg-amber-50 p-4 text-amber-950 shadow-quiet"
        >
          <p>{research.error}</p>
          {research.isPaused ? (
            <button
              type="button"
              onClick={() => void handleResumeResearch()}
              disabled={isRunning}
              className="button-primary mt-4"
            >
              {isRunning ? "Resuming…" : "Resume research"}
            </button>
          ) : null}
        </div>
      ) : null}
      {isRunning || research.stages.length > 0 ? (
        <ResearchProgress {...research} />
      ) : null}
    </section>
  );
}

function applyPayload(
  state: ResearchViewState,
  payload: ResearchEventPayload,
): ResearchViewState {
  if (payload.kind === "conversation_identified")
    return { ...state, conversationId: payload.conversationId };
  if (payload.kind === "research_run_identified")
    return { ...state, researchRunId: payload.researchRunId };
  if (payload.kind === "graph_stage_started") {
    return {
      ...state,
      stages: [
        ...state.stages,
        { name: payload.stageName, detail: payload.detail, status: "active" },
      ],
    };
  }
  if (payload.kind === "graph_stage_ended") {
    return {
      ...state,
      stages: state.stages.map((stage) =>
        stage.name === payload.stageName
          ? { ...stage, detail: payload.detail, status: "complete" }
          : stage,
      ),
    };
  }
  if (payload.kind === "tool_started") {
    return {
      ...state,
      tools: [
        ...state.tools,
        {
          executionId: payload.executionId,
          name: payload.toolName,
          status: "active",
        },
      ],
    };
  }
  if (payload.kind === "tool_ended") {
    return {
      ...state,
      tools: state.tools.map((tool) =>
        tool.executionId === payload.executionId
          ? {
              ...tool,
              status: payload.success ? "complete" : "failed",
              executionTimeMs: payload.executionTimeMs,
            }
          : tool,
      ),
    };
  }
  if (payload.kind === "source_discovered") {
    return {
      ...state,
      sources: [
        ...state.sources,
        {
          sourceId: payload.sourceId,
          title: payload.title,
          publisher: payload.publisher,
        },
      ],
    };
  }
  if (payload.kind === "evidence_accepted") {
    return {
      ...state,
      evidence: [
        ...state.evidence,
        {
          id: payload.evidenceId,
          claim: payload.claim,
          source_url: payload.sourceUrl,
          confidence: payload.confidence,
        },
      ],
    };
  }
  if (payload.kind === "research_gap_found") {
    return {
      ...state,
      gaps: [
        ...state.gaps,
        {
          gapId: payload.gapId,
          question: payload.question,
          reportSection: payload.reportSection,
        },
      ],
    };
  }
  if (payload.kind === "comparison_artifact")
    return { ...state, comparison: payload.structuredResult };
  if (payload.kind === "text_chunk")
    return { ...state, streamedText: state.streamedText + payload.text };
  if (payload.kind === "final_report_artifact")
    return { ...state, streamedText: payload.reportMarkdown };
  if (payload.kind === "error")
    return {
      ...state,
      error: payload.message,
      isPaused: payload.code === "research_run_paused",
    };
  if (payload.kind === "finished") return { ...state, isFinished: true };
  return state;
}
