import * as Dialog from "@radix-ui/react-dialog";
import { useMutation } from "@tanstack/react-query";
import { ExternalLink, GitBranch, X } from "lucide-react";
import {
  Children,
  type ReactNode,
  isValidElement,
  useMemo,
  useState,
} from "react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

import { apiRequest } from "../api/client";
import type { EvidenceArtifact } from "../research/artifact-types";
import { EpistemicBadge, isEpistemicClassification } from "./epistemic-badge";

interface DossierReportProps {
  markdown: string;
  evidence: EvidenceArtifact[];
  conversationId?: string;
  coverageScore?: number | null;
  confidenceScore?: number | null;
  label?: string;
}

interface DossierSection {
  id: string;
  number: number | null;
  title: string;
  markdown: string;
}

interface DossierDocument {
  title: string | null;
  sections: DossierSection[];
}

export function DossierReport({
  markdown,
  evidence,
  conversationId,
  coverageScore,
  confidenceScore,
  label = "Latest completed run",
}: DossierReportProps): React.JSX.Element {
  const document = useMemo(() => parseDossier(markdown), [markdown]);
  const [selectedEvidence, setSelectedEvidence] =
    useState<EvidenceArtifact | null>(null);
  const [branchId, setBranchId] = useState<string | null>(null);
  const loadEvidence = useMutation({
    mutationFn: (evidenceId: string) =>
      apiRequest<EvidenceArtifact>(`/evidence/${evidenceId}`),
    onSuccess: setSelectedEvidence,
  });
  const branchConversation = useMutation({
    mutationFn: () => {
      if (!conversationId) throw new Error("Conversation is unavailable");
      return apiRequest<{ id: string }>(
        `/conversations/${conversationId}/branches`,
        {
          method: "POST",
          body: JSON.stringify({ title: "Follow-up hypothesis" }),
        },
      );
    },
    onSuccess: (branch) => setBranchId(branch.id),
  });

  const matrixSection = document.sections.find(
    (section) => section.number === 7,
  );
  const visibleSections = document.sections.filter(
    (section) => section.number !== 7,
  );
  const leadingSections = visibleSections.filter(
    (section) => section.number === null || section.number < 7,
  );
  const trailingSections = visibleSections.filter(
    (section) => section.number !== null && section.number > 7,
  );
  const hasScores = coverageScore != null || confidenceScore != null;
  const selectedEvidenceIndex = selectedEvidence
    ? evidence.findIndex((item) => item.id === selectedEvidence.id)
    : -1;
  const selectedEvidenceNumber =
    selectedEvidenceIndex >= 0 ? selectedEvidenceIndex + 1 : null;

  function selectEvidence(evidenceId: string): void {
    const localEvidence = evidence.find((item) => item.id === evidenceId);
    if (localEvidence) {
      setSelectedEvidence(localEvidence);
      return;
    }
    loadEvidence.mutate(evidenceId);
  }

  return (
    <div className="min-w-0">
      <div className="flex flex-col gap-5 border-b border-hairline pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">{label}</p>
          <h2 className="mt-2 max-w-4xl font-serif text-3xl font-semibold leading-tight sm:text-4xl">
            {document.title ?? "Research dossier"}
          </h2>
        </div>
        {conversationId ? (
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => branchConversation.mutate()}
              disabled={branchConversation.isPending}
              className="button-secondary"
            >
              <GitBranch aria-hidden="true" size={16} /> Branch investigation
            </button>
            {branchId ? (
              <output className="font-mono text-xs text-teal">
                Branch {branchId.slice(0, 8)} created
              </output>
            ) : null}
          </div>
        ) : null}
      </div>

      {loadEvidence.error || branchConversation.error ? (
        <p role="alert" className="mt-4 text-sm text-red-800">
          {loadEvidence.error?.message ?? branchConversation.error?.message}
        </p>
      ) : null}
      <div className="mt-7 min-w-0">
        {hasScores ? (
          <div
            className="mb-8 grid max-w-sm grid-cols-2 gap-3"
            aria-label="Research quality"
          >
            <ScoreCard label="Coverage" value={coverageScore} />
            <ScoreCard label="Confidence" value={confidenceScore} />
          </div>
        ) : null}

        <div className="dossier-layout">
          <div className="dossier-intro min-w-0">
            {leadingSections.map((section) => (
              <DossierSectionView
                key={section.id}
                section={section}
                evidence={evidence}
                onEvidenceSelect={selectEvidence}
              />
            ))}
          </div>

          {matrixSection ? (
            <div className="dossier-matrix min-w-0">
              <DossierSectionView
                section={matrixSection}
                evidence={evidence}
                onEvidenceSelect={selectEvidence}
                isWide
              />
            </div>
          ) : null}

          <div className="dossier-continuation min-w-0">
            {trailingSections.map((section) => (
              <DossierSectionView
                key={section.id}
                section={section}
                evidence={evidence}
                onEvidenceSelect={selectEvidence}
              />
            ))}
          </div>
        </div>
      </div>

      <EvidenceDialog
        evidence={selectedEvidence}
        referenceNumber={selectedEvidenceNumber}
        onClose={() => setSelectedEvidence(null)}
      />
    </div>
  );
}

function ScoreCard({
  label,
  value,
}: { label: string; value?: number | null }): React.JSX.Element {
  return (
    <div className="surface-card min-w-0 p-3 sm:p-4">
      <p className="text-xs text-ink-secondary">{label}</p>
      <p className="telemetry mt-2 text-2xl font-medium text-teal">
        {value == null ? "—" : `${Math.round(value * 100)}%`}
      </p>
    </div>
  );
}

function DossierSectionView({
  section,
  evidence,
  onEvidenceSelect,
  isWide = false,
}: {
  section: DossierSection;
  evidence: EvidenceArtifact[];
  onEvidenceSelect: (evidenceId: string) => void;
  isWide?: boolean;
}): React.JSX.Element {
  return (
    <section
      id={section.id}
      className={`dossier-section ${isWide ? "dossier-section--wide max-w-none" : ""}`}
    >
      <h2>
        {section.number ? `${section.number}. ` : ""}
        {section.title}
      </h2>
      {section.number === 15 ? (
        <EvidenceLedger
          evidence={evidence}
          onEvidenceSelect={onEvidenceSelect}
        />
      ) : (
        <MarkdownBody
          markdown={section.markdown}
          onEvidenceSelect={onEvidenceSelect}
        />
      )}
    </section>
  );
}

function MarkdownBody({
  markdown,
  onEvidenceSelect,
}: {
  markdown: string;
  onEvidenceSelect: (evidenceId: string) => void;
}): React.JSX.Element {
  return (
    <ReactMarkdown
      skipHtml
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeKatex]}
      components={{
        a: ({ href, children }) => {
          const match = href?.match(/^\/api\/v1\/evidence\/([0-9a-f-]+)$/i);
          const evidenceId = match?.[1];
          if (evidenceId) {
            return (
              <button
                type="button"
                className="citation-link"
                onClick={() => onEvidenceSelect(evidenceId)}
              >
                {children}
              </button>
            );
          }
          if (href?.startsWith("#")) return <a href={href}>{children}</a>;
          return (
            <a href={href} target="_blank" rel="noreferrer">
              {children}
              <ExternalLink
                className="ml-1 inline"
                aria-hidden="true"
                size={12}
              />
            </a>
          );
        },
        strong: ({ children }) => {
          const label = getTextContent(children);
          if (isEpistemicClassification(label)) {
            return <EpistemicBadge classification={label} />;
          }
          return <strong>{children}</strong>;
        },
        p: MarkdownParagraph,
        table: ({ children }) => (
          <section
            className="dossier-table-frame"
            aria-label="Comparison table"
          >
            <table className="dossier-comparison-table">{children}</table>
          </section>
        ),
        td: ({ children }) => (
          <td className={getStatusTone(getTextContent(children))}>
            {children}
          </td>
        ),
      }}
    >
      {markdown}
    </ReactMarkdown>
  );
}

function EvidenceLedger({
  evidence,
  onEvidenceSelect,
}: {
  evidence: EvidenceArtifact[];
  onEvidenceSelect: (evidenceId: string) => void;
}): React.JSX.Element {
  if (evidence.length === 0) {
    return (
      <p className="text-ink-secondary">No evidence records are available.</p>
    );
  }
  return (
    <ol className="evidence-ledger list-none divide-y divide-hairline">
      {evidence.map((item, index) => (
        <li
          key={item.id}
          id={`evidence-${item.id}`}
          className="evidence-anchor py-4 first:pt-0"
        >
          <button
            type="button"
            onClick={() => onEvidenceSelect(item.id)}
            aria-label={`Evidence ${index + 1}: ${item.claim}`}
            className="w-full rounded-lg text-left"
          >
            <strong className="block font-sans text-sm font-medium leading-6">
              {item.claim}
              <span className="ml-2 inline-flex align-middle">
                <EpistemicBadge classification={item.fact_classification} />
              </span>
            </strong>
            <span className="mt-2 block truncate font-mono text-[0.7rem] text-ink-muted">
              {sourceDomain(item.source_url)} · Evidence{" "}
              {formatEvidenceNumber(index + 1)} ·{" "}
              {Math.round(item.confidence * 100)}% confidence
            </span>
          </button>
        </li>
      ))}
    </ol>
  );
}

function EvidenceDialog({
  evidence,
  referenceNumber,
  onClose,
}: {
  evidence: EvidenceArtifact | null;
  referenceNumber: number | null;
  onClose: () => void;
}): React.JSX.Element {
  return (
    <Dialog.Root
      open={evidence !== null}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className="evidence-dialog-overlay fixed inset-0 z-40 bg-ink/45" />
        <Dialog.Content className="evidence-dialog-content fixed inset-x-4 top-1/2 z-50 -translate-y-1/2 outline-none md:left-1/2 md:right-auto md:w-[38rem] md:-translate-x-1/2">
          <div className="evidence-dialog-card relative max-h-[85vh] overflow-y-auto rounded-xl border border-hairline bg-canvas p-6 shadow-lg md:p-8">
            <Dialog.Title className="pr-10 font-serif text-2xl text-ink">
              Evidence detail
            </Dialog.Title>
            <Dialog.Close
              className="absolute right-3 top-3 grid size-11 place-items-center rounded-lg hover:bg-subtle"
              aria-label="Close evidence"
            >
              <X aria-hidden="true" size={20} />
            </Dialog.Close>
            {evidence ? (
              <div className="mt-6 space-y-5">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.04em] text-ink-secondary">
                    Claim
                  </p>
                  <p className="mt-2 leading-7">
                    {evidence.claim}
                    <span className="ml-2 inline-flex align-middle">
                      <EpistemicBadge
                        classification={evidence.fact_classification}
                      />
                    </span>
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.04em] text-ink-secondary">
                    Relevant excerpt
                  </p>
                  <blockquote className="mt-2 leading-7 text-ink-secondary">
                    {evidence.relevant_excerpt ?? "Excerpt unavailable"}
                  </blockquote>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-3 border-t border-hairline pt-4">
                  <span className="font-mono text-xs text-ink-muted">
                    {referenceNumber
                      ? `Evidence ${formatEvidenceNumber(referenceNumber)}`
                      : "Evidence record"}{" "}
                    · {Math.round(evidence.confidence * 100)}% confidence
                  </span>
                  <a
                    href={evidence.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="button-primary evidence-source-button"
                  >
                    Open source <ExternalLink aria-hidden="true" size={15} />
                  </a>
                </div>
              </div>
            ) : null}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function MarkdownParagraph({
  children,
}: { children?: ReactNode }): React.JSX.Element {
  const paragraphChildren = Children.toArray(children);
  const badges = paragraphChildren.filter(isEpistemicStrongElement);
  const content = paragraphChildren.filter(
    (child) => !isEpistemicStrongElement(child),
  );
  return (
    <p>
      {content}
      {badges.length > 0 ? (
        <span className="ml-2 inline-flex flex-wrap gap-1 align-middle">
          {badges}
        </span>
      ) : null}
    </p>
  );
}

function isEpistemicStrongElement(child: ReactNode): boolean {
  if (!isValidElement<{ children?: ReactNode }>(child)) return false;
  return isEpistemicClassification(getTextContent(child.props.children));
}

function formatEvidenceNumber(value: number): string {
  return String(value).padStart(2, "0");
}

function parseDossier(markdown: string): DossierDocument {
  const titleMatch = markdown.match(/^#\s+(.+)$/m);
  const title = titleMatch?.[1]?.trim() ?? null;
  const body = titleMatch
    ? markdown.replace(titleMatch[0], "").trim()
    : markdown;
  const matches = Array.from(body.matchAll(/^##\s+(.+)$/gm));
  if (matches.length === 0) {
    return {
      title,
      sections: [
        { id: "report", number: null, title: "Research notes", markdown: body },
      ],
    };
  }
  const sections = matches.map((match, index): DossierSection => {
    const heading = match[1]?.trim() ?? "Section";
    const numbered = heading.match(/^(\d+)\.\s*(.+)$/);
    const number = numbered ? Number(numbered[1]) : null;
    const sectionTitle = numbered?.[2] ?? heading;
    const start = (match.index ?? 0) + match[0].length;
    const end = matches[index + 1]?.index ?? body.length;
    return {
      id: number ? `dossier-section-${number}` : slugify(sectionTitle),
      number,
      title: sectionTitle,
      markdown: body.slice(start, end).trim(),
    };
  });
  return { title, sections };
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function getTextContent(children: ReactNode): string {
  if (typeof children === "string" || typeof children === "number") {
    return String(children);
  }
  if (Array.isArray(children)) return children.map(getTextContent).join("");
  return "";
}

function sourceDomain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function getStatusTone(value: string): string {
  const normalized = value.trim();
  if (normalized === "✅" || normalized.startsWith("✅ Core")) {
    return "text-emerald-600";
  }
  if (normalized.startsWith("⚠️") || normalized.includes("Partial")) {
    return "text-amber-600";
  }
  if (normalized.startsWith("❌")) return "text-rose-500";
  return "text-slate-700";
}
