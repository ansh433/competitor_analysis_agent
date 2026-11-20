import { Link } from "@tanstack/react-router";

import { DossierReport } from "../components/dossier-report";
import { demoEvidence, demoReportMarkdown } from "../demo/demo-report-data";

/** Render the production dossier surface with static data for visual inspection. */
export function DemoReportPage(): React.JSX.Element {
  return (
    <main className="min-h-screen bg-canvas px-4 py-7 text-ink sm:px-8 sm:py-8">
      <section className="mx-auto max-w-6xl">
        <Link to="/" className="text-link text-sm">
          Back to Compass
        </Link>
        <div className="mt-8">
          <DossierReport
            markdown={demoReportMarkdown}
            evidence={demoEvidence}
            coverageScore={0.68}
            confidenceScore={0.82}
            label="Northstar Workspace"
          />
        </div>
      </section>
    </main>
  );
}
