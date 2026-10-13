import { Link, useNavigate } from "@tanstack/react-router";
import { FormEvent, useState } from "react";

import { apiRequest } from "../api/client";
import { useAuth } from "../auth/auth-context";

type AuthPageMode = "login" | "signup" | "recover" | "reset";

interface AuthPageProps {
  mode: AuthPageMode;
}

const content: Record<AuthPageMode, { title: string; description: string; action: string }> = {
  login: {
    title: "Return to your research",
    description: "Continue building evidence-backed company dossiers.",
    action: "Sign in",
  },
  signup: {
    title: "Create your analyst workspace",
    description: "Turn scattered company sources into reusable intelligence.",
    action: "Create account",
  },
  recover: {
    title: "Recover access",
    description: "We will send a reset link if the account exists.",
    action: "Send reset link",
  },
  reset: {
    title: "Choose a new password",
    description: "Use at least 12 characters for your new password.",
    action: "Reset password",
  },
};

export function AuthPage({ mode }: AuthPageProps): React.JSX.Element {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsSubmitting(true);
    const data = new FormData(event.currentTarget);
    const email = String(data.get("email") ?? "");
    const password = String(data.get("password") ?? "");
    try {
      if (mode === "login") {
        await login(email, password);
        await navigate({ to: "/dashboard" });
      } else if (mode === "signup") {
        await apiRequest("/auth/register", {
          method: "POST",
          body: JSON.stringify({ email, password, full_name: String(data.get("fullName") ?? "") }),
        });
        await login(email, password);
        await navigate({ to: "/dashboard" });
      } else if (mode === "recover") {
        await apiRequest("/auth/password-recovery", {
          method: "POST",
          body: JSON.stringify({ email }),
        });
        setMessage("If the account exists, a reset link is on its way.");
      } else {
        const token = new URLSearchParams(window.location.search).get("token") ?? "";
        await apiRequest("/auth/password-reset", {
          method: "POST",
          body: JSON.stringify({ token, new_password: password }),
        });
        setMessage("Password updated. You can now sign in.");
      }
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : "Request failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  const page = content[mode];
  const showEmail = mode !== "reset";
  const showPassword = mode === "login" || mode === "signup" || mode === "reset";

  return (
    <main className="grid min-h-screen bg-[var(--paper)] lg:grid-cols-[0.85fr_1.15fr]">
      <section className="hidden bg-[var(--navy)] p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <Link to="/login" className="font-display text-2xl">Compass Intelligence</Link>
        <blockquote className="max-w-md font-display text-4xl leading-tight">
          “What do we know, how do we know it, and what remains uncertain?”
        </blockquote>
        <p className="text-sm text-teal-100/65">A research desk built around evidence provenance.</p>
      </section>
      <section className="flex items-center justify-center p-6 md:p-12">
        <div className="w-full max-w-md">
          <p className="mb-4 text-sm font-semibold text-[var(--teal)]">Secure analyst access</p>
          <h1 className="font-display text-4xl leading-tight text-[var(--navy)]">{page.title}</h1>
          <p className="mt-3 leading-7 text-[var(--muted)]">{page.description}</p>
          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            {mode === "signup" ? (
              <label className="block text-sm font-medium">
                Full name
                <input name="fullName" required className="form-input" autoComplete="name" />
              </label>
            ) : null}
            {showEmail ? (
              <label className="block text-sm font-medium">
                Email address
                <input name="email" type="email" required className="form-input" autoComplete="email" />
              </label>
            ) : null}
            {showPassword ? (
              <label className="block text-sm font-medium">
                {mode === "reset" ? "New password" : "Password"}
                <input
                  name="password"
                  type="password"
                  minLength={mode === "login" ? 1 : 12}
                  required
                  className="form-input"
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                />
              </label>
            ) : null}
            {error ? <p role="alert" className="bg-red-50 p-3 text-sm text-red-800">{error}</p> : null}
            {message ? <p role="status" className="bg-emerald-50 p-3 text-sm text-emerald-900">{message}</p> : null}
            <button
              type="submit"
              disabled={isSubmitting}
              className="min-h-12 w-full bg-[var(--navy)] px-5 font-semibold text-white hover:bg-[var(--navy-light)] disabled:opacity-60"
            >
              {isSubmitting ? "Working…" : page.action}
            </button>
          </form>
          <div className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-sm text-[var(--muted)]">
            {mode !== "login" ? <Link to="/login" className="underline">Sign in</Link> : null}
            {mode === "login" ? <Link to="/signup" className="underline">Create account</Link> : null}
            {mode === "login" ? <Link to="/recover-password" className="underline">Forgot password?</Link> : null}
          </div>
        </div>
      </section>
    </main>
  );
}

