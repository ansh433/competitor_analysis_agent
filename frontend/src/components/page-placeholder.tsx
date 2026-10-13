interface PagePlaceholderProps {
  title: string;
  description: string;
}

export function PagePlaceholder({ title, description }: PagePlaceholderProps): React.JSX.Element {
  return (
    <section className="max-w-5xl">
      <p className="mb-3 text-sm font-semibold text-[var(--teal)]">Intelligence workspace</p>
      <h1 className="font-display text-4xl leading-tight text-[var(--navy)] md:text-5xl">{title}</h1>
      <p className="mt-5 max-w-2xl text-lg leading-8 text-[var(--muted)]">{description}</p>
      <div className="mt-10 border border-dashed border-[var(--line-strong)] bg-white p-8">
        <p className="text-sm text-[var(--muted)]">This view becomes active as research data is added.</p>
      </div>
    </section>
  );
}

