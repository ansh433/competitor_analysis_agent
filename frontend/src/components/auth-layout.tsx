import type { ReactNode } from "react";

interface AuthLayoutProps {
  title: string;
  description: string;
  children: ReactNode;
}

/** Provide one responsive frame for every authentication state. */
export function AuthLayout({
  title,
  description,
  children,
}: AuthLayoutProps): React.JSX.Element {
  return (
    <main className="min-h-dvh bg-canvas lg:grid lg:grid-cols-[0.8fr_1.2fr]">
      <aside className="hidden min-h-dvh bg-pine p-12 text-canvas lg:flex lg:items-center">
        <p className="max-w-lg font-serif text-[clamp(2.75rem,4vw,4.5rem)] font-medium leading-[1.05] tracking-[-0.025em]">
          Company research in one workspace.
        </p>
      </aside>

      <section className="flex min-h-dvh items-center justify-center px-6 py-8 sm:px-8 lg:px-12 lg:py-12">
        <div className="mx-auto w-full max-w-md">
          <h1 className="font-serif text-[clamp(2.25rem,6vw,3rem)] font-semibold leading-[1.08] tracking-[-0.02em] text-ink">
            {title}
          </h1>
          <p className="mt-3 leading-7 text-ink-secondary">{description}</p>
          {children}
        </div>
      </section>
    </main>
  );
}
