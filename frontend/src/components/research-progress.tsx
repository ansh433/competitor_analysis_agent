import { Check, CircleDashed } from "lucide-react";

import type { EvidenceArtifact } from "../research/artifact-types";
import { ComparisonMatrixView } from "./comparison-matrix";
import { DossierReport } from "./dossier-report";

export interface ResearchStageView {
  name: string;
  detail: string;
  status: "active" | "complete";
}

export interface ToolExecutionView {
  executionId: string;
  name: string;
  status: "active" | "complete" | "failed";
  executionTimeMs?: number;
}

interface ResearchProgressProps {
  stages: ResearchStageView[];
  tools: ToolExecutionView[];
  sources: Array<{ sourceId: string; title: string; publisher: string }>;
  streamedText: string;
  isFinished: boolean;
  evidence: EvidenceArtifact[];
  gaps: Array<{ gapId: string; question: string; reportSection: string }>;
  comparison: Record<string, unknown> | null;
  conversationId: string | null;
  isPaused: boolean;
}

export function ResearchProgress({
  stages,
  tools,
  sources,
  streamedText,
  isFinished,
  evidence,
  gaps,
  comparison,
  conversationId,
  isPaused,
}: ResearchProgressProps): React.JSX.Element {
  return (
    <section className="mt-10 min-w-0 space-y-6">
      <details className="surface-card px-5 py-4" open={!isFinished}>
        <summary className="cursor-pointer text-sm font-medium">
          Research activity
        </summary>
        <div className="mt-5 grid gap-6 md:grid-cols-2">
          <ol aria-label="Research stages" className="space-y-3">
            {stages.map((stage) => (
              <li
                key={`${stage.name}-${stage.status}`}
                className="flex gap-3 text-sm"
              >
                {stage.status === "complete" ? (
                  <Check
                    aria-hidden="true"
                    className="mt-0.5 shrink-0 text-teal"
                    size={17}
                  />
                ) : (
                  <CircleDashed
                    aria-hidden="true"
                    className="mt-0.5 shrink-0 motion-safe:animate-spin text-teal"
                    size={17}
                  />
                )}
                <span>
                  <strong className="block font-medium">
                    {stage.name.replaceAll("_", " ")}
                  </strong>
                  <span className="text-[var(--muted)]">{stage.detail}</span>
                </span>
              </li>
            ))}
          </ol>
          <ul aria-label="Tool timeline" className="space-y-3 text-sm">
            {tools.length === 0 ? (
              <li className="text-[var(--muted)]">No tools started yet.</li>
            ) : (
              tools.map((tool) => (
                <li
                  key={tool.executionId}
                  className="flex justify-between gap-3"
                >
                  <span>{tool.name.replaceAll("_", " ")}</span>
                  <span className="shrink-0 font-mono text-xs text-ink-muted">
                    {tool.status === "active"
                      ? "Running"
                      : tool.status === "failed"
                        ? "Failed"
                        : `${tool.executionTimeMs ?? 0} ms`}
                  </span>
                </li>
              ))
            )}
          </ul>
        </div>
      </details>
      <div className="surface-card min-w-0 overflow-hidden">
        <div className="flex items-center justify-between border-b border-hairline px-5 py-4">
          <h2 className="font-serif text-xl">Research output</h2>
          <output className="font-mono text-xs text-ink-muted">
            {isPaused ? "Paused" : isFinished ? "Complete" : "In progress"}
          </output>
        </div>
        <div className="min-h-64 p-5 leading-7 sm:p-6">
          {streamedText ? (
            <DossierReport
              markdown={streamedText}
              evidence={evidence}
              conversationId={conversationId ?? undefined}
              label="Live report"
            />
          ) : (
            "The first verified findings will appear here."
          )}
        </div>
        <div className="border-t border-hairline bg-subtle/45 px-5 py-4">
          <p className="font-mono text-xs text-ink-secondary">
            {sources.length} sources · {evidence.length} evidence records ·{" "}
            {gaps.length} open gaps
          </p>
        </div>
      </div>
      {comparison ? (
        <div className="min-w-0">
          <h2 className="mb-4 font-serif text-2xl text-ink">
            Comparison artifact
          </h2>
          <ComparisonMatrixView comparison={comparison} />
        </div>
      ) : null}
    </section>
  );
}
