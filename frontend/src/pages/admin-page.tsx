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
    <section className="max-w-6xl">
      <p className="mb-3 text-sm font-semibold text-[var(--teal)]">
        Access administration
      </p>
      <h1 className="font-display text-5xl text-[var(--navy)]">Users</h1>
      <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_22rem]">
        <div className="overflow-x-auto border border-[var(--line)] bg-white">
          <table className="w-full min-w-[42rem] text-left text-sm">
            <thead className="bg-[var(--navy)] text-white">
              <tr>
                <th className="p-4">User</th>
                <th className="p-4">Role</th>
                <th className="p-4">Status</th>
                <th className="p-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--line)]">
              {users.data?.users.map((user) => (
                <tr key={user.id}>
                  <td className="p-4">
                    <strong className="block">
                      {user.full_name ?? "Unnamed"}
                    </strong>
                    <span className="text-[var(--muted)]">{user.email}</span>
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
                      className="text-[var(--teal)] underline"
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
            </tbody>
          </table>
        </div>
        <form
          onSubmit={handleCreate}
          className="h-fit border border-[var(--line)] bg-white p-6"
        >
          <h2 className="font-display text-2xl">Add user</h2>
          <label className="mt-4 block text-sm font-medium">
            Full name
            <input name="fullName" required className="form-input" />
          </label>
          <label className="mt-4 block text-sm font-medium">
            Email
            <input name="email" type="email" required className="form-input" />
          </label>
          <label className="mt-4 block text-sm font-medium">
            Temporary password
            <input
              name="password"
              type="password"
              minLength={12}
              required
              className="form-input"
            />
          </label>
          <label className="mt-4 flex min-h-11 items-center gap-3 text-sm">
            <input name="isSuperuser" type="checkbox" /> Administrator
          </label>
          <button
            type="submit"
            disabled={createUser.isPending}
            className="mt-4 min-h-11 w-full bg-[var(--navy)] px-4 font-semibold text-white disabled:opacity-50"
          >
            Create user
          </button>
        </form>
      </div>
    </section>
  );
}
