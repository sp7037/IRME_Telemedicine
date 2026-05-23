import React from "react";

const ICONS = {
  REQUESTED: "📝",
  ACCEPTED: "✅",
  QUEUED: "📋",
  STARTED: "🟢",
  POSTPONED: "📅",
  POSTPONE_ACCEPTED: "👍",
  POSTPONE_REJECTED: "👎",
  REJECTED: "⛔",
  CANCELED: "❌",
  COMPLETED: "🏁",
  PRESCRIPTION_CREATED: "💊",
  PRESCRIPTION_UPDATED: "🧾",
};

const ConsultationTimeline = ({ events }) => {
  if (!events || events.length === 0) {
    return <p style={{ color: "#4c6480", margin: 0 }}>No timeline events yet.</p>;
  }
  return (
    <div style={{ display: "grid", gap: 10 }}>
      {events.map((event) => {
        const title = event.display_label || event.event_type?.replaceAll("_", " ") || "Event";
        const meta = event.display_time || (event.created_at ? new Date(event.created_at).toLocaleString() : "");
        const actor = event.actor_display || event.actor_email || "";
        const summary = event.summary || "";
        const rowStyle = {
          ...styles.row,
          ...(event.highlight ? styles.rowHighlight : {}),
        };
        return (
          <div key={event.id} style={rowStyle}>
            <div style={styles.icon}>{ICONS[event.event_type] || "•"}</div>
            <div>
              <div style={styles.title}>{title}</div>
              <div style={styles.meta}>
                {meta}
                {actor ? ` · ${actor}` : ""}
              </div>
              {summary ? <div style={styles.summary}>{summary}</div> : null}
              {event.note ? <div style={styles.note}>{event.note}</div> : null}
            </div>
          </div>
        );
      })}
    </div>
  );
};

const styles = {
  row: {
    display: "grid",
    gridTemplateColumns: "34px 1fr",
    gap: 10,
    background: "#fbfdff",
    border: "1px solid #d7e5f5",
    borderRadius: 10,
    padding: 10,
  },
  rowHighlight: {
    borderColor: "#8ab0dc",
    background: "#f0f6fd",
  },
  icon: {
    width: 28,
    height: 28,
    borderRadius: 999,
    background: "#edf4fd",
    display: "grid",
    placeItems: "center",
    fontSize: 14,
  },
  title: { fontWeight: 700, color: "#113864", fontSize: 13 },
  meta: { color: "#4c6480", fontSize: 12, marginTop: 2 },
  summary: { color: "#244a75", fontSize: 13, marginTop: 6, lineHeight: 1.35 },
  note: { color: "#244a75", fontSize: 13, marginTop: 4 },
};

export default ConsultationTimeline;
