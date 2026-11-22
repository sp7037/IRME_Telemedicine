import React from "react";

const STATUS_COLORS = {
  PENDING: { bg: "#fff4cc", fg: "#8a6d00" },
  ACCEPTED: { bg: "#e4efff", fg: "#1f4f8f" },
  QUEUED: { bg: "#efe9ff", fg: "#4a2f9b" },
  IN_PROGRESS: { bg: "#e3f8ea", fg: "#1b6a3a" },
  COMPLETED: { bg: "#eceff4", fg: "#3f4b5e" },
  REJECTED: { bg: "#fde8e8", fg: "#9d1d1d" },
  REJECTED_BY_PATIENT: { bg: "#fde8e8", fg: "#9d1d1d" },
  POSTPONED: { bg: "#ffeedd", fg: "#8a4b10" },
  CANCELED: { bg: "#fde8e8", fg: "#9d1d1d" },
};

const StatusBadge = ({ status }) => {
  const safe = (status || "").toUpperCase();
  const color = STATUS_COLORS[safe] || { bg: "#edf4fd", fg: "#174577" };
  return (
    <span
      style={{
        display: "inline-block",
        padding: "4px 10px",
        borderRadius: "999px",
        fontSize: 12,
        fontWeight: 700,
        backgroundColor: color.bg,
        color: color.fg,
      }}
    >
      {safe || "UNKNOWN"}
    </span>
  );
};

export default StatusBadge;
