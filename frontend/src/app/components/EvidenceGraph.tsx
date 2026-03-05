import { useState } from "react";
import type { SectionPointer } from "../../types";

interface EvidenceGraphProps {
  results: SectionPointer[];
  query?: string;
}

export function EvidenceGraph({ results, query = "Query" }: EvidenceGraphProps) {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  if (results.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-gray-500">
        Submit a query to see the evidence graph.
      </div>
    );
  }

  const top = results.slice(0, 5);
  const maxScore = Math.max(...top.map((r) => r.reranker_score), 0.001);

  // Layout: query node at top, result nodes below
  const svgWidth = 450;
  const queryNode = { id: "query", x: svgWidth / 2, y: 50 };
  const nodeY = 160;
  const nodeSpacing = svgWidth / (top.length + 1);

  const paperNodes = top.map((r, i) => ({
    id: r.chunk_id,
    x: nodeSpacing * (i + 1),
    y: nodeY,
    result: r,
    score: r.reranker_score / maxScore,
  }));

  return (
    <div className="w-full bg-gray-50 p-4 rounded">
      <svg viewBox={`0 0 ${svgWidth} 260`} className="w-full">
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#64748b" />
          </marker>
        </defs>

        {/* Edges: query → each paper */}
        {paperNodes.map((node) => (
          <line
            key={`edge-${node.id}`}
            x1={queryNode.x}
            y1={queryNode.y + 20}
            x2={node.x}
            y2={node.y - 22}
            stroke="#94a3b8"
            strokeWidth="1.5"
            markerEnd="url(#arrow)"
            opacity="0.6"
          />
        ))}

        {/* Query node */}
        <g
          transform={`translate(${queryNode.x - 90}, ${queryNode.y - 20})`}
          onClick={() => setSelectedNode("query")}
          className="cursor-pointer"
        >
          <rect
            width="180"
            height="40"
            rx="4"
            fill="#1e293b"
            stroke={selectedNode === "query" ? "#64748b" : "#1e293b"}
            strokeWidth={selectedNode === "query" ? "3" : "1.5"}
          />
          <foreignObject width="180" height="40">
            <div className="flex items-center justify-center h-full px-2">
              <span className="text-[10px] text-white font-semibold text-center line-clamp-2">
                {query.length > 60 ? query.slice(0, 60) + "…" : query}
              </span>
            </div>
          </foreignObject>
        </g>

        {/* Paper nodes */}
        {paperNodes.map((node) => {
          const isSelected = selectedNode === node.id;
          const opacity = 0.4 + node.score * 0.6;
          return (
            <g
              key={node.id}
              transform={`translate(${node.x - 65}, ${node.y - 22})`}
              onClick={() => setSelectedNode(node.id)}
              className="cursor-pointer"
            >
              <rect
                width="130"
                height="44"
                rx="4"
                fill="#ffffff"
                stroke={isSelected ? "#334155" : "#cbd5e1"}
                strokeWidth={isSelected ? "2.5" : "1.5"}
                opacity={opacity}
              />
              <foreignObject width="130" height="44">
                <div className="flex flex-col items-center justify-center h-full px-2 text-center">
                  <div className="text-[8px] font-semibold text-slate-800 line-clamp-2 leading-tight">
                    {node.result.paper_title.length > 40
                      ? node.result.paper_title.slice(0, 40) + "…"
                      : node.result.paper_title}
                  </div>
                  <div className="text-[7px] text-slate-500 mt-0.5">
                    {(node.result.reranker_score * 100).toFixed(0)}%
                  </div>
                </div>
              </foreignObject>
            </g>
          );
        })}
      </svg>

      <div className="mt-2 pt-3 border-t border-gray-300 flex items-center justify-center gap-6 text-xs">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-slate-900 rounded" />
          <span className="text-gray-600">Query</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-white border border-slate-300 rounded" />
          <span className="text-gray-600">Section (opacity = relevance)</span>
        </div>
      </div>
    </div>
  );
}
