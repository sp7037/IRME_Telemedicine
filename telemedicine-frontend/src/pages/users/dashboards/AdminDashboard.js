import React, { useCallback, useEffect, useMemo, useState } from "react";
import Header from "../../../components/Header";
import Footer from "../../../components/Footer";
import Sidebar from "../../../components/Sidebar";
import { dashboardContentMarginLeft } from "../../../constants/dashboardLayout";
import {
  DASHBOARD_BORDER,
  DASHBOARD_PAGE_BG,
  DASHBOARD_SECTION_BG,
  DASHBOARD_SHADOW,
} from "../../../constants/brandTheme";
import {
  createStaffFeeSetting,
  getStaffDoctors,
  getStaffFeeSettings,
  getStaffOperationsReport,
  getStaffPatients,
  getStaffPatientRechargeRequests,
  getStaffTMCRechargeRequests,
  getStaffTMCs,
  processTMCRechargeRequest,
  processPatientRechargeRequest,
  staffTopupAdminPlatformWallet,
  staffTopupPatientWallet,
  staffTopupTMCWallet,
  updateStaffTMCOfferSettings,
  updateDoctorVerification,
} from "../../../api/users";

const AdminDashboard = () => {
  const [report, setReport] = useState(null);
  const [fees, setFees] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [patients, setPatients] = useState([]);
  const [patientFilter, setPatientFilter] = useState("ALL");
  const [tmcs, setTmcs] = useState([]);
  const [recharges, setRecharges] = useState([]);
  const [patientRecharges, setPatientRecharges] = useState([]);
  const [message, setMessage] = useState("");
  const [feeForm, setFeeForm] = useState({ direct_patient_fee: "", tmc_consultation_fee: "", platform_fee_percentage: "" });
  const [topupForm, setTopupForm] = useState({ tmc_profile_id: "", amount: "", description: "" });
  const [adminTopupForm, setAdminTopupForm] = useState({ amount: "", description: "" });
  const [tmcOfferForm, setTmcOfferForm] = useState({
    tmc_profile_id: "",
    free_consultation_quota: "",
    free_consultations_used: "",
    discount_percentage: "",
    discounted_consultation_quota: "",
    discounted_consultations_used: "",
  });
  const [patientTopupForm, setPatientTopupForm] = useState({ patient_profile_id: "", amount: "", description: "" });
  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    () => typeof window !== "undefined" && window.innerWidth < 768
  );
  const [winW, setWinW] = useState(() => (typeof window !== "undefined" ? window.innerWidth : 1200));

  const loadAll = useCallback(async () => {
    const [r, f, d, p, t, rq, prq] = await Promise.all([
      getStaffOperationsReport(),
      getStaffFeeSettings(),
      getStaffDoctors(),
      getStaffPatients(),
      getStaffTMCs(),
      getStaffTMCRechargeRequests(),
      getStaffPatientRechargeRequests(),
    ]);
    setReport(r);
    setFees(Array.isArray(f) ? f : []);
    setDoctors(Array.isArray(d) ? d : []);
    setPatients(Array.isArray(p) ? p : []);
    setTmcs(Array.isArray(t) ? t : []);
    setRecharges(Array.isArray(rq) ? rq : []);
    setPatientRecharges(Array.isArray(prq) ? prq : []);
  }, []);

  useEffect(() => {
    const onResize = () => {
      const w = window.innerWidth;
      setWinW(w);
      if (w >= 768) setSidebarCollapsed(false);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    loadAll().catch((err) => setMessage(err?.message || "Could not load admin data."));
  }, [loadAll]);

  const submitFees = async (e) => {
    e.preventDefault();
    setMessage("");
    try {
      await createStaffFeeSetting(feeForm);
      setFeeForm({ direct_patient_fee: "", tmc_consultation_fee: "", platform_fee_percentage: "" });
      await loadAll();
      setMessage("Fee setting activated.");
    } catch (err) {
      setMessage(err?.response?.data?.error || err.message || "Fee update failed.");
    }
  };

  const submitTMCOffer = async (e) => {
    e.preventDefault();
    setMessage("");
    try {
      await updateStaffTMCOfferSettings(tmcOfferForm);
      await loadAll();
      setMessage("TMC free and discount offer settings updated.");
    } catch (err) {
      setMessage(err?.response?.data?.error || err.message || "TMC offer update failed.");
    }
  };

  const submitAdminTopup = async (e) => {
    e.preventDefault();
    setMessage("");
    try {
      await staffTopupAdminPlatformWallet(adminTopupForm);
      setAdminTopupForm({ amount: "", description: "" });
      await loadAll();
      setMessage("Admin platform wallet top-up recorded.");
    } catch (err) {
      setMessage(err?.response?.data?.error || err.message || "Admin wallet top-up failed.");
    }
  };

  const submitTopup = async (e) => {
    e.preventDefault();
    setMessage("");
    try {
      await staffTopupTMCWallet(topupForm);
      setTopupForm({ tmc_profile_id: "", amount: "", description: "" });
      await loadAll();
      setMessage("TMC wallet top-up recorded.");
    } catch (err) {
      setMessage(err?.response?.data?.error || err.message || "Top-up failed.");
    }
  };

  const submitPatientTopup = async (e) => {
    e.preventDefault();
    setMessage("");
    try {
      await staffTopupPatientWallet(patientTopupForm);
      setPatientTopupForm({ patient_profile_id: "", amount: "", description: "" });
      await loadAll();
      setMessage("Patient wallet top-up recorded.");
    } catch (err) {
      setMessage(err?.response?.data?.error || err.message || "Patient top-up failed.");
    }
  };

  const processRecharge = async (id, action) => {
    setMessage("");
    try {
      await processTMCRechargeRequest(id, { action });
      await loadAll();
      setMessage(`Recharge ${action}d.`);
    } catch (err) {
      setMessage(err?.response?.data?.error || err.message || "Recharge update failed.");
    }
  };

  const processPatientRecharge = async (id, action) => {
    setMessage("");
    try {
      await processPatientRechargeRequest(id, { action });
      await loadAll();
      setMessage(`Patient recharge ${action}d.`);
    } catch (err) {
      setMessage(err?.response?.data?.error || err.message || "Patient recharge update failed.");
    }
  };

  const verifyDoctor = async (id, action) => {
    setMessage("");
    try {
      await updateDoctorVerification(id, action);
      await loadAll();
      setMessage("Doctor verification updated.");
    } catch (err) {
      setMessage(err?.response?.data?.error || err.message || "Doctor update failed.");
    }
  };

  const contentMarginLeft = dashboardContentMarginLeft(winW < 768, sidebarCollapsed);
  const grid = winW < 760 ? "1fr" : "repeat(auto-fit, minmax(190px, 1fr))";
  const filteredPatients = useMemo(() => {
    if (patientFilter === "ALL") return patients;
    return patients.filter((patient) => patient.patient_type === patientFilter);
  }, [patientFilter, patients]);

  return (
    <div style={styles.page}>
      <Header role="admin" />
      <Sidebar role="admin" isCollapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed((c) => !c)} />
      <div style={{ marginLeft: contentMarginLeft, flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
        <main style={styles.main}>
          <h1 style={styles.title}>Admin operations</h1>
          <p style={styles.subtitle}>Fees, patient wallets, TMC wallet controls, recharge approvals, doctor verification, and reporting.</p>
          {message ? <div style={styles.banner}>{message}</div> : null}

          {report ? (
            <section style={styles.cards}>
              <Metric label="Consultations" value={report.consultations_total} />
              <Metric label="Direct" value={report.consultations_by_source?.DIRECT || 0} />
              <Metric label="TMC" value={report.consultations_by_source?.TMC || 0} />
              <Metric label="Patients" value={patients.length} />
              <Metric label="Pending recharges" value={report.tmc_finance_rollups?.pending_recharge_requests || 0} />
              <Metric label="Platform wallet" value={`Rs ${report.admin_platform_wallet?.balance || "0.00"}`} />
              <Metric label="Platform fees" value={`Rs ${report.admin_platform_wallet?.total_platform_fees || "0.00"}`} />
              <Metric label="Doctor subsidies" value={`Rs ${report.admin_platform_wallet?.total_doctor_subsidies || "0.00"}`} />
            </section>
          ) : null}

          <section style={styles.section}>
            <h3 style={styles.sectionTitle}>Fee Settings</h3>
            <p style={styles.subtitle}>
              Doctor profile fee is used first. These direct/TMC fees are fallbacks only; platform fee applies to paid consultations.
            </p>
            <form onSubmit={submitFees} style={{ ...styles.form, gridTemplateColumns: grid }}>
              <input style={styles.input} type="number" min="0" step="0.01" placeholder="Fallback direct fee" value={feeForm.direct_patient_fee} onChange={(e) => setFeeForm({ ...feeForm, direct_patient_fee: e.target.value })} />
              <input style={styles.input} type="number" min="0" step="0.01" placeholder="Fallback TMC fee" value={feeForm.tmc_consultation_fee} onChange={(e) => setFeeForm({ ...feeForm, tmc_consultation_fee: e.target.value })} />
              <input style={styles.input} type="number" min="0" max="100" step="0.01" placeholder="Platform fee %" value={feeForm.platform_fee_percentage} onChange={(e) => setFeeForm({ ...feeForm, platform_fee_percentage: e.target.value })} />
              <button style={styles.primaryBtn} type="submit">Activate Fees</button>
            </form>
            {(fees || []).slice(0, 5).map((fee) => (
              <Row key={fee.id} title={`${fee.currency} ${fee.direct_patient_fee} direct / ${fee.tmc_consultation_fee} TMC`} meta={`${fee.platform_fee_percentage || "0.00"}% platform fee - ${fee.is_active ? "Active" : "Inactive"}`} />
            ))}
          </section>

          <section style={styles.section}>
            <h3 style={styles.sectionTitle}>Admin Platform Wallet</h3>
            <form onSubmit={submitAdminTopup} style={{ ...styles.form, gridTemplateColumns: grid }}>
              <input style={styles.input} type="number" min="1" step="0.01" required placeholder="Amount" value={adminTopupForm.amount} onChange={(e) => setAdminTopupForm({ ...adminTopupForm, amount: e.target.value })} />
              <input style={styles.input} placeholder="Description" value={adminTopupForm.description} onChange={(e) => setAdminTopupForm({ ...adminTopupForm, description: e.target.value })} />
              <button style={styles.primaryBtn} type="submit">Record Admin Top-up</button>
            </form>
            {(report?.admin_platform_wallet?.recent_entries || []).slice(0, 5).map((entry) => (
              <Row key={entry.id} title={`${entry.entry_type} - Rs ${entry.amount}`} meta={`${entry.description || "Admin platform wallet entry"}${entry.consultation_id ? ` - Consultation #${entry.consultation_id}` : ""}`} />
            ))}
          </section>

          <section style={styles.section}>
            <h3 style={styles.sectionTitle}>TMC Wallet Top-up</h3>
            <form onSubmit={submitTopup} style={{ ...styles.form, gridTemplateColumns: grid }}>
              <select style={styles.input} required value={topupForm.tmc_profile_id} onChange={(e) => setTopupForm({ ...topupForm, tmc_profile_id: e.target.value })}>
                <option value="">Select TMC</option>
                {tmcs.map((tmc) => <option key={tmc.id} value={tmc.id}>{tmc.name}</option>)}
              </select>
              <input style={styles.input} type="number" min="1" step="0.01" required placeholder="Amount" value={topupForm.amount} onChange={(e) => setTopupForm({ ...topupForm, amount: e.target.value })} />
              <input style={styles.input} placeholder="Description" value={topupForm.description} onChange={(e) => setTopupForm({ ...topupForm, description: e.target.value })} />
              <button style={styles.primaryBtn} type="submit">Record Top-up</button>
            </form>
          </section>

          <section style={styles.section}>
            <h3 style={styles.sectionTitle}>TMC Free & Discount Offers</h3>
            <form onSubmit={submitTMCOffer} style={{ ...styles.form, gridTemplateColumns: grid }}>
              <select
                style={styles.input}
                required
                value={tmcOfferForm.tmc_profile_id}
                onChange={(e) => {
                  const selected = tmcs.find((tmc) => String(tmc.id) === e.target.value);
                  setTmcOfferForm({
                    tmc_profile_id: e.target.value,
                    free_consultation_quota: selected?.free_quota ?? "",
                    free_consultations_used: selected?.free_used ?? "",
                    discount_percentage: selected?.discount_percentage ?? "",
                    discounted_consultation_quota: selected?.discounted_quota ?? "",
                    discounted_consultations_used: selected?.discounted_used ?? "",
                  });
                }}
              >
                <option value="">Select TMC</option>
                {tmcs.map((tmc) => <option key={tmc.id} value={tmc.id}>{tmc.name}</option>)}
              </select>
              <input style={styles.input} type="number" min="0" step="1" placeholder="Free quota" value={tmcOfferForm.free_consultation_quota} onChange={(e) => setTmcOfferForm({ ...tmcOfferForm, free_consultation_quota: e.target.value })} />
              <input style={styles.input} type="number" min="0" step="1" placeholder="Free used" value={tmcOfferForm.free_consultations_used} onChange={(e) => setTmcOfferForm({ ...tmcOfferForm, free_consultations_used: e.target.value })} />
              <input style={styles.input} type="number" min="0" max="100" step="0.01" placeholder="Discount %" value={tmcOfferForm.discount_percentage} onChange={(e) => setTmcOfferForm({ ...tmcOfferForm, discount_percentage: e.target.value })} />
              <input style={styles.input} type="number" min="0" step="1" placeholder="Discount quota" value={tmcOfferForm.discounted_consultation_quota} onChange={(e) => setTmcOfferForm({ ...tmcOfferForm, discounted_consultation_quota: e.target.value })} />
              <input style={styles.input} type="number" min="0" step="1" placeholder="Discount used" value={tmcOfferForm.discounted_consultations_used} onChange={(e) => setTmcOfferForm({ ...tmcOfferForm, discounted_consultations_used: e.target.value })} />
              <button style={styles.primaryBtn} type="submit">Save Offer</button>
            </form>
            {tmcs.slice(0, 6).map((tmc) => (
              <Row
                key={tmc.id}
                title={tmc.name}
                meta={`Free ${tmc.free_used}/${tmc.free_quota} - Discount ${tmc.discount_percentage || "0.00"}% for ${tmc.discounted_used || 0}/${tmc.discounted_quota || 0}`}
              />
            ))}
          </section>

          <section style={styles.section}>
            <h3 style={styles.sectionTitle}>Patient Management</h3>
            <form onSubmit={submitPatientTopup} style={{ ...styles.form, gridTemplateColumns: grid }}>
              <select
                style={styles.input}
                required
                value={patientTopupForm.patient_profile_id}
                onChange={(e) => setPatientTopupForm({ ...patientTopupForm, patient_profile_id: e.target.value })}
              >
                <option value="">Select patient</option>
                {patients.map((patient) => (
                  <option key={patient.id} value={patient.id}>
                    {patient.name}
                  </option>
                ))}
              </select>
              <input
                style={styles.input}
                type="number"
                min="1"
                step="0.01"
                required
                placeholder="Amount"
                value={patientTopupForm.amount}
                onChange={(e) => setPatientTopupForm({ ...patientTopupForm, amount: e.target.value })}
              />
              <input
                style={styles.input}
                placeholder="Description"
                value={patientTopupForm.description}
                onChange={(e) => setPatientTopupForm({ ...patientTopupForm, description: e.target.value })}
              />
              <button style={styles.primaryBtn} type="submit">Top Up Patient</button>
            </form>
            <div style={styles.filterRow}>
              {[
                ["ALL", "All"],
                ["DIRECT", "Direct"],
                ["TMC_ASSISTED", "Via TMC"],
                ["BOTH", "Both"],
                ["REGISTERED", "Registered only"],
              ].map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  style={patientFilter === value ? styles.filterActive : styles.filterBtn}
                  onClick={() => setPatientFilter(value)}
                >
                  {label}
                </button>
              ))}
            </div>
            {filteredPatients.length === 0 ? <p style={styles.subtitle}>No patients found.</p> : filteredPatients.slice(0, 40).map((patient) => (
              <Row
                key={patient.id}
                title={patient.name}
                meta={`${patientTypeLabel(patient.patient_type)} - Wallet Rs ${patient.wallet_balance} - Direct ${patient.direct_consultations} / TMC ${patient.tmc_consultations}${patient.tmc_names?.length ? ` - ${patient.tmc_names.join(", ")}` : ""}`}
              />
            ))}
          </section>

          <section style={styles.section}>
            <h3 style={styles.sectionTitle}>Patient Recharge Requests</h3>
            {patientRecharges.length === 0 ? <p style={styles.subtitle}>No patient recharge requests.</p> : patientRecharges.slice(0, 12).map((r) => (
              <Row
                key={r.id}
                title={`${r.patient_name} requested Rs ${r.amount}`}
                meta={`${r.status} - ${r.provider}${r.reference_note ? ` - ${r.reference_note}` : ""}`}
                actions={r.status === "PENDING" ? (
                  <div style={styles.actions}>
                    <button style={styles.primaryBtn} type="button" onClick={() => processPatientRecharge(r.id, "approve")}>Approve</button>
                    <button style={styles.secondaryBtn} type="button" onClick={() => processPatientRecharge(r.id, "reject")}>Reject</button>
                  </div>
                ) : null}
              />
            ))}
          </section>

          <section style={styles.section}>
            <h3 style={styles.sectionTitle}>TMC Recharge Requests</h3>
            {recharges.length === 0 ? <p style={styles.subtitle}>No recharge requests.</p> : recharges.slice(0, 12).map((r) => (
              <Row
                key={r.id}
                title={`${r.tmc_name} requested Rs ${r.amount}`}
                meta={`${r.status}${r.reference_note ? ` - ${r.reference_note}` : ""}`}
                actions={r.status === "PENDING" ? (
                  <div style={styles.actions}>
                    <button style={styles.primaryBtn} type="button" onClick={() => processRecharge(r.id, "approve")}>Approve</button>
                    <button style={styles.secondaryBtn} type="button" onClick={() => processRecharge(r.id, "reject")}>Reject</button>
                  </div>
                ) : null}
              />
            ))}
          </section>

          <section style={styles.section}>
            <h3 style={styles.sectionTitle}>Doctor Verification</h3>
            <p style={{ ...styles.subtitle, marginBottom: 12 }}>
              <strong>Verify profile</strong> confirms documents and details. <strong>Approve consultations</strong> allows the doctor to receive requests and use consultation features.
            </p>
            {doctors.length === 0 ? <p style={styles.subtitle}>No doctors found.</p> : doctors.slice(0, 20).map((doc) => {
              const hasPendingChanges = doc.has_pending_changes || doc.pending_change_request_count > 0;
              const verifyAction = hasPendingChanges ? "verify" : doc.admin_verified ? "unverify" : "verify";
              const verifyLabel = hasPendingChanges ? "Apply profile changes" : doc.admin_verified ? "Unverify profile" : "Verify profile";
              const profileLine = doc.admin_verified ? "Profile verified" : "Profile not verified";
              const consultLine = doc.is_approved ? "Consultations on" : "Consultations off";
              return (
                <Row
                  key={doc.id}
                  title={doc.name}
                  meta={`${doc.specialty || "General"} — ${profileLine} · ${consultLine}`}
                  actions={
                    <div style={styles.actions}>
                      <button
                        style={hasPendingChanges || !doc.admin_verified ? styles.primaryBtn : styles.secondaryBtn}
                        type="button"
                        onClick={() => verifyDoctor(doc.id, verifyAction)}
                      >
                        {verifyLabel}
                      </button>
                      <button
                        style={
                          !doc.admin_verified
                            ? { ...styles.secondaryBtn, opacity: 0.55, cursor: "not-allowed" }
                            : styles.secondaryBtn
                        }
                        type="button"
                        disabled={!doc.admin_verified}
                        onClick={() => {
                          if (!doc.admin_verified) return;
                          verifyDoctor(doc.id, doc.is_approved ? "unapprove" : "approve");
                        }}
                      >
                        {doc.is_approved ? "Revoke consultations" : "Approve consultations"}
                      </button>
                    </div>
                  }
                />
              );
            })}
          </section>
        </main>
        <Footer />
      </div>
    </div>
  );
};

const Metric = ({ label, value }) => (
  <article style={styles.metric}>
    <div style={styles.metricLabel}>{label}</div>
    <div style={styles.metricValue}>{value}</div>
  </article>
);

const Row = ({ title, meta, actions }) => (
  <div style={styles.row}>
    <div>
      <strong style={styles.rowTitle}>{title}</strong>
      <div style={styles.rowMeta}>{meta}</div>
    </div>
    {actions}
  </div>
);

const patientTypeLabel = (value) => {
  if (value === "DIRECT") return "Direct patient";
  if (value === "TMC_ASSISTED") return "TMC-assisted patient";
  if (value === "BOTH") return "Direct + TMC patient";
  return "Registered patient";
};

const styles = {
  page: { minHeight: "100vh", background: DASHBOARD_PAGE_BG, color: "#10243e", fontFamily: "Segoe UI, system-ui, sans-serif", display: "flex", flexDirection: "column" },
  main: { flex: 1, padding: "16px 16px 48px", maxWidth: "100%", boxSizing: "border-box" },
  title: { margin: "0 0 4px", color: "#002043", fontSize: "clamp(1.35rem, 3vw, 1.9rem)", lineHeight: 1.15 },
  subtitle: { color: "#4c6480", marginTop: 0 },
  banner: { background: "#edf7ee", border: "1px solid #acd8b4", color: "#185a2b", borderRadius: 12, padding: 12, marginBottom: 12 },
  cards: { display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: 12, margin: "16px 0" },
  metric: { background: "#fff", border: DASHBOARD_BORDER, borderRadius: 14, padding: 14, boxShadow: DASHBOARD_SHADOW },
  metricLabel: { color: "#4c6480", fontSize: 12, fontWeight: 700 },
  metricValue: { color: "#113864", fontSize: 24, fontWeight: 800 },
  section: { background: DASHBOARD_SECTION_BG, border: DASHBOARD_BORDER, borderRadius: 16, padding: 18, boxShadow: DASHBOARD_SHADOW, marginTop: 14 },
  sectionTitle: { marginTop: 0, color: "#123a6f" },
  form: { display: "grid", gap: 10, alignItems: "end", marginBottom: 12 },
  input: { height: 42, borderRadius: 10, border: "1px solid #c6d7eb", padding: "0 12px", fontSize: 14, background: "#fbfdff", boxSizing: "border-box" },
  primaryBtn: { background: "#1762bf", color: "#fff", border: "none", borderRadius: 10, padding: "9px 12px", fontWeight: 700, cursor: "pointer" },
  secondaryBtn: { background: "#edf4fd", color: "#174577", border: "1px solid #8ab0dc", borderRadius: 10, padding: "9px 12px", cursor: "pointer", fontWeight: 700 },
  filterRow: { display: "flex", gap: 8, flexWrap: "wrap", margin: "8px 0 12px" },
  filterBtn: { background: "#edf4fd", color: "#174577", border: "1px solid #8ab0dc", borderRadius: 10, padding: "8px 11px", cursor: "pointer", fontWeight: 700 },
  filterActive: { background: "#1762bf", color: "#fff", border: "1px solid #1762bf", borderRadius: 10, padding: "8px 11px", cursor: "pointer", fontWeight: 700 },
  row: { border: "1px solid #d7e5f5", borderRadius: 12, padding: 12, background: "#fbfdff", marginTop: 8, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" },
  rowTitle: { color: "#113864" },
  rowMeta: { color: "#4c6480", fontSize: 13, marginTop: 4 },
  actions: { display: "flex", gap: 8, flexWrap: "wrap" },
};

export default AdminDashboard;
