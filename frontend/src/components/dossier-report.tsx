import * as Dialog from "@radix-ui/react-dialog";
import { useMutation } from "@tanstack/react-query";
import { ExternalLink, GitBranch, X } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

import { apiRequest } from "../api/client";
import type { EvidenceArtifact } from "../research/artifact-types";

interface DossierReportProps {
  markdown: string;
  evidence: EvidenceArtifact[];
  conversationId?: string;
}

export function DossierReport({
  markdown,
  evidence,
  conversationId,
}: DossierReportProps): React.JSX.Element {
  const [selectedEvidence, setSelectedEvidence] =
    useState<EvidenceArtifact | null>(null);
  const [branchId, setBranchId] = useState<string | null>(null);
  const loadEvidence = useMutation({
    mutationFn: (evidenceId: string) =>
      apiRequest<EvidenceArtifact>(`/evidence/${evidenceId}`),
    onSuccess: setSelectedEvidence,
  });
  const branchConversation = useMutation({
    mutationFn: () =>
      apiRequest<{ id: string }>(`/conversations/${conversationId}/branches`, {
        method: "POST",
        body: JSON.stringify({ title: "Follow-up hypothesis" }),
      }),
    onSuccess: (branch) => setBranchId(branch.id),
  });

  return (
    <div>
      {conversationId ? (
        <div className="mb-6 flex flex-wrap items-center gap-3 border-b border-[var(--line)] pb-5">
          <button
            type="button"
            onClick={() => branchConversation.mutate()}
            disabled={branchConversation.isPending}
            className="inline-flex min-h-11 items-center gap-2 border border-[var(--navy)] px-4 text-sm font-semibold text-[var(--navy)]"
          >
            <GitBranch aria-hidden="true" size={17} /> Branch investigation
          </button>
          {branchId ? (
            <output className="text-sm text-[var(--teal)]">
              Branch {branchId.slice(0, 8)} created
            </output>
          ) : null}
        </div>
      ) : null}
      <article className="dossier-prose">
        <ReactMarkdown
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
                    onClick={() => loadEvidence.mutate(evidenceId)}
                  >
                    {children}
                  </button>
                );
              }
              return (
                <a href={href} target="_blank" rel="noreferrer">
                  {children}
                  <ExternalLink
                    className="ml-1 inline"
                    aria-hidden="true"
                    size={13}
                  />
                </a>
              );
            },
          }}
        >
          {markdown}
        </ReactMarkdown>
      </article>

      <section className="mt-10 border-t border-[var(--line)] pt-6">
        <h2 className="font-display text-2xl">Evidence records</h2>
        <div className="mt-4 divide-y divide-[var(--line)]">
          {evidence.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => loadEvidence.mutate(item.id)}
              className="flex w-full items-start justify-between gap-4 py-4 text-left hover:bg-stone-50"
            >
              <span>
                <strong className="block font-medium">{item.claim}</strong>
                <span className="mt-1 block text-sm text-[var(--muted)]">
                  {item.source_url}
                </span>
              </span>
              <span className="shrink-0 text-sm text-[var(--teal)]">
                {Math.round(item.confidence * 100)}%
              </span>
            </button>
          ))}
        </div>
      </section>

      <Dialog.Root
        open={selectedEvidence !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedEvidence(null);
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-40 bg-black/45" />
          <Dialog.Content className="fixed inset-x-4 top-1/2 z-50 max-h-[85vh] -translate-y-1/2 overflow-y-auto bg-[var(--paper)] p-6 shadow-2xl md:left-1/2 md:right-auto md:w-[38rem] md:-translate-x-1/2 md:p-8">
            <Dialog.Title className="pr-10 font-display text-3xl text-[var(--navy)]">
              Evidence detail
            </Dialog.Title>
            <Dialog.Close
              className="absolute right-4 top-4 grid size-11 place-items-center"
              aria-label="Close evidence"
            >
              <X aria-hidden="true" />
            </Dialog.Close>
            {selectedEvidence ? (
              <div className="mt-6 space-y-5">
                <div>
                  <p className="text-sm font-semibold text-[var(--teal)]">
                    Claim
                  </p>
                  <p className="mt-1 leading-7">{selectedEvidence.claim}</p>
                </div>
                <div>
                  <p className="text-sm font-semibold text-[var(--teal)]">
                    Relevant excerpt
                  </p>
                  <blockquote className="mt-2 border-l border-[var(--line-strong)] pl-4 leading-7 text-[var(--muted)]">
                    {selectedEvidence.relevant_excerpt ?? "Excerpt unavailable"}
                  </blockquote>
                </div>
                <a
                  href={selectedEvidence.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex min-h-11 items-center gap-2 bg-[var(--navy)] px-4 text-sm font-semibold text-white"
                >
                  Open source <ExternalLink aria-hidden="true" size={16} />
                </a>
              </div>
            ) : null}
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
