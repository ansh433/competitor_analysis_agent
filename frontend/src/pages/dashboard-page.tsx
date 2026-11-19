import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ArrowRight, Plus } from "lucide-react";

import { apiRequest } from "../api/client";
import type { WorkspaceSummary } from "../research/types";

export function DashboardPage(): React.JSX.Element {
  const workspaces = useQuery({
    queryKey: ["workspaces"],
    queryFn: () =>
      apiRequest<{ workspaces: WorkspaceSummary[]; total: number }>(
        "/workspaces",
      ),
  });
  return (
    <section className="mx-auto max-w-5xl">
      <header className="hidden lg:block">
        <h1 className="page-title">Dashboard</h1>
      </header>

      <div className="mt-8 grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_18rem] lg:gap-10">
        <div className="min-w-0">
          <Link
            to="/research"
            className="pressable group block rounded-[var(--radius-card-lg)] bg-pine p-6 text-white shadow-quiet-lg sm:p-8"
          >
            <h2 className="max-w-sm font-serif text-3xl font-medium leading-tight">
              Start a company brief
            </h2>
            <p className="mt-3 max-w-sm text-sm leading-6 text-white/80">
              Investigate a company, its competitors, and the evidence behind
              your next decision.
            </p>
            <span className="mt-8 inline-flex min-h-11 items-center gap-3 rounded-[var(--radius-control)] bg-canvas px-4 py-2 text-sm font-semibold text-pine">
              Begin research
              <ArrowRight
                className="group-hover:translate-x-0.5"
                aria-hidden="true"
                size={16}
              />
            </span>
          </Link>

          <div className="mt-10 flex flex-wrap items-center justify-between gap-3 border-b border-hairline pb-3">
            <h2 className="section-title">Recent workspaces</h2>
            <Link to="/workspaces" className="text-link text-sm">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {workspaces.isLoading ? (
              <p className="py-6 text-sm text-ink-secondary">
                Loading workspaces…
              </p>
            ) : null}
            {workspaces.data?.workspaces.slice(0, 4).map((workspace) => (
              <Link
                key={workspace.id}
                to="/workspaces/$workspaceId"
                params={{ workspaceId: workspace.id }}
                className="group flex min-h-20 items-center justify-between gap-5 rounded-xl border border-hairline bg-surface px-4 py-4 shadow-quiet hover:bg-subtle/40 sm:px-5"
              >
                <span className="min-w-0">
                  <strong className="block break-words font-serif text-xl font-medium">
                    {workspace.name}
                  </strong>
                  {workspace.description ? (
                    <span className="mt-1 line-clamp-2 break-words text-sm leading-6 text-ink-secondary">
                      {workspace.description}
                    </span>
                  ) : null}
                </span>
                <ArrowRight
                  className="shrink-0 text-ink-secondary group-hover:translate-x-0.5 group-hover:text-teal"
                  aria-hidden="true"
                  size={16}
                />
              </Link>
            ))}
            {workspaces.data?.total === 0 ? (
              <div className="rounded-xl border border-dashed border-hairline bg-surface/60 px-5 py-6">
                <p className="text-sm text-ink-secondary">No workspaces yet.</p>
                <Link
                  to="/workspaces"
                  className="text-link mt-2 inline-block text-sm"
                >
                  Create a workspace
                </Link>
              </div>
            ) : null}
          </div>
        </div>

        <aside className="min-w-0 space-y-6" aria-label="Dashboard shortcuts">
          <Link
            to="/workspaces"
            className="text-link inline-flex min-h-11 items-center gap-2 text-sm font-medium"
          >
            <Plus aria-hidden="true" size={16} /> New workspace
          </Link>
        </aside>
      </div>
    </section>
  );
}
