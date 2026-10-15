import { Check, CircleDashed, Database, Search, Wrench } from "lucide-react";

export interface ResearchStageView {
  name: string;
  detail: string;
  status: "active" | "complete";
}

export interface ToolExecutionView {
  executionId: string;
  name: string;
  status: "active" | "complete" | "failed";
  executionTimeMs?: number;
}

interface ResearchProgressProps {
  stages: ResearchStageView[];
  tools: ToolExecutionView[];
  sources: Array<{ sourceId: string; title: string; publisher: string }>;
  streamedText: string;
  isFinished: boolean;
}

export function ResearchProgress({ stages, tools, sources, streamedText, isFinished }: ResearchProgressProps): React.JSX.Element {
  return (
    <section aria-live="polite" className="mt-10 grid gap-6 lg:grid-cols-[20rem_1fr]">
      <div className="space-y-6">
        <div className="border border-[var(--line)] bg-white p-5">
          <h2 className="flex items-center gap-2 font-display text-xl"><Search aria-hidden="true" size={19} /> Research stages</h2>
          <ol className="mt-4 space-y-3">
            {stages.map((stage) => (
              <li key={`${stage.name}-${stage.status}`} className="flex gap-3 text-sm">
                {stage.status === "complete" ? <Check className="mt-0.5 text-emerald-700" size={17} /> : <CircleDashed className="mt-0.5 animate-spin text-[var(--teal)]" size={17} />}
                <span><strong className="block font-medium">{stage.name.replaceAll("_", " ")}</strong><span className="text-[var(--muted)]">{stage.detail}</span></span>
              </li>
            ))}
          </ol>
        </div>
        <div className="border border-[var(--line)] bg-white p-5">
          <h2 className="flex items-center gap-2 font-display text-xl"><Wrench aria-hidden="true" size={19} /> Tool timeline</h2>
          <ul className="mt-4 space-y-3 text-sm">
            {tools.length === 0 ? <li className="text-[var(--muted)]">No tools started yet.</li> : tools.map((tool) => (
              <li key={tool.executionId} className="flex justify-between gap-3"><span>{tool.name.replaceAll("_", " ")}</span><span className="text-[var(--muted)]">{tool.status === "active" ? "Running" : `${tool.executionTimeMs ?? 0} ms`}</span></li>
            ))}
          </ul>
        </div>
      </div>
      <div className="min-w-0 border border-[var(--line)] bg-white">
        <div className="flex items-center justify-between border-b border-[var(--line)] px-6 py-4">
          <h2 className="font-display text-2xl">Live research notes</h2>
          <span className="text-sm text-[var(--muted)]">{isFinished ? "Complete" : "In progress"}</span>
        </div>
        <div className="min-h-64 whitespace-pre-wrap p-6 leading-7">{streamedText || "The first verified findings will appear here."}</div>
        <div className="border-t border-[var(--line)] bg-stone-50 px-6 py-4">
          <p className="flex items-center gap-2 text-sm font-medium"><Database aria-hidden="true" size={16} /> {sources.length} sources collected</p>
        </div>
      </div>
    </section>
  );
}

