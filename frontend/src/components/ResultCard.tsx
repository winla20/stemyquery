import type { SectionPointer } from "../types";
import { ConfidenceBadge } from "./ConfidenceBadge";

interface Props {
  result: SectionPointer;
  rank: number;
  onOpenContext: (chunkId: string) => void;
}

export function ResultCard({ result, rank, onOpenContext }: Props) {
  return (
    <div style={{
      border: "1px solid #e5e7eb",
      borderRadius: 8,
      padding: "14px 18px",
      marginBottom: 12,
      background: "#fff",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
        <span style={{ fontWeight: 700, color: "#6b7280", minWidth: 24 }}>#{rank}</span>
        <ConfidenceBadge level={result.confidence} />
        <span style={{ fontWeight: 600, fontSize: 14, flex: 1 }}>
          {result.section_path || "(no section)"}
        </span>
        <span style={{ fontSize: 12, color: "#9ca3af" }}>
          p.{result.page_start}{result.page_end !== result.page_start ? `–${result.page_end}` : ""}
        </span>
      </div>

      <div style={{ fontSize: 13, color: "#374151", marginBottom: 4 }}>
        <span style={{ fontWeight: 500 }}>{result.paper_title}</span>
        {result.pmid && (
          <span style={{ color: "#6b7280", marginLeft: 8 }}>PMID: {result.pmid}</span>
        )}
      </div>

      <ul style={{ margin: "6px 0 10px 0", paddingLeft: 18 }}>
        {result.snippets.map((s, i) => (
          <li key={i} style={{ fontSize: 13, color: "#4b5563", marginBottom: 2 }}>{s}</li>
        ))}
      </ul>

      <button
        onClick={() => onOpenContext(result.chunk_id)}
        style={{
          fontSize: 12,
          padding: "4px 10px",
          borderRadius: 4,
          border: "1px solid #d1d5db",
          background: "#f9fafb",
          cursor: "pointer",
        }}
      >
        Open in context
      </button>
    </div>
  );
}
