import type { Severity } from "../types";

const colorMap: Record<Severity, string> = {
  critical: "#7f1d1d",
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#3b82f6",
  info: "#6b7280",
};

export default function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      style={{
        backgroundColor: colorMap[severity],
        color: "#fff",
        padding: "2px 10px",
        borderRadius: "9999px",
        fontSize: "0.75rem",
        fontWeight: 600,
        textTransform: "uppercase",
      }}
    >
      {severity}
    </span>
  );
}
