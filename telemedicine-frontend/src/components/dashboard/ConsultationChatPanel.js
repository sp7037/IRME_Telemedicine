import React, { useCallback, useEffect, useRef, useState } from "react";
import { downloadPrescriptionPdf, getChatHistory, sendMessage } from "../../api/users";

const CLOSED_STATUSES = new Set(["COMPLETED", "CANCELED", "REJECTED", "REJECTED_BY_PATIENT"]);

const prescriptionMessageText = (message) =>
  String(message || "")
    .replace(/^PRESCRIPTION_RX:\d+:\s*/, "")
    .replace(/^PRESCRIPTION:\s*/, "");

const ConsultationChatPanel = ({ consultationId, status, pollMs = 6000, autoFocusInput = false, focusToken = 0 }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sendBusy, setSendBusy] = useState(false);
  const [error, setError] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const threadRef = useRef(null);
  const fileInputRef = useRef(null);
  const textInputRef = useRef(null);

  const canSend = Boolean(consultationId && status && !CLOSED_STATUSES.has(status));

  const load = useCallback(async () => {
    if (!consultationId) return;
    try {
      const hist = await getChatHistory(consultationId);
      setMessages(Array.isArray(hist) ? hist : []);
      setError("");
    } catch (e) {
      setError(e?.message || "Could not load chat.");
    } finally {
      setLoading(false);
    }
  }, [consultationId]);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  useEffect(() => {
    if (!consultationId || pollMs <= 0) return undefined;
    const id = setInterval(() => load(), pollMs);
    return () => clearInterval(id);
  }, [consultationId, pollMs, load]);

  useEffect(() => {
    const el = threadRef.current;
    if (!el) return;
    requestAnimationFrame(() => {
      el.scrollTop = el.scrollHeight;
    });
  }, [messages]);

  useEffect(() => {
    if (!autoFocusInput && !focusToken) return;
    const el = textInputRef.current;
    if (!el) return;
    requestAnimationFrame(() => {
      el.focus();
    });
  }, [autoFocusInput, focusToken, consultationId, canSend]);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!canSend || sendBusy) return;
    const t = text.trim();
    if (!t && !file) return;
    setSendBusy(true);
    setError("");
    try {
      await sendMessage(consultationId, t || "", file || null);
      setText("");
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await load();
    } catch (err) {
      setError(err?.message || "Send failed.");
    } finally {
      setSendBusy(false);
    }
  };

  return (
    <div style={styles.wrap}>
      <div style={styles.headingRow}>
        <h4 style={styles.heading}>Consultation chat</h4>
        <span style={canSend ? styles.livePill : styles.closedPill}>{canSend ? "Open" : "Closed"}</span>
      </div>
      {loading && messages.length === 0 ? <p style={styles.muted}>Loading messages...</p> : null}
      {error ? <p role="alert" style={styles.err}>{error}</p> : null}
      <div ref={threadRef} style={styles.thread} aria-live="polite">
        {messages.length === 0 && !loading ? <p style={styles.muted}>No messages yet. Say hello below.</p> : null}
        {messages.map((m) => {
          const isRx = m.is_prescription || (m.message && /^PRESCRIPTION(_RX)?:/.test(String(m.message)));
          const rx = m.prescription_data;
          return (
            <div key={m.id} style={isRx ? styles.systemBubble : styles.bubble}>
              <div style={styles.meta}>
                <strong>{m.sender_name || m.sender || "Participant"}</strong>
                <span style={styles.ts}>{m.timestamp ? new Date(m.timestamp).toLocaleString() : ""}</span>
              </div>
              {isRx ? (
                <div style={styles.rxBubbleBody}>
                  <div>
                    <div style={styles.msgMuted}>{prescriptionMessageText(m.message)}</div>
                    {rx?.id ? (
                      <div style={styles.rxMeta}>
                        RX-{rx.id}
                        {rx.updated_at ? ` - ${new Date(rx.updated_at).toLocaleString()}` : ""}
                      </div>
                    ) : null}
                  </div>
                  {rx?.id ? (
                    <button type="button" style={styles.rxDownloadBtn} onClick={() => downloadPrescriptionPdf(rx.id)}>
                      Download PDF
                    </button>
                  ) : null}
                </div>
              ) : m.message ? (
                <div style={styles.msg}>{m.message}</div>
              ) : null}
              {m.attachment_url ? (
                <a href={m.attachment_url} target="_blank" rel="noopener noreferrer" style={styles.link}>
                  Open attachment
                </a>
              ) : null}
            </div>
          );
        })}
      </div>
      {canSend ? (
        <form onSubmit={onSubmit} style={styles.form}>
          <textarea
            ref={textInputRef}
            style={styles.ta}
            rows={3}
            placeholder="Type a message..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={sendBusy}
          />
          <div style={styles.row}>
            <label style={styles.fileLabel}>
              <span style={styles.fileBtn}>Attach file</span>
              <input
                ref={fileInputRef}
                type="file"
                accept=".jpg,.jpeg,.png,.gif,.webp,.pdf"
                disabled={sendBusy}
                style={styles.fileInput}
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              {file ? <span style={styles.fileName}>{file.name}</span> : null}
            </label>
            <button type="submit" disabled={sendBusy || (!text.trim() && !file)} style={styles.btn}>
              {sendBusy ? "Sending..." : "Send"}
            </button>
          </div>
          <p style={styles.hint}>Images or PDF, up to 10 MB. Messages are recorded in the consultation timeline.</p>
        </form>
      ) : (
        <p style={styles.muted}>Messaging is closed for this consultation.</p>
      )}
    </div>
  );
};

const styles = {
  wrap: {
    marginBottom: 16,
    background: "#fbfdff",
    border: "1px solid #d7e5f5",
    borderRadius: 12,
    padding: 12,
  },
  headingRow: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, marginBottom: 10 },
  heading: { margin: 0, color: "#123a6f", fontSize: "1rem" },
  livePill: { background: "#e8f7ef", color: "#17623c", borderRadius: 999, padding: "3px 9px", fontSize: 11, fontWeight: 800 },
  closedPill: { background: "#eef2f6", color: "#53657a", borderRadius: 999, padding: "3px 9px", fontSize: 11, fontWeight: 800 },
  muted: { color: "#4c6480", fontSize: 13, margin: "6px 0" },
  err: { color: "#8a1f1f", fontSize: 13, margin: "0 0 8px" },
  thread: {
    maxHeight: "min(420px, 44vh)",
    overflowY: "auto",
    border: "1px solid #e2ecf7",
    borderRadius: 10,
    padding: 12,
    background: "linear-gradient(180deg,#ffffff 0%,#f7fbff 100%)",
    marginBottom: 12,
  },
  bubble: {
    border: "1px solid #e2ecf7",
    borderRadius: 10,
    padding: 10,
    marginBottom: 10,
    background: "#fff",
    boxShadow: "0 4px 12px rgba(16,36,62,0.04)",
  },
  systemBubble: {
    border: "1px solid #b8dbc7",
    borderRadius: 10,
    padding: 10,
    marginBottom: 10,
    background: "#effaf3",
  },
  meta: {
    display: "flex",
    justifyContent: "space-between",
    gap: 8,
    flexWrap: "wrap",
    fontSize: 12,
    color: "#4c6480",
    marginBottom: 4,
  },
  ts: { fontWeight: 500 },
  msg: { color: "#10243e", fontSize: 14, whiteSpace: "pre-wrap", wordBreak: "break-word" },
  msgMuted: { color: "#17623c", fontSize: 13, fontWeight: 700 },
  rxBubbleBody: { display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" },
  rxMeta: { color: "#2c6846", fontSize: 12, marginTop: 4 },
  rxDownloadBtn: {
    background: "#1762bf",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    padding: "7px 11px",
    fontWeight: 700,
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  link: { fontSize: 13, color: "#1762bf", fontWeight: 600 },
  form: { display: "flex", flexDirection: "column", gap: 8 },
  ta: {
    width: "100%",
    boxSizing: "border-box",
    borderRadius: 8,
    border: "1px solid #c6d7eb",
    padding: "8px 10px",
    fontFamily: "inherit",
    fontSize: 14,
    resize: "vertical",
    minHeight: 72,
  },
  row: { display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10, justifyContent: "space-between" },
  fileLabel: { display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", cursor: "pointer", position: "relative" },
  fileBtn: {
    display: "inline-block",
    background: "#edf4fd",
    color: "#174577",
    border: "1px solid #8ab0dc",
    borderRadius: 8,
    padding: "6px 12px",
    fontWeight: 700,
    fontSize: 13,
  },
  fileInput: { position: "absolute", width: 1, height: 1, opacity: 0, overflow: "hidden" },
  fileName: { fontSize: 12, color: "#304f72", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis" },
  btn: {
    background: "#1762bf",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    padding: "8px 16px",
    fontWeight: 700,
    cursor: "pointer",
  },
  hint: { margin: 0, fontSize: 11, color: "#6b7f96" },
};

export default ConsultationChatPanel;
