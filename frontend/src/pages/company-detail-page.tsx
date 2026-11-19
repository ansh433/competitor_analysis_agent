import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { AlertTriangle, BookmarkPlus, ExternalLink, Play } from "lucide-react";

import { apiRequest } from "../api/client";
import { DossierReport } from "../components/dossier-report";
import type { ResearchRunArtifact } from "../research/artifact-types";
import type { CompanySummary, TrackedCompanySummary } from "../research/types";
import { postResearchStream } from "../streaming/research-stream";

export function CompanyDetailPage(): React.JSX.Element {
  const { companyId } = useParams({ strict: false }) as { companyId: string };
  const queryClient = useQueryClient();
  const company = useQuery({
    queryKey: ["company", companyId],
    queryFn: () => apiRequest<CompanySummary>(`/companies/${companyId}`),
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

  return (
    <section className="max-w-6xl">
      {company.data ? (
        <Link
          to="/workspaces/$workspaceId"
          params={{ workspaceId: company.data.workspace_id }}
          className="text-sm text-[var(--teal)] underline"
        >
          Back to workspace
        </Link>
      ) : null}
      <div className="mt-5 flex flex-col justify-between gap-6 md:flex-row md:items-start">
        <div>
          <p className="text-sm font-semibold text-[var(--teal)]">
            {company.data?.industry ?? "Industry not yet sourced"}
          </p>
          <h1 className="mt-2 font-display text-5xl text-[var(--navy)]">
            {company.data?.display_name ?? "Company"}
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-[var(--muted)]">
            {company.data?.description ??
              "Run research to build this canonical profile."}
          </p>
        </div>
        <button
          type="button"
          onClick={() => track.mutate()}
          disabled={track.isPending}
          className="inline-flex min-h-11 items-center gap-2 border border-[var(--navy)] px-4 font-semibold text-[var(--navy)]"
        >
          <BookmarkPlus aria-hidden="true" size={18} /> Track company
        </button>
      </div>
      <dl className="mt-10 grid border-y border-[var(--line)] md:grid-cols-3">
        <div className="py-5 md:border-r md:border-[var(--line)] md:px-5">
          <dt className="text-sm text-[var(--muted)]">Domain</dt>
          <dd className="mt-1 font-medium">
            {company.data?.domain ?? "Unavailable"}
          </dd>
        </div>
        <div className="py-5 md:border-r md:border-[var(--line)] md:px-5">
          <dt className="text-sm text-[var(--muted)]">Headquarters</dt>
          <dd className="mt-1 font-medium">
            {company.data?.headquarters ?? "Unavailable"}
          </dd>
        </div>
        <div className="py-5 md:px-5">
          <dt className="text-sm text-[var(--muted)]">Research status</dt>
          <dd className="mt-1 font-medium">
            {company.data?.research_status.replaceAll("_", " ")}
          </dd>
        </div>
      </dl>
      {company.data?.website ? (
        <a
          href={company.data.website}
          target="_blank"
          rel="noreferrer"
          className="mt-6 inline-flex items-center gap-2 text-sm text-[var(--teal)] underline"
        >
          Visit official website <ExternalLink aria-hidden="true" size={15} />
        </a>
      ) : null}
      {latestRun.data?.status === "paused" ? (
        <div className="mt-8 flex items-start justify-between gap-6 border border-amber-300 bg-amber-50 p-5 text-amber-950">
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
            className="inline-flex min-h-11 shrink-0 items-center gap-2 bg-[var(--navy)] px-4 font-semibold text-white disabled:opacity-50"
          >
            <Play aria-hidden="true" size={17} />
            {resumeRun.isPending ? "Resuming…" : "Resume research"}
          </button>
        </div>
      ) : null}
      {latestRun.data?.final_report ? (
        <div className="mt-12 border-t border-[var(--line)] pt-8">
          <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-[var(--teal)]">
                Latest completed run
              </p>
              <h2 className="mt-1 font-display text-3xl">
                Decision-ready dossier
              </h2>
            </div>
            {latestRun.data.comparison_id ? (
              <Link
                to="/comparisons/$comparisonId"
                params={{ comparisonId: latestRun.data.comparison_id }}
                className="text-sm text-[var(--teal)] underline"
              >
                Open full comparison
              </Link>
            ) : null}
          </div>
          <DossierReport
            markdown={latestRun.data.final_report}
            evidence={latestRun.data.evidence}
            conversationId={latestRun.data.conversation_id}
          />
        </div>
      ) : null}
    </section>
  );
}
