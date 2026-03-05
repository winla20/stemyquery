import { useState } from "react";
import { FileText, Network, BarChart3 } from "lucide-react";
import { EvidenceGraph } from "./EvidenceGraph";
import type { SectionPointer } from "../../types";

type TabType = "source" | "relevance" | "graph";

interface EvidencePanelProps {
  results: SectionPointer[];
  selectedResult: SectionPointer | null;
  onOpenContext: (chunkId: string) => void;
}

export function EvidencePanel({ results, selectedResult, onOpenContext }: EvidencePanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>("source");

  const maxScore = results.length > 0
    ? Math.max(...results.map((r) => r.reranker_score))
    : 1;

  return (
    <div className="h-full flex flex-col bg-white border-l border-gray-200">
      {/* Header with Tabs */}
      <div className="border-b border-gray-200">
        <div className="p-4 pb-0">
          <h2 className="text-sm uppercase tracking-wider text-gray-600">Evidence & Analysis</h2>
        </div>

        <div className="flex">
          {(
            [
              { id: "source", icon: FileText, label: "Source Text" },
              { id: "relevance", icon: BarChart3, label: "Relevance" },
              { id: "graph", icon: Network, label: "Graph" },
            ] as const
          ).map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm transition-colors border-b-2 ${
                activeTab === id
                  ? "border-slate-900 text-slate-900"
                  : "border-transparent text-gray-600 hover:text-gray-900"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Source Text */}
        {activeTab === "source" && (
          <div className="p-4 space-y-4">
            {!selectedResult && (
              <p className="text-xs text-gray-500">
                Click a result card to view its source text here.
              </p>
            )}
            {selectedResult && (
              <div className="border border-gray-200 rounded p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs text-slate-500 uppercase tracking-wider">
                    {selectedResult.section_path}
                  </span>
                </div>
                <p className="text-sm font-medium text-slate-800 mb-3">
                  {selectedResult.paper_title}
                </p>
                {selectedResult.snippets.map((snip, i) => (
                  <p
                    key={i}
                    className="text-sm leading-relaxed text-gray-800 mb-3 italic border-l-2 border-slate-300 pl-3"
                    style={{ fontFamily: "Georgia, serif" }}
                  >
                    {snip}
                  </p>
                ))}
                <button
                  onClick={() => onOpenContext(selectedResult.chunk_id)}
                  className="mt-2 text-xs text-slate-700 underline hover:text-slate-900 transition-colors"
                >
                  Open full context →
                </button>
              </div>
            )}
          </div>
        )}

        {/* Relevance */}
        {activeTab === "relevance" && (
          <div className="p-4">
            <p className="text-xs text-gray-600 mb-4">
              Scores normalized to highest result (100%). Based on cross-encoder reranking.
            </p>
            {results.length === 0 && (
              <p className="text-xs text-gray-500">No results to display.</p>
            )}
            <div className="space-y-3">
              {results.map((r, idx) => {
                const pct = (r.reranker_score / maxScore) * 100;
                return (
                  <div key={r.chunk_id} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-800 line-clamp-1 flex-1 mr-2">
                        #{idx + 1} {r.paper_title.length > 35 ? r.paper_title.slice(0, 35) + "…" : r.paper_title}
                      </span>
                      <span className="font-semibold text-slate-900 flex-shrink-0">
                        {pct.toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-slate-700 rounded-full transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            {results.length > 0 && (
              <div className="mt-6 p-4 bg-slate-50 border border-slate-200 rounded">
                <h3 className="text-xs uppercase tracking-wider text-slate-700 mb-2">
                  Scoring Methodology
                </h3>
                <ul className="text-xs text-gray-700 space-y-1">
                  <li>• Hybrid BM25 + MedCPT dense retrieval</li>
                  <li>• MedCPT cross-encoder reranking</li>
                  <li>• Section path + text passage scoring</li>
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Graph */}
        {activeTab === "graph" && (
          <div className="p-4">
            <p className="text-xs text-gray-600 mb-4">
              Evidence graph showing top sections retrieved for the query. Node opacity indicates relevance score.
            </p>
            <EvidenceGraph results={results} />
          </div>
        )}
      </div>
    </div>
  );
}
