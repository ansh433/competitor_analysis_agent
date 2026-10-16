import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { ArrowUpRight, Building2 } from "lucide-react";
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
    <section className="max-w-6xl">
      <Link to="/workspaces" className="text-sm text-[var(--teal)] underline">
        All workspaces
      </Link>
      <h1 className="mt-4 font-display text-4xl text-[var(--navy)] md:text-5xl">
        {workspace.data?.name ?? "Workspace"}
      </h1>
      <p className="mt-4 max-w-2xl text-lg text-[var(--muted)]">
        {workspace.data?.description}
      </p>
      <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_22rem]">
        <div>
          <div className="flex items-center justify-between border-b border-[var(--line)] pb-3">
            <h2 className="font-display text-2xl">Companies</h2>
            <span className="text-sm text-[var(--muted)]">
              {companies.data?.total ?? 0}
            </span>
          </div>
          <div className="divide-y divide-[var(--line)]">
            {companies.data?.companies.map((company) => (
              <Link
                key={company.id}
                to="/companies/$companyId"
                params={{ companyId: company.id }}
                className="group flex min-h-24 items-center justify-between gap-5 py-4"
              >
                <div>
                  <h3 className="font-display text-xl">
                    {company.display_name}
                  </h3>
                  <p className="mt-1 text-sm text-[var(--muted)]">
                    {company.domain ?? "Domain unresolved"} ·{" "}
                    {company.research_status.replaceAll("_", " ")}
                  </p>
                </div>
                <ArrowUpRight
                  aria-hidden="true"
                  className="group-hover:text-[var(--teal)]"
                />
              </Link>
            ))}
          </div>
        </div>
        <form
          onSubmit={handleCreateCompany}
          className="h-fit border border-[var(--line)] bg-white p-6"
        >
          <Building2 className="text-[var(--teal)]" aria-hidden="true" />
          <h2 className="mt-4 font-display text-2xl">Add a company</h2>
          <label className="mt-5 block text-sm font-medium">
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
          <button
            type="submit"
            disabled={createCompany.isPending}
            className="mt-5 min-h-11 w-full bg-[var(--navy)] px-4 font-semibold text-white disabled:opacity-50"
          >
            Add company
          </button>
        </form>
      </div>
    </section>
  );
}
