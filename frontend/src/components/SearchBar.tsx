import { useState } from "react";
import type { Paper } from "../types";

interface Props {
  papers: Paper[];
  isLoading: boolean;
  onSearch: (query: string, paperId: string, topN: number) => void;
}

export function SearchBar({ papers, isLoading, onSearch }: Props) {
  const [query, setQuery] = useState("");
  const [paperId, setPaperId] = useState("");
  const [topN, setTopN] = useState(8);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim(), paperId, topN);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: 24 }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. electrophysiology assessment metrics"
          style={{
            flex: 1,
            padding: "10px 14px",
            borderRadius: 6,
            border: "1px solid #d1d5db",
            fontSize: 14,
          }}
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          style={{
            padding: "10px 20px",
            borderRadius: 6,
            border: "none",
            background: isLoading ? "#9ca3af" : "#2563eb",
            color: "#fff",
            fontWeight: 600,
            cursor: isLoading ? "not-allowed" : "pointer",
            fontSize: 14,
          }}
        >
          {isLoading ? "Searching…" : "Search"}
        </button>
      </div>

      <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
        <select
          value={paperId}
          onChange={(e) => setPaperId(e.target.value)}
          style={{ padding: "6px 10px", borderRadius: 4, border: "1px solid #d1d5db", fontSize: 13 }}
        >
          <option value="">All papers</option>
          {papers.map((p) => (
            <option key={p.paper_id} value={p.paper_id}>
              {p.title} ({p.chunk_count} chunks)
            </option>
          ))}
        </select>

        <label style={{ fontSize: 13, color: "#374151", display: "flex", alignItems: "center", gap: 6 }}>
          Top&nbsp;
          <input
            type="range"
            min={1}
            max={20}
            value={topN}
            onChange={(e) => setTopN(Number(e.target.value))}
            style={{ width: 80 }}
          />
          &nbsp;{topN}
        </label>
      </div>
    </form>
  );
}
