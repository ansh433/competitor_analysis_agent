import { useQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";

import { apiRequest } from "../api/client";
import { ComparisonMatrixView } from "../components/comparison-matrix";
import type { ComparisonArtifactData } from "../research/artifact-types";

export function ComparisonPage(): React.JSX.Element {
  const { comparisonId } = useParams({ strict: false }) as {
    comparisonId: string;
  };
  const comparison = useQuery({
    queryKey: ["comparison", comparisonId],
    queryFn: () =>
      apiRequest<ComparisonArtifactData>(`/comparisons/${comparisonId}`),
  });
  return (
    <section className="mx-auto min-w-0 max-w-7xl">
      <header className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-3">
        <h1 className="page-title">Company comparison</h1>
        {comparison.data ? (
          <p className="text-sm text-ink-secondary">
            Generated{" "}
            <time dateTime={comparison.data.generated_at}>
              {new Date(comparison.data.generated_at).toLocaleString()}
            </time>
          </p>
        ) : null}
      </header>
      <div className="mt-8 min-w-0">
        {comparison.data ? (
          <ComparisonMatrixView
            comparison={comparison.data.structured_result}
          />
        ) : comparison.isError ? (
          <div role="alert" className="border-y border-hairline py-8">
            <p className="text-sm text-ink-secondary">
              This comparison could not be loaded.
            </p>
            <button
              type="button"
              onClick={() => void comparison.refetch()}
              disabled={comparison.isFetching}
              className="button-secondary mt-4"
            >
              {comparison.isFetching ? "Retrying…" : "Try again"}
            </button>
          </div>
        ) : (
          <output className="text-sm text-ink-secondary">
            Loading comparison…
          </output>
        )}
      </div>
    </section>
  );
}
