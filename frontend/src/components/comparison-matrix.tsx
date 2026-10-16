interface ComparisonCell {
  company_name: string;
  value: string | null;
  classification: string;
}

interface ComparisonRow {
  dimension: string;
  cells: ComparisonCell[];
}

interface NormalizedComparison {
  companyNames: string[];
  rows: ComparisonRow[];
}

export function ComparisonMatrixView({ comparison }: { comparison: Record<string, unknown> }): React.JSX.Element {
  const normalized = normalizeComparison(comparison);
  if (!normalized) return <p className="text-[var(--muted)]">Comparison data is unavailable.</p>;
  return (
    <div className="overflow-x-auto border border-[var(--line)]">
      <table className="w-full min-w-[48rem] border-collapse text-left text-sm">
        <thead className="bg-[var(--navy)] text-white">
          <tr><th className="p-4 font-semibold">Dimension</th>{normalized.companyNames.map((name) => <th key={name} className="p-4 font-semibold">{name}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-[var(--line)] bg-white">
          {normalized.rows.map((row) => (
            <tr key={row.dimension}>
              <th className="p-4 align-top font-semibold text-[var(--navy)]">{row.dimension}</th>
              {normalized.companyNames.map((companyName) => {
                const cell = row.cells.find((item) => item.company_name === companyName);
                return <td key={companyName} className="p-4 align-top"><span>{cell?.value ?? "Unavailable"}</span><span className="mt-2 block text-xs text-[var(--muted)]">{cell?.classification.replaceAll("_", " ") ?? "unavailable information"}</span></td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function normalizeComparison(value: Record<string, unknown>): NormalizedComparison | null {
  const names = value.company_names;
  const rows = value.rows;
  if (!Array.isArray(names) || !names.every((item) => typeof item === "string") || !Array.isArray(rows)) return null;
  const normalizedRows: ComparisonRow[] = [];
  for (const row of rows) {
    if (!row || typeof row !== "object") return null;
    const record = row as Record<string, unknown>;
    if (typeof record.dimension !== "string" || !Array.isArray(record.cells)) return null;
    const cells: ComparisonCell[] = [];
    for (const cell of record.cells) {
      if (!cell || typeof cell !== "object") return null;
      const item = cell as Record<string, unknown>;
      if (typeof item.company_name !== "string" || (typeof item.value !== "string" && item.value !== null) || typeof item.classification !== "string") return null;
      cells.push({ company_name: item.company_name, value: item.value, classification: item.classification });
    }
    normalizedRows.push({ dimension: record.dimension, cells });
  }
  return { companyNames: names, rows: normalizedRows };
}

