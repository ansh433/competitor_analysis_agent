import { useMutation } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";

import { apiRequest } from "../api/client";
import { type AuthenticatedUser, useAuth } from "../auth/auth-context";

export function SettingsPage(): React.JSX.Element {
  const { currentUser, refreshUser } = useAuth();
  const [message, setMessage] = useState<string | null>(null);
  const updateProfile = useMutation({
    mutationFn: (body: { full_name: string; email: string }) =>
      apiRequest<AuthenticatedUser>("/users/me", {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: async () => {
      await refreshUser();
      setMessage("Profile updated");
    },
  });
  const changePassword = useMutation({
    mutationFn: (body: { current_password: string; new_password: string }) =>
      apiRequest("/users/me/password", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => setMessage("Password updated"),
  });

  function handleProfile(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    updateProfile.mutate({
      full_name: String(data.get("fullName") ?? ""),
      email: String(data.get("email") ?? ""),
    });
  }
  function handlePassword(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    changePassword.mutate(
      {
        current_password: String(data.get("currentPassword") ?? ""),
        new_password: String(data.get("newPassword") ?? ""),
      },
      { onSuccess: () => form.reset() },
    );
  }

  return (
    <section className="max-w-5xl">
      <p className="mb-3 text-sm font-semibold text-[var(--teal)]">
        Account controls
      </p>
      <h1 className="font-display text-5xl text-[var(--navy)]">Settings</h1>
      {message ? (
        <output className="mt-5 block bg-emerald-50 p-4 text-emerald-900">
          {message}
        </output>
      ) : null}
      <div className="mt-10 grid gap-8 md:grid-cols-2">
        <form
          onSubmit={handleProfile}
          className="border border-[var(--line)] bg-white p-6"
        >
          <h2 className="font-display text-2xl">Profile</h2>
          <label className="mt-5 block text-sm font-medium">
            Full name
            <input
              name="fullName"
              required
              defaultValue={currentUser?.full_name ?? ""}
              className="form-input"
            />
          </label>
          <label className="mt-4 block text-sm font-medium">
            Email
            <input
              name="email"
              type="email"
              required
              defaultValue={currentUser?.email ?? ""}
              className="form-input"
            />
          </label>
          <button
            type="submit"
            disabled={updateProfile.isPending}
            className="mt-5 min-h-11 bg-[var(--navy)] px-5 font-semibold text-white disabled:opacity-50"
          >
            Save profile
          </button>
        </form>
        <form
          onSubmit={handlePassword}
          className="border border-[var(--line)] bg-white p-6"
        >
          <h2 className="font-display text-2xl">Password</h2>
          <label className="mt-5 block text-sm font-medium">
            Current password
            <input
              name="currentPassword"
              type="password"
              required
              className="form-input"
              autoComplete="current-password"
            />
          </label>
          <label className="mt-4 block text-sm font-medium">
            New password
            <input
              name="newPassword"
              type="password"
              required
              minLength={12}
              className="form-input"
              autoComplete="new-password"
            />
          </label>
          <button
            type="submit"
            disabled={changePassword.isPending}
            className="mt-5 min-h-11 bg-[var(--navy)] px-5 font-semibold text-white disabled:opacity-50"
          >
            Change password
          </button>
        </form>
      </div>
    </section>
  );
}
