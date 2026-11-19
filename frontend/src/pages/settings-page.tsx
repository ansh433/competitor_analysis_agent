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
    setMessage(null);
    const data = new FormData(event.currentTarget);
    updateProfile.mutate({
      full_name: String(data.get("fullName") ?? ""),
      email: String(data.get("email") ?? ""),
    });
  }
  function handlePassword(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    setMessage(null);
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
    <section className="mx-auto min-w-0 max-w-4xl">
      <h1 className="page-title">Settings</h1>
      {message ? (
        <output className="mt-5 block bg-emerald-50 p-4 text-emerald-900">
          {message}
        </output>
      ) : null}
      <div className="mt-8 divide-y divide-hairline border-y border-hairline">
        <form
          onSubmit={handleProfile}
          aria-busy={updateProfile.isPending}
          className="grid gap-5 py-7 md:grid-cols-[12rem_minmax(0,1fr)]"
        >
          <h2 className="font-serif text-xl">Profile</h2>
          <div className="min-w-0 max-w-md">
            <label className="block text-sm font-medium">
              Full name
              <input
                name="fullName"
                required
                defaultValue={currentUser?.full_name ?? ""}
                className="form-input"
                autoComplete="name"
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
                autoComplete="email"
                autoCapitalize="none"
                spellCheck={false}
              />
            </label>
            {updateProfile.isError ? (
              <p role="alert" className="mt-4 text-sm text-red-800">
                {updateProfile.error.message}
              </p>
            ) : null}
            <button
              type="submit"
              disabled={updateProfile.isPending}
              className="button-primary mt-5"
            >
              {updateProfile.isPending ? "Saving…" : "Save profile"}
            </button>
          </div>
        </form>
        <form
          onSubmit={handlePassword}
          aria-busy={changePassword.isPending}
          className="grid gap-5 py-7 md:grid-cols-[12rem_minmax(0,1fr)]"
        >
          <h2 className="font-serif text-xl">Password</h2>
          <div className="min-w-0 max-w-md">
            <label className="block text-sm font-medium">
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
                aria-describedby="new-password-guidance"
              />
            </label>
            <p
              id="new-password-guidance"
              className="mt-2 text-sm text-ink-secondary"
            >
              Use at least 12 characters.
            </p>
            {changePassword.isError ? (
              <p role="alert" className="mt-4 text-sm text-red-800">
                {changePassword.error.message}
              </p>
            ) : null}
            <button
              type="submit"
              disabled={changePassword.isPending}
              className="button-primary mt-5"
            >
              {changePassword.isPending ? "Updating…" : "Change password"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
