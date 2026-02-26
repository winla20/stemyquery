interface Props {
  level: "high" | "med" | "low";
}

const styles: Record<string, React.CSSProperties> = {
  high: { background: "#d1fae5", color: "#065f46", border: "1px solid #6ee7b7" },
  med:  { background: "#fef3c7", color: "#92400e", border: "1px solid #fcd34d" },
  low:  { background: "#f3f4f6", color: "#374151", border: "1px solid #d1d5db" },
};

export function ConfidenceBadge({ level }: Props) {
  return (
    <span style={{
      ...styles[level],
      padding: "2px 8px",
      borderRadius: 4,
      fontSize: 12,
      fontWeight: 600,
      textTransform: "uppercase",
    }}>
      {level}
    </span>
  );
}
