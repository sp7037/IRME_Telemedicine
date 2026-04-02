import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import Header from "../../../components/Header";
import Footer from "../../../components/Footer";
import Sidebar from "../../../components/Sidebar";
import StatusBadge from "../../../components/dashboard/StatusBadge";
import ConsultationDetailModal from "../../../components/dashboard/ConsultationDetailModal";
import {
  getUserProfile,
  getPatientConsultationHistory,
  getActiveConsultation,
  patientRespondToConsultation,
  getConsultationEvents,
  getPrescription,
  downloadPrescriptionPdf,
  getPatientWalletSummary,
  topupPatientWallet,
} from "../../../api/users";
import { API_BASE_URL } from "../../../api/config";

const PatientDashboardRefined = () => {
  const [doctors, setDoctors] = useState([]);
  const [consultations, setConsultations] = useState([]);
  const [active, setActive] = useState(null);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState(null);
  const [events, setEvents] = useState([]);
  const [prescriptionMap, setPrescriptionMap] = useState({});
  const [search, setSearch] = useState("");
  const [wallet, setWallet] = useState(null);

  const refresh = async () => {
    await getUserProfile();
    const [docs, history, current] = await Promise.all([
      axios.get(`${API_BASE_URL}/consultations/available-doctors/`),
      getPatientConsultationHistory(),
      getActiveConsultation(),
    ]);
    const walletData = await getPatientWalletSummary();
    setDoctors(Array.isArray(docs.data) ? docs.data : []);
    setConsultations(Array.isArray(history) ? history : []);
    setActive(current || null);
    setWallet(walletData);
  };

  useEffect(() => {
    refresh().catch(() => {});
    const t = setInterval(() => refresh().catch(() => {}), 8000);
    return () => clearInterval(t);
  }, []);

  const grouped = useMemo(
    () => ({
      QUEUED: consultations.filter((c) => c.status === "QUEUED"),
      PENDING: consultations.filter((c) => c.status === "PENDING"),
      POSTPONED: consultations.filter((c) => c.status === "POSTPONED"),
      COMPLETED: consultations.filter((c) => c.status === "COMPLETED" || c.is_completed),
    }),
    [consultations]
  );

  const filteredDoctors = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return doctors;
    return doctors.filter((d) =>
      `${d.first_name || ""} ${d.last_name || ""} ${d.specialty || ""}`.toLowerCase().includes(q)
    );
  }, [search, doctors]);

  const requestConsultation = async (doctorId) => {
    setBusy(true);
    try {
      await axios.post(
        `${API_BASE_URL}/consultations/book-consultation/`,
        { doctor_id: doctorId, consultation_type: "DIRECT" },
        { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
      );
      await refresh();
    } finally {
      setBusy(false);
    }
  };

  const openDetails = async (consultation) => {
    setSelected(consultation);
    const [timeline, rx] = await Promise.all([
      getConsultationEvents(consultation.id),
      getPrescription(consultation.id),
    ]);
    setEvents(Array.isArray(timeline) ? timeline : []);
    setPrescriptionMap((prev) => ({ ...prev, [consultation.id]: rx }));
  };

  return (
    <div style={styles.page}>
      <Header />
      <Sidebar role="patient" />
      <main style={styles.main}>
        <h2 style={styles.title}>Patient Dashboard</h2>
        <section style={styles.section}>
          <h3 style={styles.sectionTitle}>Wallet & Spending</h3>
          <div style={styles.rowActions}>
            <strong style={{ color: "#123a6f" }}>Balance: Rs {wallet?.balance || "0.00"}</strong>
            <span style={styles.rowMeta}>Credited: Rs {wallet?.total_credited || "0.00"}</span>
            <span style={styles.rowMeta}>Debited: Rs {wallet?.total_debited || "0.00"}</span>
            <button
              style={styles.secondaryBtn}
              onClick={async () => {
                await topupPatientWallet("500.00");
                await refresh();
              }}
            >
              Add Rs 500
            </button>
          </div>
          <div style={{ marginTop: 10 }}>
            {(wallet?.recent_entries || []).slice(0, 5).map((entry) => (
              <div key={entry.id} style={styles.card}>
                <div>
                  <div style={styles.rowTitle}>{entry.entry_type}</div>
                  <div style={styles.rowMeta}>{entry.description || "Wallet entry"}</div>
                </div>
                <strong style={{ color: "#123a6f" }}>Rs {entry.amount}</strong>
              </div>
            ))}
          </div>
        </section>
        <section style={styles.section}>
          <h3 style={styles.sectionTitle}>Active Consultation</h3>
          {!active ? <p style={styles.muted}>No active consultation.</p> : (
            <ConsultationCard consultation={active} helper="Consultation is live." actions={<button style={styles.primaryBtn} onClick={() => openDetails(active)}>Open Chat / Details</button>} />
          )}
        </section>
        <Section title="In Queue">
          {grouped.QUEUED.map((c) => <ConsultationCard key={c.id} consultation={c} helper={`Doctor accepted. Queue #${c.queue_number || "-"}.`} actions={<button style={styles.secondaryBtn} onClick={() => openDetails(c)}>Timeline</button>} />)}
          {grouped.QUEUED.length === 0 ? <p style={styles.muted}>No queued consultations.</p> : null}
        </Section>
        <Section title="Pending">
          {grouped.PENDING.map((c) => <ConsultationCard key={c.id} consultation={c} helper="Doctor review is pending." />)}
          {grouped.PENDING.length === 0 ? <p style={styles.muted}>No pending consultations.</p> : null}
        </Section>
        <Section title="Postponed">
          {grouped.POSTPONED.map((c) => (
            <ConsultationCard
              key={c.id}
              consultation={c}
              helper={`Doctor proposed: ${c.formatted_suggested_time || "updated time"}`}
              actions={
                <div style={styles.rowActions}>
                  <button style={styles.primaryBtn} onClick={async () => { await patientRespondToConsultation(c.id, "approve_postponed"); await refresh(); }}>Accept</button>
                  <button style={styles.warnBtn} onClick={async () => { await patientRespondToConsultation(c.id, "reject_postponed"); await refresh(); }}>Reject</button>
                </div>
              }
            />
          ))}
          {grouped.POSTPONED.length === 0 ? <p style={styles.muted}>No postponed consultations.</p> : null}
        </Section>
        <Section title="Completed">
          {grouped.COMPLETED.map((c) => <ConsultationCard key={c.id} consultation={c} actions={<button style={styles.secondaryBtn} onClick={() => openDetails(c)}>Open History</button>} />)}
          {grouped.COMPLETED.length === 0 ? <p style={styles.muted}>No completed consultations.</p> : null}
        </Section>
        <Section title="Find Doctors">
          <input style={styles.input} value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name or specialty" />
          <div style={{ marginTop: 10 }}>
            {filteredDoctors.slice(0, 12).map((d) => (
              <div key={d.id} style={styles.doctorRow}>
                <div>
                  <div style={styles.rowTitle}>Dr. {d.first_name} {d.last_name}</div>
                  <div style={styles.rowMeta}>{d.specialty || "General"}</div>
                </div>
                <button disabled={busy} style={styles.primaryBtn} onClick={() => requestConsultation(d.id)}>Consult Now</button>
              </div>
            ))}
          </div>
        </Section>
      </main>
      <Footer />
      <ConsultationDetailModal consultation={selected} events={events} onClose={() => setSelected(null)}>
        {selected && prescriptionMap[selected.id] ? (
          <div style={styles.sectionInset}>
            <h4 style={{ margin: 0, color: "#123a6f" }}>Your Prescription</h4>
            <button style={styles.primaryBtn} onClick={() => downloadPrescriptionPdf(prescriptionMap[selected.id].id)}>Download PDF</button>
          </div>
        ) : null}
      </ConsultationDetailModal>
    </div>
  );
};

const ConsultationCard = ({ consultation, helper, actions }) => (
  <article style={styles.card}>
    <div>
      <div style={styles.rowTitle}>Dr. {consultation.doctor_name}</div>
      <div style={styles.rowMeta}>{consultation.formatted_time} · {consultation.consultation_type}</div>
      <div style={{ marginTop: 6 }}><StatusBadge status={consultation.status} /></div>
      {helper ? <p style={styles.helper}>{helper}</p> : null}
    </div>
    {actions}
  </article>
);

const Section = ({ title, children }) => (
  <section style={styles.section}>
    <h3 style={styles.sectionTitle}>{title}</h3>
    {children}
  </section>
);

const styles = {
  page: { minHeight: "100vh", backgroundColor: "#f5f8fc", color: "#10243e", fontFamily: "Segoe UI, Arial, sans-serif" },
  main: { marginLeft: "280px", padding: "84px 24px 24px", maxWidth: 1200 },
  title: { margin: 0, color: "#123a6f" },
  muted: { color: "#4c6480", margin: 0 },
  section: { marginTop: 14, background: "#fff", borderRadius: 14, padding: 16, boxShadow: "0 8px 20px rgba(0,0,0,0.08)" },
  sectionInset: { marginBottom: 14, background: "#fbfdff", border: "1px solid #d7e5f5", borderRadius: 10, padding: 10 },
  sectionTitle: { margin: 0, marginBottom: 10, color: "#123a6f" },
  card: { border: "1px solid #d7e5f5", borderRadius: 12, padding: 12, background: "#fbfdff", marginBottom: 10, display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" },
  rowTitle: { fontWeight: 700, color: "#113864", fontSize: 14 },
  rowMeta: { color: "#4c6480", fontSize: 13, marginTop: 4 },
  helper: { color: "#244a75", fontSize: 13, marginTop: 8, marginBottom: 0 },
  rowActions: { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" },
  primaryBtn: { background: "#1762bf", color: "#fff", border: "none", borderRadius: 8, padding: "8px 12px", fontWeight: 700, cursor: "pointer" },
  secondaryBtn: { background: "#edf4fd", color: "#174577", border: "1px solid #8ab0dc", borderRadius: 8, padding: "8px 12px", fontWeight: 700, cursor: "pointer" },
  warnBtn: { background: "#ffeedd", color: "#8a4b10", border: "1px solid #ffca9f", borderRadius: 8, padding: "8px 12px", fontWeight: 700, cursor: "pointer" },
  input: { height: 40, borderRadius: 8, border: "1px solid #c6d7eb", padding: "0 10px", width: "100%" },
  doctorRow: { border: "1px solid #d7e5f5", borderRadius: 12, padding: 12, marginBottom: 8, background: "#fbfdff", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 },
};

export default PatientDashboardRefined;
