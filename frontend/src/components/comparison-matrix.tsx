import { EpistemicBadge } from "./epistemic-badge";

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

export function ComparisonMatrixView({
  comparison,
}: { comparison: Record<string, unknown> }): React.JSX.Element {
  const normalized = normalizeComparison(comparison);
  if (!normalized)
    return (
      <p className="text-ink-secondary">Comparison data is unavailable.</p>
    );
  return (
    <section
      aria-label="Comparison matrix"
      className="relative isolate w-full max-w-full overflow-x-auto overscroll-x-contain rounded-2xl border border-slate-200 bg-white shadow-sm"
    >
      <table className="w-full min-w-[900px] table-fixed border-collapse text-left text-[0.8125rem] leading-[1.45] text-slate-700">
        <thead className="bg-slate-50 text-base uppercase tracking-wide text-slate-600">
          <tr>
            <th
              scope="col"
              className="sticky left-0 z-30 w-36 min-w-36 max-w-36 border-b border-r border-slate-200 bg-slate-50 px-4 py-3 font-bold sm:w-44 sm:min-w-44 sm:max-w-44"
            >
              Dimension
            </th>
            {normalized.companyNames.map((name, index) => (
              <th
                scope="col"
                key={name}
                className={`border-b border-slate-200 px-4 py-3 font-bold ${
                  index === normalized.companyNames.length - 1
                    ? "border-r-0"
                    : "border-r border-slate-100"
                }`}
              >
                {name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {normalized.rows.map((row, rowIndex) => {
            const isEvenRow = rowIndex % 2 === 1;
            return (
              <tr
                key={row.dimension}
                className={`group ${
                  isEvenRow
                    ? "bg-slate-50/50 hover:bg-slate-100"
                    : "bg-white hover:bg-slate-50"
                }`}
              >
                <th
                  scope="row"
                  className={`sticky left-0 z-20 w-36 min-w-36 max-w-36 border-r border-slate-100 px-4 py-3 align-top font-medium text-slate-900 sm:w-44 sm:min-w-44 sm:max-w-44 ${
                    isEvenRow
                      ? "bg-slate-50 group-hover:bg-slate-100"
                      : "bg-white group-hover:bg-slate-50"
                  }`}
                >
                  {row.dimension}
                </th>
                {normalized.companyNames.map((companyName, columnIndex) => {
                  const cell = row.cells.find(
                    (item) => item.company_name === companyName,
                  );
                  return (
                    <td
                      key={companyName}
                      className={`px-4 py-3 text-left align-top ${getStatusTone(
                        cell?.value,
                      )} ${
                        columnIndex === normalized.companyNames.length - 1
                          ? "border-r-0"
                          : "border-r border-slate-100"
                      }`}
                    >
                      <span className="block">
                        {cell?.value ?? "Unavailable"}
                      </span>
                      <span className="mt-2 block">
                        <EpistemicBadge
                          classification={
                            cell?.classification ?? "unavailable_information"
                          }
                        />
                      </span>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

function getStatusTone(value: string | null | undefined): string {
  const normalized = value?.trim() ?? "";
  if (normalized === "✅" || normalized.startsWith("✅ Core")) {
    return "text-emerald-600";
  }
  if (normalized.startsWith("⚠️") || normalized.includes("Partial")) {
    return "text-amber-600";
  }
  if (normalized.startsWith("❌")) return "text-rose-500";
  return "text-slate-700";
}

function normalizeComparison(
  value: Record<string, unknown>,
): NormalizedComparison | null {
  const names = value.company_names;
  const rows = value.rows;
  if (
    !Array.isArray(names) ||
    !names.every((item) => typeof item === "string") ||
    !Array.isArray(rows)
  )
    return null;
  const normalizedRows: ComparisonRow[] = [];
  for (const row of rows) {
    if (!row || typeof row !== "object") return null;
    const record = row as Record<string, unknown>;
    if (typeof record.dimension !== "string" || !Array.isArray(record.cells))
      return null;
    const cells: ComparisonCell[] = [];
    for (const cell of record.cells) {
      if (!cell || typeof cell !== "object") return null;
      const item = cell as Record<string, unknown>;
      if (
        typeof item.company_name !== "string" ||
        (typeof item.value !== "string" && item.value !== null) ||
        typeof item.classification !== "string"
      )
        return null;
      cells.push({
        company_name: item.company_name,
        value: item.value,
        classification: item.classification,
      });
    }
    normalizedRows.push({ dimension: record.dimension, cells });
  }
  return { companyNames: names, rows: normalizedRows };
}
