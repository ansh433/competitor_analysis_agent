import { Link, useNavigate } from "@tanstack/react-router";
import { Eye, EyeOff } from "lucide-react";
import { type FormEvent, useState } from "react";

import { apiRequest } from "../api/client";
import { useAuth } from "../auth/auth-context";
import { AuthLayout } from "../components/auth-layout";

type AuthPageMode = "login" | "signup" | "recover" | "reset";

interface AuthPageProps {
  mode: AuthPageMode;
}

const content: Record<
  AuthPageMode,
  { title: string; description: string; action: string }
> = {
  login: {
    title: "Sign in",
    description: "Access your workspace.",
    action: "Sign in",
  },
  signup: {
    title: "Create an account",
    description: "Start your research.",
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

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
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
          body: JSON.stringify({
            email,
            password,
            full_name: String(data.get("fullName") ?? ""),
          }),
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
        const token =
          new URLSearchParams(window.location.search).get("token") ?? "";
        await apiRequest("/auth/password-reset", {
          method: "POST",
          body: JSON.stringify({ token, new_password: password }),
        });
        setMessage("Password updated. You can now sign in.");
      }
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Request failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  const page = content[mode];
  const showEmail = mode !== "reset";
  const showPassword =
    mode === "login" || mode === "signup" || mode === "reset";

  return (
    <AuthLayout title={page.title} description={page.description}>
      <form
        onSubmit={handleSubmit}
        aria-busy={isSubmitting}
        className="mt-8 space-y-5"
      >
        {mode === "signup" ? (
          <label className="block text-sm font-medium">
            Full name
            <input
              name="fullName"
              required
              className="form-input"
              autoComplete="name"
            />
          </label>
        ) : null}
        {showEmail ? (
          <label className="block text-sm font-medium">
            Email address
            <input
              name="email"
              type="email"
              required
              className="form-input"
              autoComplete="email"
              autoCapitalize="none"
              spellCheck={false}
            />
          </label>
        ) : null}
        {showPassword ? (
          <PasswordField
            key={mode}
            label={mode === "reset" ? "New password" : "Password"}
            minLength={mode === "login" ? 1 : 12}
            autoComplete={
              mode === "login" ? "current-password" : "new-password"
            }
            guidanceId={mode === "signup" ? "password-guidance" : undefined}
          />
        ) : null}
        {mode === "signup" ? (
          <p id="password-guidance" className="text-sm text-ink-secondary">
            At least 12 characters.
          </p>
        ) : null}
        {error ? (
          <p
            role="alert"
            className="rounded-md bg-red-50 p-3 text-sm text-red-800"
          >
            {error}
          </p>
        ) : null}
        {message ? (
          <output className="block rounded-md bg-emerald-50 p-3 text-sm text-emerald-900">
            {message}
          </output>
        ) : null}
        <button
          type="submit"
          disabled={isSubmitting}
          className="button-primary min-h-12 w-full"
        >
          {isSubmitting ? "Working…" : page.action}
        </button>
      </form>
      <div className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-sm text-ink-secondary">
        {mode === "signup" ? (
          <p className="flex min-h-11 items-center gap-1.5">
            <span>Already registered?</span>
            <Link to="/login" className="text-link font-medium">
              Sign in
            </Link>
          </p>
        ) : null}
        {mode === "recover" || mode === "reset" ? (
          <Link
            to="/login"
            className="text-link inline-flex min-h-11 items-center"
          >
            Sign in
          </Link>
        ) : null}
        {mode === "login" ? (
          <Link
            to="/signup"
            className="text-link inline-flex min-h-11 items-center"
          >
            Create account
          </Link>
        ) : null}
        {mode === "login" ? (
          <Link
            to="/recover-password"
            className="text-link inline-flex min-h-11 items-center"
          >
            Forgot password?
          </Link>
        ) : null}
      </div>
    </AuthLayout>
  );
}

interface PasswordFieldProps {
  label: string;
  minLength: number;
  autoComplete: "current-password" | "new-password";
  guidanceId?: string;
}

function PasswordField({
  label,
  minLength,
  autoComplete,
  guidanceId,
}: PasswordFieldProps): React.JSX.Element {
  const [isVisible, setIsVisible] = useState(false);
  return (
    <div>
      <label htmlFor="auth-password" className="block text-sm font-medium">
        {label}
      </label>
      <span className="relative mt-2 block">
        <input
          id="auth-password"
          name="password"
          type={isVisible ? "text" : "password"}
          minLength={minLength}
          required
          className="form-input form-input--embedded"
          autoComplete={autoComplete}
          aria-describedby={guidanceId}
        />
        <button
          type="button"
          onClick={() => setIsVisible((current) => !current)}
          className="absolute inset-y-1 right-1 grid w-10 place-items-center rounded-md text-ink-secondary hover:bg-subtle hover:text-ink"
          aria-label={isVisible ? "Hide password" : "Show password"}
          aria-pressed={isVisible}
        >
          {isVisible ? (
            <EyeOff aria-hidden="true" size={18} />
          ) : (
            <Eye aria-hidden="true" size={18} />
          )}
        </button>
      </span>
    </div>
  );
}
