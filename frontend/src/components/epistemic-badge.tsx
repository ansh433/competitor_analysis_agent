type EpistemicClassification =
  | "sourced_fact"
  | "calculated_result"
  | "analyst_inference"
  | "unavailable_information";

interface EpistemicBadgeProps {
  classification?: string;
  label?: string;
}

const badgeDetails: Record<
  EpistemicClassification,
  { label: string; className: string }
> = {
  sourced_fact: {
    label: "Sourced fact",
    className: "status-badge--fact",
  },
  calculated_result: {
    label: "Calculated result",
    className: "status-badge--calculated",
  },
  analyst_inference: {
    label: "Analyst inference",
    className: "status-badge--inference",
  },
  unavailable_information: {
    label: "Unavailable information",
    className: "status-badge--unavailable",
  },
};

/** Render a semantic claim-classification badge. */
export function EpistemicBadge({
  classification = "unavailable_information",
  label,
}: EpistemicBadgeProps): React.JSX.Element {
  const normalized = normalizeClassification(classification);
  const details = badgeDetails[normalized];
  return (
    <span className={`status-badge ${details.className}`}>
      {label ?? details.label}
    </span>
  );
}

/** Convert a display label or API value to a supported classification. */
export function normalizeClassification(
  value: string,
): EpistemicClassification {
  const normalized = value
    .trim()
    .toLowerCase()
    .replace(/:$/, "")
    .replaceAll(" ", "_");
  if (normalized === "sourced_fact") return "sourced_fact";
  if (normalized === "calculated_result") return "calculated_result";
  if (normalized === "analyst_inference") return "analyst_inference";
  return "unavailable_information";
}

/** Return whether text names an epistemic classification. */
export function isEpistemicClassification(value: string): boolean {
  const normalized = value
    .trim()
    .toLowerCase()
    .replace(/:$/, "")
    .replaceAll(" ", "_");
  return normalized in badgeDetails;
}
