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
    <section className="max-w-7xl">
      <p className="mb-3 text-sm font-semibold text-[var(--teal)]">
        Normalized evidence view
      </p>
      <h1 className="font-display text-5xl text-[var(--navy)]">
        Company comparison
      </h1>
      <p className="mt-4 text-[var(--muted)]">
        Generated{" "}
        {comparison.data
          ? new Date(comparison.data.generated_at).toLocaleString()
          : "—"}
      </p>
      <div className="mt-8">
        {comparison.data ? (
          <ComparisonMatrixView
            comparison={comparison.data.structured_result}
          />
        ) : (
          <p>Loading comparison…</p>
        )}
      </div>
    </section>
  );
}
