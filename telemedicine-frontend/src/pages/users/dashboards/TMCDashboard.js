import React, { useEffect, useState } from "react";
import Header from "../../../components/Header";
import Footer from "../../../components/Footer";
import Sidebar from "../../../components/Sidebar";
import {
  getTMCSummary,
  getTMCConsultations,
  getTMCPatients,
  createTMCConsultation,
  getConsultationEvents,
  getTMCFinanceSummary,
} from "../../../api/users";
import axios from "axios";
import { API_BASE_URL } from "../../../api/config";

const TMCDashboard = () => {
  const [summary, setSummary] = useState(null);
  const [consultations, setConsultations] = useState([]);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState([]);
  const [finance, setFinance] = useState(null);
  const [selectedConsultation, setSelectedConsultation] = useState(null);
  const [form, setForm] = useState({
    patient_id: "",
    doctor_id: "",
    scheduled_time: "",
  });

  const loadAll = async () => {
    const [s, c, p] = await Promise.all([
      getTMCSummary(),
      getTMCConsultations(),
      getTMCPatients(),
    ]);
    const fin = await getTMCFinanceSummary();
    setSummary(s);
    setConsultations(Array.isArray(c) ? c : []);
    setPatients(Array.isArray(p) ? p : []);
    const d = await axios.get(`${API_BASE_URL}/consultations/available-doctors/`);
    setDoctors(Array.isArray(d.data) ? d.data : []);
    setFinance(fin);
  };

  useEffect(() => {
    loadAll().catch(() => {});
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createTMCConsultation(form);
      setForm({ patient_id: "", doctor_id: "", scheduled_time: "" });
      await loadAll();
      alert("Consultation initiated successfully.");
    } catch (err) {
      alert(err?.response?.data?.error || err.message || "Failed to initiate consultation.");
    } finally {
      setLoading(false);
    }
  };

  const openTimeline = async (consultation) => {
    setSelectedConsultation(consultation);
    const items = await getConsultationEvents(consultation.id);
    setEvents(Array.isArray(items) ? items : []);
  };

  return (
    <div style={styles.page}>
      <Header />
      <Sidebar role="tmc" />
      <main style={styles.main}>
        <h2 style={styles.title}>TMC Operations Dashboard</h2>
        <p style={styles.subtitle}>Initiate and monitor TMC-routed consultations.</p>

        {summary && (
          <div style={styles.cards}>
            <Card label="Total" value={summary.total} />
            <Card label="Active" value={summary.in_progress} />
            <Card label="Queued" value={summary.queued} />
            <Card label="Completed" value={summary.completed} />
            <Card label="Free Used" value={`${summary.free_used}/${summary.free_quota}`} />
            <Card label="TMC Charged" value={`Rs ${finance?.total_charged || "0.00"}`} />
          </div>
        )}

        <section style={styles.section}>
          <h3 style={styles.sectionTitle}>Initiate Consultation</h3>
          <form onSubmit={submit} style={styles.form}>
            <select
              value={form.patient_id}
              onChange={(e) => setForm({ ...form, patient_id: e.target.value })}
              required
              style={styles.input}
            >
              <option value="">Select patient</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>{p.name} ({p.email})</option>
              ))}
            </select>
            <select
              value={form.doctor_id}
              onChange={(e) => setForm({ ...form, doctor_id: e.target.value })}
              required
              style={styles.input}
            >
              <option value="">Select doctor</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>Dr. {d.first_name} {d.last_name} - {d.specialty || "General"}</option>
              ))}
            </select>
            <input
              type="datetime-local"
              value={form.scheduled_time}
              onChange={(e) => setForm({ ...form, scheduled_time: e.target.value })}
              style={styles.input}
            />
            <button type="submit" disabled={loading} style={styles.primaryButton}>
              {loading ? "Creating..." : "Create TMC Consultation"}
            </button>
          </form>
        </section>

        <section style={styles.section}>
          <h3 style={styles.sectionTitle}>Consultation Tracking</h3>
          <div style={styles.tableWrap}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th>ID</th><th>Patient</th><th>Doctor</th><th>Status</th><th>Type</th><th>Free/Paid</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {consultations.map((c) => (
                  <tr key={c.id}>
                    <td>{c.id}</td>
                    <td>{c.patient_name}</td>
                    <td>{c.doctor_name}</td>
                    <td><span style={styles.badge}>{c.status}</span></td>
                    <td>{c.consultation_type}</td>
                    <td>{c.is_free ? "Free" : "Paid"}</td>
                    <td><button onClick={() => openTimeline(c)} style={styles.secondaryButton}>Timeline</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {selectedConsultation && (
          <section style={styles.section}>
            <h3 style={styles.sectionTitle}>Timeline - Consultation #{selectedConsultation.id}</h3>
            {events.length === 0 ? (
              <p style={styles.subtitle}>No events yet.</p>
            ) : (
              <ul style={styles.timeline}>
                {events.map((e) => (
                  <li key={e.id} style={styles.timelineItem}>
                    <strong>{e.event_type}</strong> - {new Date(e.created_at).toLocaleString()}
                    {e.note ? <div>{e.note}</div> : null}
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        {finance && (
          <section style={styles.section}>
            <h3 style={styles.sectionTitle}>Recent Finance Entries</h3>
            {(finance.recent_entries || []).slice(0, 8).map((entry) => (
              <div key={entry.id} style={styles.timelineItem}>
                <strong>{entry.entry_type}</strong> - Rs {entry.amount}
                <div style={{ color: "#4c6480" }}>{entry.description || "TMC finance entry"}</div>
              </div>
            ))}
          </section>
        )}
      </main>
      <Footer />
    </div>
  );
};

const Card = ({ label, value }) => (
  <article style={styles.card}>
    <div style={styles.cardLabel}>{label}</div>
    <div style={styles.cardValue}>{value}</div>
  </article>
);

const styles = {
  page: { minHeight: "100vh", backgroundColor: "#f5f8fc", color: "#10243e", fontFamily: "Segoe UI, Arial, sans-serif" },
  main: { marginLeft: "280px", padding: "84px 24px 24px" },
  title: { margin: 0, color: "#123a6f" },
  subtitle: { color: "#4c6480" },
  cards: { display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: 12, margin: "16px 0" },
  card: { background: "#fff", border: "1px solid #d7e5f5", borderRadius: 12, padding: 14, boxShadow: "0 6px 14px rgba(0,0,0,0.06)" },
  cardLabel: { color: "#4c6480", fontSize: 12, fontWeight: 700 },
  cardValue: { color: "#113864", fontSize: 24, fontWeight: 800 },
  section: { background: "#fff", borderRadius: 14, padding: 16, boxShadow: "0 8px 20px rgba(0,0,0,0.08)", marginTop: 14 },
  sectionTitle: { marginTop: 0, color: "#123a6f" },
  form: { display: "grid", gridTemplateColumns: "2fr 2fr 1.4fr 1.5fr", gap: 10 },
  input: { height: 40, borderRadius: 8, border: "1px solid #c6d7eb", padding: "0 10px", fontSize: 14 },
  primaryButton: { background: "#1762bf", color: "#fff", border: "none", borderRadius: 8, fontWeight: 700, cursor: "pointer" },
  secondaryButton: { background: "#edf4fd", color: "#174577", border: "1px solid #8ab0dc", borderRadius: 8, padding: "6px 10px", cursor: "pointer", fontWeight: 700 },
  tableWrap: { overflowX: "auto" },
  table: { width: "100%", borderCollapse: "collapse" },
  badge: { display: "inline-block", borderRadius: 14, background: "#e6f0fb", color: "#0b2b55", padding: "2px 8px", fontSize: 12, fontWeight: 700 },
  timeline: { listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 8 },
  timelineItem: { border: "1px solid #d7e5f5", borderRadius: 10, padding: 10, background: "#fbfdff" },
};

export default TMCDashboard;
