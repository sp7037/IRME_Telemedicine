import React, { useEffect, useMemo, useState } from "react";
import Header from "../../../components/Header";
import Footer from "../../../components/Footer";
import Sidebar from "../../../components/Sidebar";
import StatusBadge from "../../../components/dashboard/StatusBadge";
import ConsultationDetailModal from "../../../components/dashboard/ConsultationDetailModal";
import {
  getUserProfile,
  getPatientConsultationHistory,
  getDoctorPendingRequests,
  getDoctorQueuedConsultations,
  getActiveConsultation,
  doctorRespondToRequest,
  startConsultation,
  completeConsultation,
  getConsultationEvents,
  getDoctorEarningsSummary,
} from "../../../api/users";

const DoctorDashboard = () => {
  const [all, setAll] = useState([]);
  const [pending, setPending] = useState([]);
  const [queued, setQueued] = useState([]);
  const [active, setActive] = useState(null);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState(null);
  const [events, setEvents] = useState([]);
  const [postponeDate, setPostponeDate] = useState("");
  const [earnings, setEarnings] = useState(null);

  const refresh = async () => {
    const [profile, history, pend, queue, current] = await Promise.all([
      getUserProfile(),
      getPatientConsultationHistory(),
      getDoctorPendingRequests(),
      getDoctorQueuedConsultations(),
      getActiveConsultation(),
    ]);
    const earningData = await getDoctorEarningsSummary();
    void profile.user;
    setAll(Array.isArray(history) ? history : []);
    setPending(Array.isArray(pend) ? pend : []);
    setQueued(Array.isArray(queue) ? queue : []);
    setActive(current || null);
    setEarnings(earningData);
  };

  useEffect(() => {
    refresh().catch(() => {});
    const t = setInterval(() => refresh().catch(() => {}), 8000);
    return () => clearInterval(t);
  }, []);

  const completed = useMemo(
    () => all.filter((c) => c.status === "COMPLETED" || c.is_completed).slice(0, 8),
    [all]
  );
  const postponed = useMemo(() => all.filter((c) => c.status === "POSTPONED"), [all]);

  const openDetail = async (consultation) => {
    setSelected(consultation);
    const e = await getConsultationEvents(consultation.id);
    setEvents(Array.isArray(e) ? e : []);
  };

  const handleAction = async (consultationId, status) => {
    setBusy(true);
    try {
      await doctorRespondToRequest(consultationId, status, status === "POSTPONED" ? new Date(postponeDate).toISOString() : null);
      setPostponeDate("");
      await refresh();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={styles.page}>
      <Header />
      <Sidebar role="doctor" />
      <main style={styles.main}>
        <h2 style={styles.title}>Doctor Operations Dashboard</h2>
        <p style={styles.subtitle}>Clear workflow from requests to completion.</p>

        <div style={styles.cards}>
          <Metric label="Active" value={active ? 1 : 0} />
          <Metric label="Queued" value={queued.length} />
          <Metric label="Pending" value={pending.filter((x) => x.status === "PENDING").length} />
          <Metric label="Completed" value={completed.length} />
          <Metric label="Total Earnings" value={earnings ? `Rs ${earnings.total_earnings}` : "Rs 0.00"} />
        </div>

        <section style={styles.section}>
          <h3 style={styles.sectionTitle}>Active Consultation</h3>
          {!active ? <Empty text="No active consultation. Accept a pending request or start from queue." /> : (
            <RowCard
              consultation={active}
              actions={
                <div style={styles.rowActions}>
                  <button style={styles.primaryBtn} onClick={() => openDetail(active)}>Open Consultation</button>
                  <button style={styles.secondaryBtn} onClick={async () => { await completeConsultation(active.id); await refresh(); }}>Mark Completed</button>
                </div>
              }
            />
          )}
        </section>

        <section style={styles.section}>
          <h3 style={styles.sectionTitle}>Queue</h3>
          {queued.length === 0 ? <Empty text="Queue is empty." /> : queued.map((q) => (
            <RowCard
              key={q.id}
              consultation={q}
              label={`Queue #${q.queue_number || "-"}`}
              actions={
                <div style={styles.rowActions}>
                  <button style={styles.primaryBtn} onClick={async () => { await startConsultation(q.id); await refresh(); }}>Start</button>
                  <button style={styles.secondaryBtn} onClick={() => openDetail(q)}>Preview</button>
                </div>
              }
            />
          ))}
        </section>

        <section style={styles.section}>
          <h3 style={styles.sectionTitle}>Pending Requests</h3>
          {pending.length === 0 ? <Empty text="No pending requests." /> : pending.map((p) => (
            <div key={p.id} style={styles.card}>
              <RowCard consultation={p} />
              <div style={styles.rowActions}>
                <button style={styles.primaryBtn} disabled={busy} onClick={() => handleAction(p.id, "ACCEPTED")}>Accept</button>
                <button style={styles.secondaryBtn} disabled={busy} onClick={() => handleAction(p.id, "REJECTED")}>Reject</button>
                <input type="datetime-local" value={postponeDate} onChange={(e) => setPostponeDate(e.target.value)} style={styles.input} />
                <button style={styles.warnBtn} disabled={busy || !postponeDate} onClick={() => handleAction(p.id, "POSTPONED")}>Postpone</button>
              </div>
            </div>
          ))}
        </section>

        <section style={styles.section}>
          <h3 style={styles.sectionTitle}>Postponed Consultations</h3>
          {postponed.length === 0 ? <Empty text="No postponed consultations." /> : postponed.map((p) => <RowCard key={p.id} consultation={p} />)}
        </section>

        <section style={styles.section}>
          <h3 style={styles.sectionTitle}>Completed (Recent)</h3>
          {completed.length === 0 ? <Empty text="No completed consultations yet." /> : completed.map((c) => (
            <RowCard key={c.id} consultation={c} actions={<button style={styles.secondaryBtn} onClick={() => openDetail(c)}>Open History</button>} />
          ))}
        </section>

        <section style={styles.section}>
          <h3 style={styles.sectionTitle}>Earning Records (Recent)</h3>
          {!earnings || !earnings.recent_earnings || earnings.recent_earnings.length === 0 ? (
            <Empty text="No earnings recorded yet." />
          ) : (
            earnings.recent_earnings.slice(0, 8).map((e) => (
              <div key={e.consultation_id} style={styles.rowCard}>
                <div>
                  <div style={styles.rowTitle}>Consultation #{e.consultation_id}</div>
                  <div style={styles.rowMeta}>
                    {e.source_type} · {e.billing_type} · {e.status}
                  </div>
                </div>
                <strong style={{ color: "#123a6f" }}>Rs {e.earning_amount}</strong>
              </div>
            ))
          )}
        </section>
      </main>
      <Footer />
      <ConsultationDetailModal consultation={selected} events={events} onClose={() => setSelected(null)} />
    </div>
  );
};

const Metric = ({ label, value }) => (
  <article style={styles.metric}>
    <div style={styles.metricLabel}>{label}</div>
    <div style={styles.metricValue}>{value}</div>
  </article>
);

const RowCard = ({ consultation, label, actions }) => (
  <article style={styles.rowCard}>
    <div>
      <div style={styles.rowTitle}>
        Dr/Patient: {consultation.patient_name || "-"} · {consultation.doctor_name || "-"}
        {label ? <span style={styles.queueTag}>{label}</span> : null}
      </div>
      <div style={styles.rowMeta}>
        {consultation.consultation_type} · {consultation.formatted_time}
        {consultation.tmc_name ? ` · TMC: ${consultation.tmc_name}` : ""}
      </div>
      <div style={{ marginTop: 6 }}><StatusBadge status={consultation.status} /></div>
    </div>
    {actions}
  </article>
);

const Empty = ({ text }) => <p style={{ color: "#4c6480", margin: "4px 0" }}>{text}</p>;

const styles = {
  page: { minHeight: "100vh", backgroundColor: "#f5f8fc", color: "#10243e", fontFamily: "Segoe UI, Arial, sans-serif" },
  main: { marginLeft: "280px", padding: "84px 24px 24px", maxWidth: 1200 },
  title: { margin: 0, color: "#123a6f" },
  subtitle: { color: "#4c6480", marginTop: 8 },
  cards: { display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(170px,1fr))", gap: 12, marginTop: 16 },
  metric: { background: "#fff", border: "1px solid #d7e5f5", borderRadius: 12, padding: 14, boxShadow: "0 8px 20px rgba(0,0,0,0.08)" },
  metricLabel: { color: "#4c6480", fontSize: 12, fontWeight: 700 },
  metricValue: { color: "#113864", fontSize: 28, fontWeight: 800 },
  section: { marginTop: 14, background: "#fff", borderRadius: 14, padding: 16, boxShadow: "0 8px 20px rgba(0,0,0,0.08)" },
  sectionTitle: { margin: 0, marginBottom: 10, color: "#123a6f" },
  card: { border: "1px solid #d7e5f5", borderRadius: 12, padding: 10, marginBottom: 10, background: "#fbfdff" },
  rowCard: { border: "1px solid #d7e5f5", borderRadius: 12, padding: 12, background: "#fbfdff", marginBottom: 10, display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" },
  rowTitle: { fontWeight: 700, color: "#113864", fontSize: 14 },
  rowMeta: { color: "#4c6480", fontSize: 13, marginTop: 4 },
  rowActions: { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" },
  queueTag: { marginLeft: 8, padding: "2px 8px", borderRadius: 999, background: "#efe9ff", color: "#4a2f9b", fontSize: 12 },
  primaryBtn: { background: "#1762bf", color: "#fff", border: "none", borderRadius: 8, padding: "8px 12px", fontWeight: 700, cursor: "pointer" },
  secondaryBtn: { background: "#edf4fd", color: "#174577", border: "1px solid #8ab0dc", borderRadius: 8, padding: "8px 12px", fontWeight: 700, cursor: "pointer" },
  warnBtn: { background: "#ffeedd", color: "#8a4b10", border: "1px solid #ffca9f", borderRadius: 8, padding: "8px 12px", fontWeight: 700, cursor: "pointer" },
  input: { height: 36, borderRadius: 8, border: "1px solid #c6d7eb", padding: "0 10px" },
};

export default DoctorDashboard;
