import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { AlertTriangle, BookmarkPlus, Play } from "lucide-react";

import { apiRequest } from "../api/client";
import { DossierReport } from "../components/dossier-report";
import type { ResearchRunArtifact } from "../research/artifact-types";
import type {
  CompanySummary,
  TrackedCompanySummary,
  WorkspaceSummary,
} from "../research/types";
import { postResearchStream } from "../streaming/research-stream";

export function CompanyDetailPage(): React.JSX.Element {
  const { companyId } = useParams({ strict: false }) as { companyId: string };
  const queryClient = useQueryClient();
  const company = useQuery({
    queryKey: ["company", companyId],
    queryFn: () => apiRequest<CompanySummary>(`/companies/${companyId}`),
  });
  const workspaceId = company.data?.workspace_id;
  const workspace = useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () => {
      if (!workspaceId) throw new Error("Workspace is unavailable");
      return apiRequest<WorkspaceSummary>(`/workspaces/${workspaceId}`);
    },
    enabled: Boolean(workspaceId),
  });
  const latestRun = useQuery({
    queryKey: ["company-latest-run", companyId],
    queryFn: () =>
      apiRequest<ResearchRunArtifact>(
        `/companies/${companyId}/research-runs/latest`,
      ),
    retry: false,
  });
  const track = useMutation({
    mutationFn: () =>
      apiRequest<TrackedCompanySummary>(`/companies/${companyId}/tracking`, {
        method: "PUT",
        body: JSON.stringify({ monitoring_preferences: { news: true } }),
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["tracked-companies"] }),
  });
  const resumeRun = useMutation({
    mutationFn: async (runId: string) => {
      for await (const event of postResearchStream(
        `/research-runs/${runId}/resume`,
        {},
      )) {
        if (event.payload.kind === "error") {
          throw new Error(event.payload.message);
        }
      }
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["company-latest-run", companyId],
        }),
        queryClient.invalidateQueries({ queryKey: ["company", companyId] }),
      ]);
    },
  });

  if (company.isPending) {
    return (
      <output className="mx-auto block max-w-6xl text-sm text-ink-secondary">
        Loading company…
      </output>
    );
  }

  if (company.isError) {
    return (
      <p role="alert" className="mx-auto max-w-6xl text-sm text-red-800">
        {company.error.message}
      </p>
    );
  }

  return (
    <section className="mx-auto max-w-6xl">
      {company.data ? (
        <Link
          to="/workspaces/$workspaceId"
          params={{ workspaceId: company.data.workspace_id }}
          className="text-link text-sm"
        >
          Back to workspace
        </Link>
      ) : null}
      <div className="mt-5 flex flex-col justify-between gap-6 md:flex-row md:items-start">
        <div>
          {company.data.industry ? (
            <p className="eyebrow">{company.data.industry}</p>
          ) : null}
          <h1 className="page-title mt-2">
            {company.data?.display_name ?? "Company"}
          </h1>
          {company.data.description ? (
            <p className="mt-3 max-w-[68ch] text-ink-secondary">
              {company.data.description}
            </p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={() => track.mutate()}
          disabled={track.isPending || track.isSuccess}
          className="button-secondary shrink-0 self-start"
        >
          <BookmarkPlus aria-hidden="true" size={18} />{" "}
          {track.isSuccess
            ? "Company tracked"
            : track.isPending
              ? "Tracking…"
              : "Track company"}
        </button>
      </div>
      {track.error ? (
        <p role="alert" className="mt-3 text-sm text-red-800">
          {track.error.message}
        </p>
      ) : null}
      {latestRun.data?.status === "paused" ? (
        <div className="mt-8 flex flex-col items-start justify-between gap-5 rounded-xl border border-amber-300 bg-amber-50 p-5 text-amber-950 shadow-quiet sm:flex-row">
          <div className="flex gap-3">
            <AlertTriangle
              className="mt-0.5 shrink-0"
              aria-hidden="true"
              size={20}
            />
            <div>
              <h2 className="font-semibold">Research paused</h2>
              <p className="mt-1 text-sm">
                Resume from{" "}
                {latestRun.data.resume_stage?.replaceAll("_", " ") ??
                  "the saved checkpoint"}
                .
              </p>
              {resumeRun.error ? (
                <p role="alert" className="mt-2 text-sm">
                  {resumeRun.error.message}
                </p>
              ) : null}
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              if (latestRun.data) resumeRun.mutate(latestRun.data.id);
            }}
            disabled={resumeRun.isPending}
            className="button-primary shrink-0"
          >
            <Play aria-hidden="true" size={17} />
            {resumeRun.isPending ? "Resuming…" : "Resume research"}
          </button>
        </div>
      ) : null}
      {latestRun.data?.final_report ? (
        <div className="mt-12 border-t border-hairline pt-8">
          {latestRun.data.comparison_id ? (
            <div className="mb-4 flex justify-end">
              <Link
                to="/comparisons/$comparisonId"
                params={{ comparisonId: latestRun.data.comparison_id }}
                className="text-link text-sm"
              >
                Open comparison view
              </Link>
            </div>
          ) : null}
          <DossierReport
            markdown={latestRun.data.final_report}
            evidence={latestRun.data.evidence}
            conversationId={latestRun.data.conversation_id}
            coverageScore={latestRun.data.coverage_score}
            confidenceScore={latestRun.data.confidence_score}
            label={workspace.data?.name ?? company.data.display_name}
          />
        </div>
      ) : null}
    </section>
  );
}
