import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import type { FormEvent } from "react";

import { apiRequest } from "../api/client";
import type { CompanySummary, WorkspaceSummary } from "../research/types";

export function WorkspaceDetailPage(): React.JSX.Element {
  const { workspaceId } = useParams({ strict: false }) as {
    workspaceId: string;
  };
  const queryClient = useQueryClient();
  const workspace = useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () => apiRequest<WorkspaceSummary>(`/workspaces/${workspaceId}`),
  });
  const companies = useQuery({
    queryKey: ["companies", workspaceId],
    queryFn: () =>
      apiRequest<{ companies: CompanySummary[]; total: number }>(
        `/workspaces/${workspaceId}/companies`,
      ),
  });
  const createCompany = useMutation({
    mutationFn: (input: { display_name: string; website?: string }) =>
      apiRequest<CompanySummary>(`/workspaces/${workspaceId}/companies`, {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["companies", workspaceId] }),
  });

  function handleCreateCompany(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const website = String(data.get("website") ?? "").trim();
    createCompany.mutate(
      {
        display_name: String(data.get("name") ?? ""),
        ...(website ? { website } : {}),
      },
      { onSuccess: () => form.reset() },
    );
  }

  return (
    <section className="mx-auto max-w-5xl">
      <Link to="/workspaces" className="text-link text-sm">
        All workspaces
      </Link>
      <h1 className="page-title mt-5 break-words">
        {workspace.data?.name ?? "Workspace"}
      </h1>
      {workspace.data?.description ? (
        <p className="mt-3 max-w-2xl break-words text-sm leading-6 text-ink-secondary">
          {workspace.data.description}
        </p>
      ) : null}
      <div className="mt-8 grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_18rem] lg:gap-10">
        <div className="min-w-0">
          <div className="flex items-center justify-between border-b border-hairline pb-3">
            <h2 className="section-title">Companies</h2>
            <span className="text-sm tabular-nums text-ink-secondary">
              {companies.isLoading ? "—" : (companies.data?.total ?? 0)}
            </span>
          </div>
          <div className="space-y-3">
            {companies.isLoading ? (
              <p className="py-6 text-sm text-ink-secondary">
                Loading companies…
              </p>
            ) : null}
            {companies.data?.companies.map((company) => (
              <Link
                key={company.id}
                to="/companies/$companyId"
                params={{ companyId: company.id }}
                className="group flex min-h-24 items-center justify-between gap-5 rounded-xl border border-hairline bg-surface px-4 py-4 shadow-quiet hover:bg-subtle/40 sm:px-5"
              >
                <div className="min-w-0">
                  <h3 className="break-words font-serif text-xl">
                    {company.display_name}
                  </h3>
                  <p className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm leading-6 text-ink-secondary">
                    <span className="break-all">
                      {company.domain ?? "Domain unresolved"}
                    </span>
                    <span>{company.research_status.replaceAll("_", " ")}</span>
                  </p>
                </div>
                <ArrowRight
                  aria-hidden="true"
                  className="shrink-0 text-ink-secondary group-hover:translate-x-0.5 group-hover:text-teal"
                  size={18}
                />
              </Link>
            ))}
            {companies.data?.total === 0 ? (
              <div className="rounded-xl border border-dashed border-hairline bg-surface/60 px-5 py-8">
                <p className="text-sm leading-6 text-ink-secondary">
                  No companies yet. Add a company to this workspace to get
                  started.
                </p>
              </div>
            ) : null}
          </div>
        </div>
        <form
          onSubmit={handleCreateCompany}
          aria-labelledby="add-company-title"
          className="surface-card min-w-0 rounded-[var(--radius-card-lg)] p-5 sm:p-6"
        >
          <h2 id="add-company-title" className="section-title">
            Add a company
          </h2>
          <label className="mt-6 block text-sm font-medium">
            Display name
            <input name="name" required className="form-input" />
          </label>
          <label className="mt-4 block text-sm font-medium">
            Website
            <input
              name="website"
              type="url"
              className="form-input"
              placeholder="https://example.com"
            />
          </label>
          {createCompany.error ? (
            <p role="alert" className="mt-3 text-sm text-red-800">
              {createCompany.error.message}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={createCompany.isPending}
            className="button-primary mt-6 w-full"
          >
            Add company
          </button>
        </form>
      </div>
    </section>
  );
}
