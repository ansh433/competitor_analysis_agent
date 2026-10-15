import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";

import { apiRequest } from "../api/client";
import type { TrackedCompanySummary } from "../research/types";

export function TrackedCompaniesPage(): React.JSX.Element {
  const tracked = useQuery({ queryKey: ["tracked-companies"], queryFn: () => apiRequest<{ tracked_companies: TrackedCompanySummary[] }>("/tracked-companies") });
  return (
    <section className="max-w-5xl">
      <p className="mb-3 text-sm font-semibold text-[var(--teal)]">Monitoring queue</p>
      <h1 className="font-display text-5xl text-[var(--navy)]">Tracked companies</h1>
      <div className="mt-10 divide-y divide-[var(--line)] border-y border-[var(--line)]">
        {tracked.data?.tracked_companies.map((item) => (
          <Link key={item.id} to="/companies/$companyId" params={{ companyId: item.company_id }} className="flex min-h-20 items-center justify-between py-4"><span className="font-medium">Company {item.company_id.slice(0, 8)}</span><span className="text-sm text-[var(--teal)]">Open dossier</span></Link>
        ))}
        {tracked.data?.tracked_companies.length === 0 ? <p className="py-10 text-[var(--muted)]">No companies are tracked yet.</p> : null}
      </div>
    </section>
  );
}

