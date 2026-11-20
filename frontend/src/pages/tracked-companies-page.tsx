import { useQueries, useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";

import { apiRequest } from "../api/client";
import type { CompanySummary, TrackedCompanySummary } from "../research/types";

export function TrackedCompaniesPage(): React.JSX.Element {
  const tracked = useQuery({
    queryKey: ["tracked-companies"],
    queryFn: () =>
      apiRequest<{ tracked_companies: TrackedCompanySummary[] }>(
        "/tracked-companies",
      ),
  });
  const records = tracked.data?.tracked_companies ?? [];
  const companies = useQueries({
    queries: records.map((item) => ({
      queryKey: ["company", item.company_id],
      queryFn: () =>
        apiRequest<CompanySummary>(`/companies/${item.company_id}`),
      staleTime: 60_000,
    })),
  });

  return (
    <section className="mx-auto min-w-0 max-w-5xl">
      <h1 className="page-title">Tracked companies</h1>

      <div className="mt-8 space-y-3">
        {records.map((item, index) => {
          const companyQuery = companies[index];
          const company = companyQuery?.data;
          const title =
            company?.display_name ||
            company?.legal_name ||
            (companyQuery?.isError
              ? "Company unavailable"
              : "Loading company…");
          const detail = company?.domain || company?.industry;
          return (
            <Link
              key={item.id}
              to="/companies/$companyId"
              params={{ companyId: item.company_id }}
              className="flex min-h-24 flex-col items-start justify-between gap-3 rounded-xl border border-hairline bg-surface px-4 py-5 shadow-quiet hover:bg-subtle/40 sm:flex-row sm:items-center sm:gap-5 sm:px-5"
            >
              <span className="min-w-0">
                <strong className="block font-serif text-xl font-medium [overflow-wrap:anywhere]">
                  {title}
                </strong>
                {detail ? (
                  <span className="mt-1 block text-sm text-ink-secondary [overflow-wrap:anywhere]">
                    {detail}
                  </span>
                ) : !company ? (
                  <span className="mt-1 block font-mono text-xs text-ink-muted">
                    Reference {item.company_id.slice(0, 8)}
                  </span>
                ) : null}
              </span>
              <span className="flex shrink-0 items-center gap-2 text-sm text-teal">
                Open dossier
                <ArrowUpRight aria-hidden="true" size={15} />
              </span>
            </Link>
          );
        })}
        {tracked.isLoading ? (
          <output className="block py-8 text-sm text-ink-secondary">
            Loading tracked companies…
          </output>
        ) : null}
        {tracked.isError ? (
          <div role="alert" className="py-8 text-sm text-ink-secondary">
            <p>Tracked companies could not be loaded.</p>
            <button
              type="button"
              onClick={() => void tracked.refetch()}
              disabled={tracked.isFetching}
              className="button-secondary mt-4"
            >
              {tracked.isFetching ? "Retrying…" : "Try again"}
            </button>
          </div>
        ) : null}
        {records.length === 0 && !tracked.isLoading && !tracked.isError ? (
          <div className="rounded-xl border border-dashed border-hairline bg-surface/60 px-5 py-8">
            <p className="text-sm text-ink-secondary">
              No companies are tracked yet.
            </p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
