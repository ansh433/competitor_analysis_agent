import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import type { FormEvent } from "react";

import { apiRequest } from "../api/client";
import type { WorkspaceSummary } from "../research/types";

export function WorkspacesPage(): React.JSX.Element {
  const queryClient = useQueryClient();
  const workspaces = useQuery({
    queryKey: ["workspaces"],
    queryFn: () =>
      apiRequest<{ workspaces: WorkspaceSummary[]; total: number }>(
        "/workspaces",
      ),
  });
  const createWorkspace = useMutation({
    mutationFn: (input: { name: string; description: string }) =>
      apiRequest<WorkspaceSummary>("/workspaces", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["workspaces"] }),
  });

  function handleCreate(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    createWorkspace.mutate(
      {
        name: String(data.get("name") ?? ""),
        description: String(data.get("description") ?? ""),
      },
      { onSuccess: () => form.reset() },
    );
  }

  return (
    <section className="mx-auto max-w-5xl">
      <header>
        <h1 className="page-title">Workspaces</h1>
        <p className="mt-3 max-w-xl text-sm leading-6 text-ink-secondary">
          Organize companies and research by project or market.
        </p>
      </header>

      <div className="mt-8 grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_18rem] lg:gap-10">
        <div className="min-w-0 space-y-3">
          {workspaces.isLoading ? (
            <p className="py-6 text-sm text-ink-secondary">
              Loading workspaces…
            </p>
          ) : null}
          {workspaces.data?.workspaces.map((workspace) => (
            <Link
              key={workspace.id}
              to="/workspaces/$workspaceId"
              params={{ workspaceId: workspace.id }}
              className="group flex min-h-24 items-center justify-between gap-6 rounded-xl border border-hairline bg-surface px-4 py-5 shadow-quiet hover:bg-subtle/40 sm:px-5"
            >
              <div className="min-w-0">
                <h2 className="break-words font-serif text-2xl font-semibold text-ink">
                  {workspace.name}
                </h2>
                {workspace.description ? (
                  <p className="mt-1 line-clamp-2 break-words text-sm leading-6 text-ink-secondary">
                    {workspace.description}
                  </p>
                ) : null}
              </div>
              <ArrowRight
                className="shrink-0 text-ink-secondary group-hover:translate-x-0.5 group-hover:text-teal"
                aria-hidden="true"
                size={18}
              />
            </Link>
          ))}
          {workspaces.data?.total === 0 ? (
            <div className="rounded-xl border border-dashed border-hairline bg-surface/60 px-5 py-8">
              <p className="text-sm leading-6 text-ink-secondary">
                Create a workspace to add companies and start research.
              </p>
            </div>
          ) : null}
        </div>
        <form
          onSubmit={handleCreate}
          aria-labelledby="new-workspace-title"
          className="surface-card min-w-0 rounded-[var(--radius-card-lg)] p-5 sm:p-6"
        >
          <h2 id="new-workspace-title" className="section-title">
            New workspace
          </h2>
          <label className="mt-6 block text-sm font-medium">
            Name
            <input name="name" required className="form-input" />
          </label>
          <label className="mt-4 block text-sm font-medium">
            Description
            <textarea
              name="description"
              className="form-input min-h-24 resize-y"
            />
          </label>
          {createWorkspace.error ? (
            <p role="alert" className="mt-3 text-sm text-red-800">
              {createWorkspace.error.message}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={createWorkspace.isPending}
            className="button-primary mt-6 w-full"
          >
            Create workspace
          </button>
        </form>
      </div>
    </section>
  );
}
