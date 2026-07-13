type Status = "pending" | "cloning" | "indexing" | "ready" | "error";

const colorMap: Record<Status, string> = {
  pending: "#6b7280",
  cloning: "#3b82f6",
  indexing: "#f59e0b",
  ready: "#10b981",
  error: "#ef4444",
};

export default function StatusBadge({ status }: { status: string }) {
  const color = colorMap[status as Status] ?? "#6b7280";
  return (
    <span
      style={{
        backgroundColor: color,
        color: "#fff",
        padding: "2px 10px",
        borderRadius: "9999px",
        fontSize: "0.75rem",
        fontWeight: 600,
        textTransform: "capitalize",
      }}
    >
      {status}
    </span>
  );
}
