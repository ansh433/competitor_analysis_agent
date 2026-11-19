import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";

import { apiRequest } from "../api/client";

interface ManagedUser {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export function AdminPage(): React.JSX.Element {
  const queryClient = useQueryClient();
  const users = useQuery({
    queryKey: ["admin-users"],
    queryFn: () =>
      apiRequest<{ users: ManagedUser[]; total: number }>("/users"),
  });
  const createUser = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      apiRequest<ManagedUser>("/users", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
  const updateUser = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      apiRequest<ManagedUser>(`/users/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active }),
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  function handleCreate(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    createUser.mutate(
      {
        email: String(data.get("email") ?? ""),
        full_name: String(data.get("fullName") ?? ""),
        password: String(data.get("password") ?? ""),
        is_superuser: data.get("isSuperuser") === "on",
      },
      { onSuccess: () => form.reset() },
    );
  }

  return (
    <section className="mx-auto min-w-0 max-w-5xl">
      <h1 className="page-title">Users</h1>
      {updateUser.isError ? (
        <p role="alert" className="mt-5 text-sm text-red-800">
          User status could not be updated. Please try again.
        </p>
      ) : null}
      <div className="mt-8 grid items-start gap-8 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <section
          aria-label="User accounts"
          className="min-w-0 overflow-x-auto rounded-xl border border-hairline bg-surface shadow-quiet"
        >
          <table className="w-full min-w-[36rem] text-left text-sm">
            <caption className="sr-only">
              User accounts, roles, and access
            </caption>
            <thead className="border-b border-hairline bg-subtle/60 text-ink-secondary">
              <tr>
                <th scope="col" className="p-4 font-medium">
                  User
                </th>
                <th scope="col" className="p-4 font-medium">
                  Role
                </th>
                <th scope="col" className="p-4 font-medium">
                  Status
                </th>
                <th scope="col" className="p-4 font-medium">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {users.data?.users.map((user) => (
                <tr key={user.id}>
                  <td className="p-4">
                    <strong className="block font-medium">
                      {user.full_name || user.email}
                    </strong>
                    {user.full_name ? (
                      <span className="text-ink-secondary">{user.email}</span>
                    ) : null}
                  </td>
                  <td className="p-4">
                    {user.is_superuser ? "Administrator" : "Analyst"}
                  </td>
                  <td className="p-4">
                    {user.is_active ? "Active" : "Disabled"}
                  </td>
                  <td className="p-4">
                    <button
                      type="button"
                      className="text-link inline-flex min-h-11 items-center"
                      aria-label={`${user.is_active ? "Disable" : "Enable"} ${user.full_name || user.email}`}
                      disabled={updateUser.isPending}
                      onClick={() =>
                        updateUser.mutate({
                          id: user.id,
                          is_active: !user.is_active,
                        })
                      }
                    >
                      {user.is_active ? "Disable" : "Enable"}
                    </button>
                  </td>
                </tr>
              ))}
              {users.isLoading ? (
                <tr>
                  <td colSpan={4} className="p-6 text-ink-secondary">
                    <output>Loading users…</output>
                  </td>
                </tr>
              ) : null}
              {users.isError ? (
                <tr>
                  <td colSpan={4} className="p-6">
                    <p role="alert" className="text-ink-secondary">
                      User accounts could not be loaded.
                    </p>
                    <button
                      type="button"
                      onClick={() => void users.refetch()}
                      disabled={users.isFetching}
                      className="button-secondary mt-4"
                    >
                      {users.isFetching ? "Retrying…" : "Try again"}
                    </button>
                  </td>
                </tr>
              ) : null}
              {users.data?.users.length === 0 && !users.isError ? (
                <tr>
                  <td colSpan={4} className="p-6 text-ink-secondary">
                    No user accounts found.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </section>
        <form
          onSubmit={handleCreate}
          aria-busy={createUser.isPending}
          className="surface-card h-fit p-5 sm:p-6"
        >
          <h2 className="font-serif text-xl">Add user</h2>
          <label className="mt-4 block text-sm font-medium">
            Full name
            <input
              name="fullName"
              required
              className="form-input"
              autoComplete="off"
            />
          </label>
          <label className="mt-4 block text-sm font-medium">
            Email
            <input
              name="email"
              type="email"
              required
              className="form-input"
              autoComplete="off"
              autoCapitalize="none"
              spellCheck={false}
            />
          </label>
          <label className="mt-4 block text-sm font-medium">
            Temporary password
            <input
              name="password"
              type="password"
              minLength={12}
              required
              className="form-input"
              autoComplete="new-password"
              aria-describedby="temporary-password-guidance"
            />
          </label>
          <p
            id="temporary-password-guidance"
            className="mt-2 text-sm text-ink-secondary"
          >
            Use at least 12 characters.
          </p>
          <label className="mt-4 flex min-h-11 items-center gap-3 text-sm">
            <input name="isSuperuser" type="checkbox" /> Administrator
          </label>
          {createUser.isError ? (
            <p role="alert" className="mt-4 text-sm text-red-800">
              {createUser.error.message}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={createUser.isPending}
            className="button-primary mt-4 w-full"
          >
            {createUser.isPending ? "Creating…" : "Create user"}
          </button>
        </form>
      </div>
    </section>
  );
}
