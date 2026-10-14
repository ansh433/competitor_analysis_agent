import { AlertTriangle, ArrowRight, Gauge } from "lucide-react";

import { useQuotaStatus } from "../quotas/use-quota";

export function ResearchStartPage(): React.JSX.Element {
  const quota = useQuotaStatus();
  const standard = quota.data?.tiers.find((tier) => tier.tier === "standard");
  const isDisabled = !quota.isLoading && !quota.data?.can_start_research;

  return (
    <section className="mx-auto max-w-6xl">
      <div className="grid gap-10 lg:grid-cols-[1fr_20rem]">
        <div>
          <p className="mb-3 text-sm font-semibold text-[var(--teal)]">New intelligence brief</p>
          <h1 className="max-w-3xl font-display text-4xl leading-tight text-[var(--navy)] md:text-6xl">
            Begin with a company. End with an evidence ledger.
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-[var(--muted)]">
            Define the decision you need to make. Compass resolves the company, discovers alternatives,
            and shows the source behind every material claim.
          </p>

          {isDisabled ? (
            <div role="alert" className="mt-8 flex gap-3 border border-amber-300 bg-amber-50 p-4 text-amber-950">
              <AlertTriangle className="mt-0.5 shrink-0" aria-hidden="true" size={20} />
              Daily research allowance exhausted. Existing dossiers remain available until the quota resets.
            </div>
          ) : null}

          <form className="mt-10 space-y-6 border border-[var(--line)] bg-white p-6 md:p-8">
            <label className="block text-sm font-semibold">
              Company name or website
              <input
                className="form-input"
                placeholder="Example: Linear or linear.app"
                disabled={isDisabled}
              />
            </label>
            <label className="block text-sm font-semibold">
              Research objective
              <textarea
                className="form-input min-h-36 resize-y"
                placeholder="Assess product differentiation, pricing, and direct competitors for a market-entry decision."
                disabled={isDisabled}
              />
            </label>
            <button
              type="button"
              disabled={isDisabled || quota.isLoading}
              className="inline-flex min-h-12 items-center gap-2 bg-[var(--navy)] px-5 font-semibold text-white hover:bg-[var(--navy-light)] disabled:cursor-not-allowed disabled:opacity-50"
            >
              Begin research <ArrowRight aria-hidden="true" size={18} />
            </button>
          </form>
        </div>

        <aside aria-label="Research allowance" className="h-fit border-t-4 border-[var(--signal)] bg-[var(--navy)] p-6 text-white lg:mt-24">
          <Gauge aria-hidden="true" className="text-[var(--signal)]" />
          <h2 className="mt-4 font-display text-2xl">Today’s allowance</h2>
          <p className="mt-3 text-sm leading-6 text-teal-50/75">
            Standard runs remaining
          </p>
          <p className="mt-1 font-display text-5xl">{quota.isLoading ? "—" : standard?.bypassed ? "∞" : (standard?.remaining ?? 0)}</p>
          <dl className="mt-6 space-y-3 border-t border-white/15 pt-5 text-sm">
            <div className="flex justify-between gap-4"><dt className="text-teal-50/65">Source ceiling</dt><dd>{quota.data?.maximum_sources_per_run ?? "—"}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-teal-50/65">Gap loops</dt><dd>{quota.data?.maximum_gap_research_loops ?? "—"}</dd></div>
          </dl>
        </aside>
      </div>
    </section>
  );
}

