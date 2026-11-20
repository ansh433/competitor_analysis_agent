import { Link, useNavigate } from "@tanstack/react-router";
import { ArrowRight, Compass, Globe2 } from "lucide-react";
import type { FormEvent } from "react";

import { useAuth } from "../auth/auth-context";
import { storeResearchCompanyPrefill } from "../research/prefill";

/** Present the public research entry point. */
export function LandingPage(): React.JSX.Element {
  const { currentUser, isLoading } = useAuth();
  const navigate = useNavigate();
  const userLabel =
    currentUser?.full_name?.trim() || currentUser?.email || "Account";
  const userInitials = currentUser
    ? getUserInitials(currentUser.full_name, currentUser.email)
    : "";

  function handleCompanySubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const company = String(
      new FormData(event.currentTarget).get("company") ?? "",
    );
    storeResearchCompanyPrefill(company);
    void navigate({ to: currentUser ? "/research" : "/signup" });
  }

  return (
    <main className="min-h-screen bg-[#e6efe8] text-ink">
      <header className="border-b border-[#c8d8cd] bg-[#e6efe8]">
        <div className="mx-auto flex min-h-20 max-w-6xl items-center justify-between gap-4 px-4 sm:px-8">
          <Link
            to="/"
            className="flex min-h-11 items-center gap-3 font-serif text-2xl text-pine"
          >
            <span className="grid size-9 place-items-center rounded-lg bg-pine text-brass">
              <Compass aria-hidden="true" size={20} />
            </span>
            Compass
          </Link>
          {isLoading ? (
            <span className="size-11" aria-hidden="true" />
          ) : currentUser ? (
            <Link
              to="/dashboard"
              aria-label={`Open dashboard for ${userLabel}`}
              title={userLabel}
              className="grid size-11 place-items-center rounded-full border border-pine bg-pine font-sans text-sm font-semibold tracking-[0.02em] text-canvas shadow-sm"
            >
              {userInitials}
            </Link>
          ) : (
            <Link to="/signup" className="button-primary">
              Sign up
            </Link>
          )}
        </div>
      </header>

      <section className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-5xl flex-col items-center justify-start px-4 pb-16 pt-14 text-center sm:justify-center sm:px-8 sm:py-20">
        <h1 className="max-w-[16ch] font-serif text-[clamp(3rem,6.2vw,5.35rem)] font-medium leading-[1.02] tracking-[-0.035em] text-pine">
          Know where a company stands before you decide.
        </h1>
        <p className="mt-7 max-w-[44rem] text-balance text-lg leading-8 text-ink-secondary sm:text-xl">
          A company, its competitors, and the evidence behind the comparison.
          Keep what is known separate from what is inferred—and what is still
          missing.
        </p>

        <form
          onSubmit={handleCompanySubmit}
          className="mt-9 w-full max-w-[46rem]"
        >
          <div className="flex flex-col gap-2 rounded-[var(--radius-card)] border border-[#bfd1c4] bg-surface p-2 shadow-quiet sm:flex-row sm:items-center">
            <div className="flex min-h-14 min-w-0 flex-1 items-center gap-3 px-3">
              <Globe2
                className="shrink-0 text-ink-secondary"
                aria-hidden="true"
                size={19}
              />
              <input
                id="research-company"
                name="company"
                aria-label="Company name or website"
                className="min-w-0 flex-1 bg-transparent text-base text-ink outline-none placeholder:text-ink-secondary"
                placeholder="Company name or website"
                required
              />
            </div>
            <button type="submit" className="button-primary min-h-14 px-5">
              Research company <ArrowRight aria-hidden="true" size={18} />
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

function getUserInitials(fullName: string | null, email: string): string {
  const nameParts = fullName?.trim().split(/\s+/).filter(Boolean) ?? [];
  if (nameParts.length > 0) {
    const firstInitial = nameParts[0]?.[0] ?? "";
    const lastInitial =
      nameParts.length > 1 ? (nameParts.at(-1)?.[0] ?? "") : "";
    return `${firstInitial}${lastInitial}`.toUpperCase();
  }
  return email.slice(0, 2).toUpperCase();
}
