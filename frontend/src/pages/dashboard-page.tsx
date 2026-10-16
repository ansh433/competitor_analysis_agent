import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ArrowRight, Building2, Gauge, Telescope } from "lucide-react";

import { apiRequest } from "../api/client";
import { useQuotaStatus } from "../quotas/use-quota";
import type { WorkspaceSummary } from "../research/types";

export function DashboardPage(): React.JSX.Element {
  const quota = useQuotaStatus();
  const workspaces = useQuery({
    queryKey: ["workspaces"],
    queryFn: () =>
      apiRequest<{ workspaces: WorkspaceSummary[]; total: number }>(
        "/workspaces",
      ),
  });
  const standard = quota.data?.tiers.find((item) => item.tier === "standard");
  return (
    <section className="max-w-6xl">
      <p className="mb-3 text-sm font-semibold text-[var(--teal)]">
        Decision desk
      </p>
      <h1 className="max-w-4xl font-display text-5xl leading-tight text-[var(--navy)] md:text-6xl">
        Research that shows its work.
      </h1>
      <div className="mt-10 grid gap-px border border-[var(--line)] bg-[var(--line)] md:grid-cols-[1.4fr_1fr]">
        <Link
          to="/research"
          className="group bg-[var(--navy)] p-7 text-white md:p-9"
        >
          <Telescope className="text-[var(--signal)]" aria-hidden="true" />
          <h2 className="mt-8 font-display text-3xl">Start a company brief</h2>
          <p className="mt-3 max-w-lg leading-7 text-teal-50/75">
            Resolve an identity, discover competitors, and preserve every
            accepted source.
          </p>
          <span className="mt-8 inline-flex items-center gap-2 font-semibold">
            Begin research{" "}
            <ArrowRight
              className="transition-transform group-hover:translate-x-1"
              aria-hidden="true"
              size={18}
            />
          </span>
        </Link>
        <div className="bg-white p-7 md:p-9">
          <Gauge className="text-[var(--teal)]" aria-hidden="true" />
          <h2 className="mt-8 font-display text-2xl">Daily capacity</h2>
          <p className="mt-3 font-display text-5xl text-[var(--navy)]">
            {standard?.bypassed ? "∞" : (standard?.remaining ?? "—")}
          </p>
          <p className="mt-2 text-sm text-[var(--muted)]">
            standard runs remaining
          </p>
        </div>
      </div>
      <div className="mt-10 flex items-center justify-between border-b border-[var(--line)] pb-3">
        <h2 className="font-display text-2xl">Recent workspaces</h2>
        <Link to="/workspaces" className="text-sm text-[var(--teal)] underline">
          View all
        </Link>
      </div>
      <div className="divide-y divide-[var(--line)]">
        {workspaces.data?.workspaces.slice(0, 4).map((workspace) => (
          <Link
            key={workspace.id}
            to="/workspaces/$workspaceId"
            params={{ workspaceId: workspace.id }}
            className="flex min-h-20 items-center justify-between py-4"
          >
            <span className="flex items-center gap-3">
              <Building2 aria-hidden="true" size={18} />
              <strong>{workspace.name}</strong>
            </span>
            <ArrowRight aria-hidden="true" size={17} />
          </Link>
        ))}
      </div>
    </section>
  );
}
