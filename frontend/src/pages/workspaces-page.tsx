import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ArrowUpRight, FolderPlus } from "lucide-react";
import { FormEvent } from "react";

import { apiRequest } from "../api/client";
import type { WorkspaceSummary } from "../research/types";

export function WorkspacesPage(): React.JSX.Element {
  const queryClient = useQueryClient();
  const workspaces = useQuery({
    queryKey: ["workspaces"],
    queryFn: () => apiRequest<{ workspaces: WorkspaceSummary[]; total: number }>("/workspaces"),
  });
  const createWorkspace = useMutation({
    mutationFn: (input: { name: string; description: string }) =>
      apiRequest<WorkspaceSummary>("/workspaces", { method: "POST", body: JSON.stringify(input) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workspaces"] }),
  });

  function handleCreate(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    createWorkspace.mutate(
      { name: String(data.get("name") ?? ""), description: String(data.get("description") ?? "") },
      { onSuccess: () => form.reset() },
    );
  }

  return (
    <section className="max-w-6xl">
      <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
        <div>
          <p className="mb-3 text-sm font-semibold text-[var(--teal)]">Research library</p>
          <h1 className="font-display text-4xl text-[var(--navy)] md:text-5xl">Workspaces</h1>
          <p className="mt-4 max-w-2xl text-lg text-[var(--muted)]">Keep each market thesis, company set, and evidence trail in a distinct mandate.</p>
        </div>
        <span className="text-sm text-[var(--muted)]">{workspaces.data?.total ?? 0} workspaces</span>
      </div>

      <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_22rem]">
        <div className="divide-y divide-[var(--line)] border-y border-[var(--line)]">
          {workspaces.isLoading ? <p className="py-6 text-[var(--muted)]">Loading workspaces…</p> : null}
          {workspaces.data?.workspaces.map((workspace) => (
            <Link
              key={workspace.id}
              to="/workspaces/$workspaceId"
              params={{ workspaceId: workspace.id }}
              className="group flex min-h-28 items-center justify-between gap-6 py-5 hover:bg-white/55"
            >
              <div>
                <h2 className="font-display text-2xl text-[var(--navy)]">{workspace.name}</h2>
                <p className="mt-2 line-clamp-2 text-sm text-[var(--muted)]">{workspace.description || "No description yet"}</p>
              </div>
              <ArrowUpRight className="shrink-0 transition-transform group-hover:-translate-y-1 group-hover:translate-x-1" aria-hidden="true" />
            </Link>
          ))}
          {workspaces.data?.total === 0 ? <p className="py-10 text-[var(--muted)]">Create the first workspace for your current strategic question.</p> : null}
        </div>
        <form onSubmit={handleCreate} className="h-fit border border-[var(--line)] bg-white p-6">
          <FolderPlus aria-hidden="true" className="text-[var(--teal)]" />
          <h2 className="mt-4 font-display text-2xl">New workspace</h2>
          <label className="mt-5 block text-sm font-medium">Name<input name="name" required className="form-input" /></label>
          <label className="mt-4 block text-sm font-medium">Description<textarea name="description" className="form-input min-h-24" /></label>
          {createWorkspace.error ? <p role="alert" className="mt-3 text-sm text-red-800">{createWorkspace.error.message}</p> : null}
          <button type="submit" disabled={createWorkspace.isPending} className="mt-5 min-h-11 w-full bg-[var(--navy)] px-4 font-semibold text-white disabled:opacity-50">Create workspace</button>
        </form>
      </div>
    </section>
  );
}

