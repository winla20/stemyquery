import { useChunkContext } from "../hooks/useChunkContext";
import type { ChunkOut } from "../types";

interface Props {
  chunkId: string;
  onClose: () => void;
}

function ChunkBlock({ chunk, highlight }: { chunk: ChunkOut; highlight?: boolean }) {
  return (
    <div style={{
      padding: "12px 16px",
      marginBottom: 8,
      borderRadius: 6,
      background: highlight ? "#eff6ff" : "#f9fafb",
      border: highlight ? "2px solid #3b82f6" : "1px solid #e5e7eb",
      opacity: highlight ? 1 : 0.75,
    }}>
      <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 4 }}>
        {chunk.section_path.join(" → ")} &middot; p.{chunk.page_start}
      </div>
      <div style={{ fontSize: 13, whiteSpace: "pre-wrap", color: "#1f2937" }}>
        {chunk.text}
      </div>
    </div>
  );
}

export function ContextViewer({ chunkId, onClose }: Props) {
  const { context, isLoading, error } = useChunkContext(chunkId);

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      background: "rgba(0,0,0,0.4)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 1000,
    }}>
      <div style={{
        background: "#fff",
        borderRadius: 10,
        padding: 24,
        width: "min(700px, 90vw)",
        maxHeight: "85vh",
        overflowY: "auto",
        boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
          <strong style={{ fontSize: 16 }}>Section Context</strong>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 18 }}>
            &times;
          </button>
        </div>

        {isLoading && <p style={{ color: "#6b7280" }}>Loading...</p>}
        {error && <p style={{ color: "#dc2626" }}>{error}</p>}

        {context && (
          <>
            {context.prev && <ChunkBlock chunk={context.prev} />}
            <ChunkBlock chunk={context.current} highlight />
            {context.next && <ChunkBlock chunk={context.next} />}
          </>
        )}
      </div>
    </div>
  );
}
