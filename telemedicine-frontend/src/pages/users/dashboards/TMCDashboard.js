import React, { useEffect, useState, useCallback, useMemo, useRef } from "react";
import Header from "../../../components/Header";
import Footer from "../../../components/Footer";
import Sidebar from "../../../components/Sidebar";
import ConsultationDetailModal from "../../../components/dashboard/ConsultationDetailModal";
import ConsultationChatPanel from "../../../components/dashboard/ConsultationChatPanel";
import {
  getTMCSummary,
  getTMCConsultations,
  getTMCPatients,
  createTMCPatient,
  createTMCConsultation,
  getConsultationEvents,
  getTMCFinanceSummary,
  createTMCRechargeRequest,
  createTMCRazorpayOrder,
  verifyTMCRazorpayPayment,
  cancelTMCRechargeRequest,
  lookupPincode,
  getTMCProfile,
  updateTMCProfile,
  uploadTMCQualificationDocument,
  deleteTMCQualificationDocument,
  requestConsultationFollowUp,
} from "../../../api/users";
import { getStatusMessage, getAvailableActions } from "../../../utils/consultationStatus";
import { StaleNotification } from "../../../components/dashboard/InlineNotification";
import axios from "axios";
import { API_BASE_URL } from "../../../api/config";
import { dashboardContentMarginLeft } from "../../../constants/dashboardLayout";
import { BRAND_NAVY } from "../../../constants/brandTheme";

function loadRazorpayCheckout() {
  return new Promise((resolve, reject) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    const existing = document.querySelector('script[src="https://checkout.razorpay.com/v1/checkout.js"]');
    if (existing) {
      existing.addEventListener("load", () => resolve(true), { once: true });
      existing.addEventListener("error", () => reject(new Error("Could not load Razorpay checkout.")), { once: true });
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => reject(new Error("Could not load Razorpay checkout."));
    document.body.appendChild(script);
  });
}

const TMCDashboard = () => {
  const [summary, setSummary] = useState(null);
  const [consultations, setConsultations] = useState([]);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState([]);
  const [finance, setFinance] = useState(null);
  const [selectedConsultation, setSelectedConsultation] = useState(null);
  const [chatConsultation, setChatConsultation] = useState(null);
  const [chatEvents, setChatEvents] = useState([]);
  const [followUpBusy, setFollowUpBusy] = useState(false);
  const [followUpMsg, setFollowUpMsg] = useState("");
  const [rechargeForm, setRechargeForm] = useState({ amount: "", reference_note: "" });
  const [rechargeSaving, setRechargeSaving] = useState(false);
  const [rechargeMsg, setRechargeMsg] = useState("");
  const [tmcProfile, setTmcProfile] = useState(null);
  const [profileMsg, setProfileMsg] = useState("");
  const [profileSaving, setProfileSaving] = useState(false);
  const [pinLookupLoading, setPinLookupLoading] = useState(false);
  const [profileForm, setProfileForm] = useState({
    tmc_details: "",
    clinic_name: "",
    clinic_address_street: "",
    city: "",
    state: "",
    pin_code: "",
    aadhaar_document: null,
    user_photo: null,
    clinic_front_photo: null,
  });
  const [qualificationForm, setQualificationForm] = useState({
    exam_name: "SECONDARY",
    board_or_university: "",
    percentage: "",
    document: null,
  });
  const [form, setForm] = useState({
    patient_id: "",
    doctor_id: "",
    scheduled_time: "",
  });
  const [patientForm, setPatientForm] = useState({ name: "", age: "", gender: "M" });
  const [patientSaving, setPatientSaving] = useState(false);
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [patientSearch, setPatientSearch] = useState("");
  const [doctorSearch, setDoctorSearch] = useState("");
  const [doctorSpecialty, setDoctorSpecialty] = useState("");
  const [activeSection, setActiveSection] = useState("overview");
  const [isStale, setIsStale] = useState(false);
  
  const mountedRef = useRef(true);
  const inflightRefreshRef = useRef(false);
  const chatIdRef = useRef(null);

  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    () => typeof window !== "undefined" && window.innerWidth < 768
  );
  const [winW, setWinW] = useState(() => (typeof window !== "undefined" ? window.innerWidth : 1200));

  const loadAll = useCallback(async (skipUnrelated = false) => {
    if (inflightRefreshRef.current) return;
    inflightRefreshRef.current = true;
    
    try {
      if (skipUnrelated) {
        const c = await getTMCConsultations();
        if (!mountedRef.current) return;
        setConsultations(Array.isArray(c) ? c : []);
        setIsStale(false);
      } else {
        const [s, c, p, profile] = await Promise.all([
          getTMCSummary(),
          getTMCConsultations(),
          getTMCPatients(),
          getTMCProfile(),
        ]);
        const fin = await getTMCFinanceSummary();
        
        if (!mountedRef.current) return;
        
        setSummary(s);
        setConsultations(Array.isArray(c) ? c : []);
        setPatients(Array.isArray(p) ? p : []);
        const profileData = profile?.profile || profile;
        setTmcProfile(profileData);
        setProfileForm((current) => ({
          ...current,
          tmc_details: profileData?.tmc_details || "",
          clinic_name: profileData?.clinic_name || "",
          clinic_address_street: profileData?.clinic_address_street || "",
          city: profileData?.city || "",
          state: profileData?.state || "",
          pin_code: profileData?.pin_code || "",
          aadhaar_document: null,
          user_photo: null,
          clinic_front_photo: null,
        }));
        const d = await axios.get(`${API_BASE_URL}/consultations/available-doctors/`);
        setDoctors(Array.isArray(d.data) ? d.data : []);
        setFinance(fin);
        setIsStale(false);
      }
    } catch (err) {
      if (mountedRef.current) {
        setIsStale(true);
      }
    } finally {
      inflightRefreshRef.current = false;
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    const onR = () => {
      const w = window.innerWidth;
      setWinW(w);
      if (w >= 768) setSidebarCollapsed(false);
    };
    window.addEventListener("resize", onR);
    return () => {
      mountedRef.current = false;
      window.removeEventListener("resize", onR);
    };
  }, []);

  useEffect(() => {
    loadAll().catch(() => {});
    const interval = setInterval(() => {
      loadAll(true).catch(() => {});
    }, 8000);
    return () => clearInterval(interval);
  }, [loadAll]);

  useEffect(() => {
    if (!chatConsultation?.id) return undefined;
    chatIdRef.current = chatConsultation.id;
    const id = setInterval(async () => {
      const currentChatId = chatIdRef.current;
      try {
        const latest = await getTMCConsultations();
        if (!mountedRef.current || chatIdRef.current !== currentChatId) return;
        const list = Array.isArray(latest) ? latest : [];
        const fresh = list.find((item) => String(item.id) === String(currentChatId));
        setConsultations(list);
        if (fresh && chatIdRef.current === currentChatId) {
          setChatConsultation(fresh);
        }
      } catch (err) {
        // Keep the current modal usable if a background status refresh fails.
      }
    }, 5000);
    return () => {
      clearInterval(id);
      chatIdRef.current = null;
    };
  }, [chatConsultation?.id]);

  const [consultationMsg, setConsultationMsg] = useState("");
  const [patientMsg, setPatientMsg] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setConsultationMsg("");
    try {
      await createTMCConsultation(form);
      setForm({ patient_id: "", doctor_id: "", scheduled_time: "" });
      await loadAll();
      setConsultationMsg("Consultation initiated successfully.");
    } catch (err) {
      setConsultationMsg(err?.response?.data?.error || err.message || "Failed to initiate consultation.");
    } finally {
      setLoading(false);
    }
  };

  const submitPatient = async (e) => {
    e.preventDefault();
    setPatientSaving(true);
    setPatientMsg("");
    try {
      const patient = await createTMCPatient(patientForm);
      setPatientForm({ name: "", age: "", gender: "M" });
      setShowPatientModal(false);
      setForm((current) => ({ ...current, patient_id: patient.id }));
      await loadAll();
      setPatientMsg("Patient added for this TMC.");
    } catch (err) {
      setPatientMsg(err?.response?.data?.error || err.message || "Failed to add patient.");
    } finally {
      setPatientSaving(false);
    }
  };

  const submitRecharge = async (e) => {
    e.preventDefault();
    setRechargeSaving(true);
    setRechargeMsg("");
    let rechargeRequestId = null;
    try {
      const requestData = await createTMCRechargeRequest({
        amount: rechargeForm.amount,
        reference_note: rechargeForm.reference_note,
      });
      rechargeRequestId = requestData.id;
      const order = await createTMCRazorpayOrder(rechargeRequestId);
      if (order.razorpay_enabled && order.key_id && order.order_id) {
        await loadRazorpayCheckout();
        let completed = false;
        await new Promise((resolve, reject) => {
          const checkout = new window.Razorpay({
            key: order.key_id,
            amount: order.amount_paise,
            currency: order.currency || "INR",
            name: "IRME Telemedicine",
            description: "TMC wallet recharge",
            order_id: order.order_id,
            handler: async (response) => {
              try {
                    await verifyTMCRazorpayPayment(rechargeRequestId, response);
                completed = true;
                resolve();
              } catch (verifyErr) {
                reject(verifyErr);
              }
            },
            modal: {
              ondismiss: async () => {
                if (!completed) {
                  try {
                    await cancelTMCRechargeRequest(rechargeRequestId);
                  } catch (cancelErr) {
                    // The summary reload below will still pick up any server-side state.
                  }
                  reject(new Error("Transaction was cancelled. No amount was added to the wallet."));
                }
              },
            },
          });
          checkout.open();
        });
        setRechargeMsg("Payment successful. TMC wallet credited.");
      } else {
        await cancelTMCRechargeRequest(rechargeRequestId);
        setRechargeMsg("Razorpay is not configured. No pending recharge was created.");
      }
      setRechargeForm({ amount: "", reference_note: "" });
      await loadAll();
    } catch (err) {
      if (rechargeRequestId) {
        await cancelTMCRechargeRequest(rechargeRequestId).catch(() => {});
      }
      setRechargeMsg(err?.response?.data?.error || err.message || "Transaction was cancelled. No amount was added to the wallet.");
      await loadAll().catch(() => {});
    } finally {
      setRechargeSaving(false);
    }
  };

  const runPinLookup = async () => {
    const pin = String(profileForm.pin_code || "").trim();
    if (!/^\d{6}$/.test(pin)) {
      setProfileMsg("Enter a valid 6-digit clinic PIN code.");
      return;
    }
    setPinLookupLoading(true);
    setProfileMsg("");
    try {
      const data = await lookupPincode(pin);
      setProfileForm((current) => ({
        ...current,
        pin_code: data.pincode || pin,
        city: data.district || current.city,
        state: data.state || current.state,
      }));
    } catch (err) {
      setProfileMsg(err?.response?.data?.error || err.message || "Could not fetch city/state for this PIN.");
    } finally {
      setPinLookupLoading(false);
    }
  };

  const submitProfile = async (e) => {
    e.preventDefault();
    setProfileSaving(true);
    setProfileMsg("");
    try {
      const result = await updateTMCProfile(profileForm);
      const profileData = result?.profile || result;
      setTmcProfile(profileData);
      setProfileForm((current) => ({
        ...current,
        aadhaar_document: null,
        user_photo: null,
        clinic_front_photo: null,
      }));
      setProfileMsg(result?.message || "TMC profile saved. Admin can verify and approve the center from the admin panel.");
      await loadAll();
    } catch (err) {
      const data = err?.response?.data;
      setProfileMsg(data?.error || err.message || "Could not save TMC profile.");
    } finally {
      setProfileSaving(false);
    }
  };

  const submitQualification = async (e) => {
    e.preventDefault();
    setProfileMsg("");
    try {
      const result = await uploadTMCQualificationDocument(qualificationForm);
      setQualificationForm({ exam_name: "SECONDARY", board_or_university: "", percentage: "", document: null });
      await loadAll();
      setProfileMsg(result?.message || "Qualification document uploaded.");
    } catch (err) {
      const data = err?.response?.data;
      setProfileMsg(data?.document?.[0] || data?.error || err.message || "Could not upload qualification document.");
    }
  };

  const removeQualification = async (id) => {
    setProfileMsg("");
    try {
      const result = await deleteTMCQualificationDocument(id);
      await loadAll();
      setProfileMsg(result?.message || "Qualification document removed.");
    } catch (err) {
      setProfileMsg(err?.response?.data?.error || err.message || "Could not remove document.");
    }
  };

  const openTimeline = async (consultation) => {
    setSelectedConsultation(consultation);
    const items = await getConsultationEvents(consultation.id, { order: "asc" });
    setEvents(Array.isArray(items) ? items : []);
  };

  const openChat = async (consultation) => {
    setFollowUpMsg("");
    let current = consultation;
    try {
      const latest = await getTMCConsultations();
      const list = Array.isArray(latest) ? latest : [];
      setConsultations(list);
      current = list.find((item) => String(item.id) === String(consultation.id)) || consultation;
    } catch (err) {
      current = consultation;
    }
    setChatConsultation(current);
    const items = await getConsultationEvents(consultation.id, { order: "asc" });
    setChatEvents(Array.isArray(items) ? items : []);
  };

  const requestTMCFollowUp = async (consultation) => {
    setFollowUpBusy(true);
    setFollowUpMsg("");
    try {
      const result = await requestConsultationFollowUp(consultation.id);
      const message = result.is_billable
          ? `Follow-up request sent. Rs ${result.amount_charged} has been charged from the TMC wallet.`
          : "Free follow-up request sent to the doctor.";
      await loadAll();
      await openChat({
        ...consultation,
        follow_up: { ...(consultation.follow_up || {}), active_status: "PENDING", can_request: false },
      });
      setFollowUpMsg(message);
    } catch (err) {
      setFollowUpMsg(err?.message || "Could not request follow-up.");
    } finally {
      setFollowUpBusy(false);
    }
  };

  const isNarrow = winW < 768;
  const contentMarginLeft = dashboardContentMarginLeft(isNarrow, sidebarCollapsed);
  const rechargeGrid = winW < 720 ? "1fr" : "minmax(0,1fr) minmax(0,2fr) auto";
  const tmcLocked = !!(tmcProfile?.admin_verified || tmcProfile?.is_approved);
  const filteredPatients = useMemo(() => {
    const term = patientSearch.trim().toLowerCase();
    if (!term) return patients;
    return patients.filter((p) => `${p.name} ${p.age || ""} ${p.gender || ""}`.toLowerCase().includes(term));
  }, [patients, patientSearch]);
  const filteredDoctors = useMemo(() => {
    const term = doctorSearch.trim().toLowerCase();
    const spec = doctorSpecialty.trim().toLowerCase();
    return doctors.filter((d) => {
      const text = [
        d.first_name,
        d.last_name,
        d.specialty,
        d.qualification,
        d.hospital_or_clinic_name,
        d.city,
        d.state,
      ].join(" ").toLowerCase();
      return (!term || text.includes(term)) && (!spec || String(d.specialty || "").toLowerCase().includes(spec));
    });
  }, [doctors, doctorSearch, doctorSpecialty]);
  const patientSearchTerm = patientSearch.trim();
  const doctorHasSearch = !!(doctorSearch.trim() || doctorSpecialty.trim());
  const selectedPatient = patients.find((p) => String(p.id) === String(form.patient_id));
  const selectedDoctor = doctors.find((d) => String(d.id) === String(form.doctor_id));
  const patientResults = patientSearchTerm
    ? filteredPatients.slice(0, 8)
    : selectedPatient
      ? [selectedPatient]
      : patients.slice(0, 4);
  const patientsPageList = patientSearchTerm ? filteredPatients.slice(0, 24) : patients.slice(0, 12);
  const doctorResults = doctorHasSearch
    ? filteredDoctors.slice(0, 12)
    : selectedDoctor
      ? [selectedDoctor]
      : [];
  const consultationBillingLabel = (consultation) =>
    consultation.billing_type === "FREE" || consultation.is_free ? "Free" : "Paid";
  const freeConsultations = consultations.filter((c) => consultationBillingLabel(c) === "Free").length;
  const paidConsultations = consultations.filter((c) => consultationBillingLabel(c) === "Paid").length;
  const activeConsultations = consultations.filter((c) => ["ACCEPTED", "QUEUED", "IN_PROGRESS", "POSTPONED"].includes(c.status)).length;
  const completedConsultations = consultations.filter((c) => c.status === "COMPLETED" || c.is_completed).length;
  const pendingRecharges = (finance?.recent_recharge_requests || []).filter((r) => r.status === "PENDING" && r.provider !== "RAZORPAY").length;
  const chatStatus = chatConsultation?.follow_up?.active_status === "IN_PROGRESS" ? "IN_PROGRESS" : chatConsultation?.status;
  const sectionMenu = [
    { key: "overview", label: "Overview", helper: "Today at a glance" },
    { key: "start", label: "Start Consultation", helper: "Patient and doctor selection" },
    { key: "patients", label: "Patients", helper: "TMC-assisted records" },
    { key: "consultations", label: "Consultations", helper: "Current and past visits" },
    { key: "wallet", label: "Funds & Finance", helper: "Recharge, fees, ledger" },
    { key: "profile", label: "Profile", helper: "Verification documents" },
    { key: "reports", label: "Reports", helper: "Free, paid, and activity" },
  ];

  return (
    <div style={styles.page}>
      <Header role="tmc" />
      <Sidebar
        role="tmc"
        isCollapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((c) => !c)}
      />
      <div
        style={{
          marginLeft: contentMarginLeft,
          flex: 1,
          minWidth: 0,
          transition: "margin-left 0.25s ease",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <main
          style={{
            ...styles.main,
            padding: "16px 16px 48px",
            maxWidth: "100%",
            boxSizing: "border-box",
          }}
        >
        <section style={styles.heroPanel}>
          <div>
            <span style={styles.kicker}>TMC workspace</span>
            <h1 style={styles.title}>Telemedicine operations dashboard</h1>
            <p style={styles.heroCopy}>Search first, select fast, and keep patient-doctor work arranged for real clinic volume.</p>
          </div>
          <div style={styles.heroStats}>
            <div style={styles.heroStat}>
              <strong>{patients.length}</strong>
              <span>Patients</span>
            </div>
            <div style={styles.heroStat}>
              <strong>{doctors.length}</strong>
              <span>Doctors online</span>
            </div>
            <div style={styles.heroStat}>
              <strong>Rs {finance?.balance || "0.00"}</strong>
              <span>TMC wallet</span>
            </div>
          </div>
        </section>

        <nav style={styles.sectionMenu} aria-label="TMC dashboard sections">
          {sectionMenu.map((item) => (
            <button
              key={item.key}
              type="button"
              style={activeSection === item.key ? styles.sectionMenuActive : styles.sectionMenuItem}
              onClick={() => setActiveSection(item.key)}
            >
              <strong>{item.label}</strong>
              <span>{item.helper}</span>
            </button>
          ))}
        </nav>

        {activeSection === "overview" && (
          <>
            {summary && (
              <div style={styles.cards}>
                <Card label="Total Consultations" value={summary.total} />
                <Card label="Active Now" value={activeConsultations} />
                <Card label="Completed" value={completedConsultations} />
                <Card label="Patients Added" value={patients.length} />
                <Card label="Wallet Balance" value={`Rs ${finance?.balance || "0.00"}`} />
                <Card label="Free Used" value={`${summary.free_used}/${summary.free_quota}`} />
              </div>
            )}
            <section style={styles.section}>
              <div style={styles.actionGrid}>
                <button type="button" style={styles.actionCard} onClick={() => setActiveSection("start")}>
                  <strong>Start consultation</strong>
                  <span>Book a TMC-assisted visit with a selected doctor.</span>
                </button>
                <button type="button" style={styles.actionCard} onClick={() => setActiveSection("patients")}>
                  <strong>Add or find patient</strong>
                  <span>Manage only patients created by this TMC.</span>
                </button>
                <button type="button" style={styles.actionCard} onClick={() => setActiveSection("wallet")}>
                  <strong>Recharge wallet</strong>
                  <span>{pendingRecharges ? `${pendingRecharges} pending recharge request(s).` : "View balance and request funds."}</span>
                </button>
                <button type="button" style={styles.actionCard} onClick={() => setActiveSection("profile")}>
                  <strong>Profile verification</strong>
                  <span>{tmcProfile?.completion_percentage || 0}% complete{tmcProfile?.has_pending_changes ? " · changes pending" : ""}</span>
                </button>
              </div>
            </section>
          </>
        )}

        {activeSection === "profile" && (
        <section style={styles.section}>
          <div style={styles.sectionHeader}>
            <div>
              <h3 style={styles.sectionTitle}>TMC Profile & Verification</h3>
              <p style={styles.subtitle}>
                Clinic address, operator documents, clinic photo, and education records for admin approval.
              </p>
            </div>
            <span style={styles.badge}>
              {tmcProfile?.completion_percentage || 0}% complete
            </span>
          </div>
          {profileMsg ? <div style={styles.notice}>{profileMsg}</div> : null}
          {tmcLocked ? (
            <div style={styles.lockNotice}>
              This TMC profile is verified or approved. Any saved profile or document change is submitted to admin for approval before it takes effect.
            </div>
          ) : null}
          <form onSubmit={submitProfile} style={styles.profileGrid}>
            <input style={styles.input} placeholder="Present clinic name" value={profileForm.clinic_name} onChange={(e) => setProfileForm({ ...profileForm, clinic_name: e.target.value })} required />
            <input style={styles.input} placeholder="Clinic PIN code" value={profileForm.pin_code} onChange={(e) => setProfileForm({ ...profileForm, pin_code: e.target.value })} onBlur={runPinLookup} required />
            <button type="button" style={styles.secondaryButton} onClick={runPinLookup} disabled={pinLookupLoading}>{pinLookupLoading ? "Fetching..." : "Fetch City/State"}</button>
            <input style={styles.input} placeholder="City / district" value={profileForm.city} onChange={(e) => setProfileForm({ ...profileForm, city: e.target.value })} required />
            <input style={styles.input} placeholder="State" value={profileForm.state} onChange={(e) => setProfileForm({ ...profileForm, state: e.target.value })} required />
            <input style={styles.input} placeholder="Clinic street address" value={profileForm.clinic_address_street} onChange={(e) => setProfileForm({ ...profileForm, clinic_address_street: e.target.value })} required />
            <textarea style={{ ...styles.input, height: 72, paddingTop: 10 }} placeholder="TMC service details" value={profileForm.tmc_details} onChange={(e) => setProfileForm({ ...profileForm, tmc_details: e.target.value })} />
            <label style={styles.fileLabel}>Aadhaar PDF<input type="file" accept="application/pdf,.pdf" onChange={(e) => setProfileForm({ ...profileForm, aadhaar_document: e.target.files?.[0] || null })} /></label>
            <label style={styles.fileLabel}>TMC user photo<input type="file" accept="image/*" onChange={(e) => setProfileForm({ ...profileForm, user_photo: e.target.files?.[0] || null })} /></label>
            <label style={styles.fileLabel}>Clinic front photo<input type="file" accept="image/*" onChange={(e) => setProfileForm({ ...profileForm, clinic_front_photo: e.target.files?.[0] || null })} /></label>
            <button type="submit" disabled={profileSaving} style={styles.primaryButton}>{profileSaving ? "Saving..." : tmcLocked ? "Request Profile Change" : "Save TMC Profile"}</button>
          </form>
          <div style={styles.documentLinks}>
            {tmcProfile?.aadhaar_document_url ? <a href={tmcProfile.aadhaar_document_url} target="_blank" rel="noreferrer">Aadhaar document</a> : null}
            {tmcProfile?.user_photo_url ? <a href={tmcProfile.user_photo_url} target="_blank" rel="noreferrer">User photo</a> : null}
            {tmcProfile?.clinic_front_photo_url ? <a href={tmcProfile.clinic_front_photo_url} target="_blank" rel="noreferrer">Clinic front photo</a> : null}
          </div>

          <h4 style={styles.subheading}>Qualification Documents</h4>
          <form onSubmit={submitQualification} style={styles.qualificationGrid}>
            <select style={styles.input} value={qualificationForm.exam_name} onChange={(e) => setQualificationForm({ ...qualificationForm, exam_name: e.target.value })}>
              <option value="SECONDARY">Secondary</option>
              <option value="SENIOR_SECONDARY">Senior Secondary</option>
              <option value="UG">UG</option>
              <option value="CERTIFICATE">Certificate</option>
              <option value="OTHER">Other</option>
            </select>
            <input style={styles.input} placeholder="Board / university" value={qualificationForm.board_or_university} onChange={(e) => setQualificationForm({ ...qualificationForm, board_or_university: e.target.value })} required />
            <input style={styles.input} type="number" min="0" max="100" step="0.01" placeholder="Percentage" value={qualificationForm.percentage} onChange={(e) => setQualificationForm({ ...qualificationForm, percentage: e.target.value })} />
            <label style={styles.fileLabel}>PDF document<input type="file" accept="application/pdf,.pdf" required onChange={(e) => setQualificationForm({ ...qualificationForm, document: e.target.files?.[0] || null })} /></label>
            <button type="submit" style={styles.primaryButton}>{tmcLocked ? "Request Add" : "Add Document"}</button>
          </form>
          <div style={styles.tableWrap}>
            <table style={styles.table}>
              <thead>
                <tr><th>Exam</th><th>Board / University</th><th>Percentage</th><th>Document</th><th>Action</th></tr>
              </thead>
              <tbody>
                {(tmcProfile?.qualification_documents || []).map((doc) => (
                  <tr key={doc.id}>
                    <td>{doc.exam_name}</td>
                    <td>{doc.board_or_university}</td>
                    <td>{doc.percentage || "-"}</td>
                    <td>{doc.document_url ? <a href={doc.document_url} target="_blank" rel="noreferrer">Open PDF</a> : "-"}</td>
                    <td><button type="button" style={styles.secondaryButton} onClick={() => removeQualification(doc.id)}>{tmcLocked ? "Request Remove" : "Remove"}</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        )}

        {activeSection === "wallet" && (
        <>
        <section style={styles.section}>
          <h3 style={styles.sectionTitle}>Wallet Recharge</h3>
          {rechargeMsg ? <div style={styles.notice}>{rechargeMsg}</div> : null}
          <form onSubmit={submitRecharge} style={{ ...styles.rechargeForm, gridTemplateColumns: rechargeGrid }}>
            <input
              type="number"
              min="1"
              step="0.01"
              value={rechargeForm.amount}
              onChange={(e) => setRechargeForm({ ...rechargeForm, amount: e.target.value })}
              placeholder="Amount"
              required
              style={styles.input}
            />
            <input
              value={rechargeForm.reference_note}
              onChange={(e) => setRechargeForm({ ...rechargeForm, reference_note: e.target.value })}
              placeholder="Payment reference / note"
              style={styles.input}
            />
            <button type="submit" disabled={rechargeSaving} style={styles.primaryButton}>
              {rechargeSaving ? "Processing..." : "Add Funds"}
            </button>
          </form>
          {(finance?.recent_recharge_requests || []).length ? (
            <div style={styles.requestList}>
              {finance.recent_recharge_requests.slice(0, 5).map((req) => (
                <div key={req.id} style={styles.timelineItem}>
                  <strong>Rs {req.amount}</strong> - {req.status}
                  {req.reference_note ? <div style={styles.smallMeta}>{req.reference_note}</div> : null}
                  {req.admin_note ? <div style={styles.smallMeta}>{req.admin_note}</div> : null}
                </div>
              ))}
            </div>
          ) : (
            <p style={styles.subtitle}>No recharge requests yet.</p>
          )}
        </section>

        {finance && (
          <section style={styles.section}>
            <h3 style={styles.sectionTitle}>Recent Finance Entries</h3>
            {(finance.recent_entries || []).length ? (finance.recent_entries || []).slice(0, 12).map((entry) => (
              <div key={entry.id} style={styles.timelineItem}>
                <strong>{entry.entry_type}</strong> - Rs {entry.amount}
                <div style={{ color: "#4c6480" }}>{entry.description || "TMC finance entry"}</div>
              </div>
            )) : <p style={styles.subtitle}>No finance entries yet.</p>}
          </section>
        )}
        </>
        )}

        {activeSection === "patients" && (
          <section style={styles.section}>
            <div style={styles.sectionHeader}>
              <div>
                <h3 style={styles.sectionTitle}>TMC Patients</h3>
                <p style={styles.subtitle}>
                  {patientSearchTerm
                    ? `${filteredPatients.length} matching patient(s).`
                    : `Showing latest ${Math.min(patients.length, 12)} of ${patients.length} patient(s). Use search for older records.`}
                </p>
              </div>
              <button type="button" style={styles.primaryButton} onClick={() => setShowPatientModal(true)}>Add New Patient</button>
            </div>
            <div style={styles.toolbarRow}>
              <input style={styles.searchInput} placeholder="Search patient name, age, or sex" value={patientSearch} onChange={(e) => setPatientSearch(e.target.value)} />
              {patientSearchTerm ? (
                <button type="button" style={styles.secondaryButton} onClick={() => setPatientSearch("")}>Clear</button>
              ) : null}
            </div>
            <div style={styles.patientGrid}>
              {patientsPageList.length ? patientsPageList.map((p) => (
                <article key={p.id} style={styles.personCard}>
                  <strong>{p.name}</strong>
                  <span>{p.age ? `${p.age} years` : "Age not set"} · {genderLabel(p.gender)}</span>
                  <button type="button" style={styles.secondaryButton} onClick={() => { setForm({ ...form, patient_id: p.id }); setActiveSection("start"); }}>
                    Start Consultation
                  </button>
                </article>
              )) : (
                <div style={styles.emptyState}>
                  <strong>{patients.length ? "No patient matched this search." : "No TMC patients yet."}</strong>
                  <span>Add a new patient if the record does not exist.</span>
                  <button type="button" style={styles.primaryButton} onClick={() => setShowPatientModal(true)}>Add New Patient</button>
                </div>
              )}
            </div>
          </section>
        )}

        {activeSection === "start" && (
        <section style={styles.section}>
          <div style={styles.sectionHeader}>
            <div>
              <h3 style={styles.sectionTitle}>Initiate Consultation</h3>
              <p style={styles.subtitle}>Find an existing TMC patient, then search doctors by specialty, name, qualification, or clinic.</p>
            </div>
            <button type="button" style={styles.primaryButton} onClick={() => setShowPatientModal(true)}>Add New Patient</button>
          </div>
          {consultationMsg ? (
            <div style={consultationMsg.includes("success") ? styles.successNotice : styles.errorNotice}>
              {consultationMsg}
              <button type="button" style={styles.dismissBtn} onClick={() => setConsultationMsg("")}>×</button>
            </div>
          ) : null}
          <div style={styles.selectionGrid}>
            <div style={styles.finderPanel}>
              <div style={styles.finderHeader}>
                <strong>1. Patient</strong>
                {selectedPatient ? <span style={styles.badge}>Selected</span> : <span style={styles.muted}>Search or add</span>}
              </div>
              <div style={styles.toolbarRow}>
                <input style={styles.searchInput} placeholder="Search this TMC's patients" value={patientSearch} onChange={(e) => setPatientSearch(e.target.value)} />
                {patientSearchTerm ? (
                  <button type="button" style={styles.secondaryButton} onClick={() => setPatientSearch("")}>Clear</button>
                ) : null}
              </div>
              <div style={styles.optionList}>
                {patientResults.length ? patientResults.map((p) => (
                  <button key={p.id} type="button" style={String(form.patient_id) === String(p.id) ? styles.optionActive : styles.optionButton} onClick={() => setForm({ ...form, patient_id: p.id })}>
                    <strong>{p.name}</strong>
                    <span>{p.age ? `${p.age} yrs` : "Age not set"} · {genderLabel(p.gender)}</span>
                  </button>
                )) : (
                  <div style={styles.emptyState}>
                    <strong>No patient found.</strong>
                    <span>Add the patient before starting a TMC-assisted consultation.</span>
                    <button type="button" style={styles.primaryButton} onClick={() => setShowPatientModal(true)}>Add New Patient</button>
                  </div>
                )}
              </div>
            </div>
            <div style={styles.finderPanel}>
              <div style={styles.finderHeader}>
                <strong>2. Doctor</strong>
                {selectedDoctor ? <span style={styles.badge}>Selected</span> : <span style={styles.muted}>Search specialty first</span>}
              </div>
              <div style={styles.searchRow}>
                <input style={styles.searchInput} placeholder="Search doctor name, qualification, clinic" value={doctorSearch} onChange={(e) => setDoctorSearch(e.target.value)} />
                <input style={styles.searchInput} placeholder="Specialty: dermatologist, physician, ortho..." value={doctorSpecialty} onChange={(e) => setDoctorSpecialty(e.target.value)} />
              </div>
              <div style={styles.doctorResultGrid}>
                {doctorResults.length ? doctorResults.map((d) => (
                  <DoctorSearchCard
                    key={d.id}
                    doctor={d}
                    selected={String(form.doctor_id) === String(d.id)}
                    onSelect={() => setForm({ ...form, doctor_id: d.id })}
                  />
                )) : (
                  <div style={styles.emptyState}>
                    <strong>Search to view available doctors.</strong>
                    <span>Use specialty for the fastest result, then open the complete doctor card before selecting.</span>
                  </div>
                )}
              </div>
            </div>
          </div>
          <form onSubmit={submit} style={styles.consultForm}>
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
        )}

        {activeSection === "consultations" && (
        <>
        <section style={styles.section}>
          <div style={styles.sectionHeader}>
            <div>
              <h3 style={styles.sectionTitle}>Consultation Tracking</h3>
              {isStale && (
                <StaleNotification onRetry={() => loadAll()} />
              )}
            </div>
          </div>
          <div style={styles.consultationList}>
            {consultations.length === 0 ? (
              <div style={styles.emptyState}>
                <strong>No consultations yet.</strong>
                <span>Start a consultation from the "Start Consultation" section.</span>
              </div>
            ) : (
              consultations.map((c) => {
                const statusInfo = getStatusMessage(c, "tmc");
                const actions = getAvailableActions(c, "tmc");
                const hasFollowUp = c.follow_up?.active_status === "IN_PROGRESS";
                return (
                  <article key={c.id} style={styles.consultationCard}>
                    <div style={styles.consultationHeader}>
                      <div>
                        <strong style={styles.consultationTitle}>
                          {c.patient_name} → Dr. {c.doctor_name}
                        </strong>
                        <div style={styles.consultationMeta}>
                          ID: {c.id} · {c.consultation_type} · {consultationBillingLabel(c)}
                          {c.scheduled_time && ` · ${new Date(c.scheduled_time).toLocaleString("en-IN", { dateStyle: "short", timeStyle: "short", timeZone: "Asia/Kolkata" })} IST`}
                        </div>
                      </div>
                      <span style={styles.badge}>{c.status}</span>
                    </div>
                    {statusInfo && (
                      <div style={styles.statusMessage}>
                        {statusInfo.message}
                      </div>
                    )}
                    {c.status === "POSTPONED" && c.formatted_suggested_time && (
                      <div style={styles.postponedNote}>
                        <strong>Proposed time:</strong> {c.formatted_suggested_time}
                        <div style={styles.smallMeta}>The patient must accept or reject this time.</div>
                      </div>
                    )}
                    {hasFollowUp && (
                      <div style={styles.followUpIndicator}>
                        Active follow-up session in progress
                      </div>
                    )}
                    <div style={styles.cardActions}>
                      {actions.map((action) => (
                        <button
                          key={action.key}
                          type="button"
                          style={action.variant === "primary" ? styles.primaryButton : styles.secondaryButton}
                          onClick={() => {
                            if (action.key === "open_chat" || action.key === "open_followup") {
                              openChat(c);
                            } else if (action.key === "view_timeline") {
                              openTimeline(c);
                            }
                          }}
                        >
                          {action.label}
                        </button>
                      ))}
                    </div>
                  </article>
                );
              })
            )}
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
        </>
        )}

        {activeSection === "reports" && (
          <section style={styles.section}>
            <h3 style={styles.sectionTitle}>TMC Reports</h3>
            <div style={styles.cards}>
              <Card label="Free Consultations" value={freeConsultations} />
              <Card label="Paid Consultations" value={paidConsultations} />
              <Card label="Completed" value={completedConsultations} />
              <Card label="Wallet Credited" value={`Rs ${finance?.total_credited || "0.00"}`} />
              <Card label="Wallet Debited" value={`Rs ${finance?.total_debited || "0.00"}`} />
              <Card label="TMC Charged" value={`Rs ${finance?.total_charged || "0.00"}`} />
            </div>
            <div style={styles.reportSplit}>
              <div style={styles.reportPanel}>
                <h4 style={styles.subheading}>Recent Consultations</h4>
                {consultations.slice(0, 8).map((c) => (
                  <div key={c.id} style={styles.timelineItem}>
                    <strong>{c.patient_name}</strong>
                    <div style={styles.smallMeta}>Dr. {c.doctor_name} · {c.status} · {consultationBillingLabel(c)}</div>
                  </div>
                ))}
                {!consultations.length ? <p style={styles.subtitle}>No consultations yet.</p> : null}
              </div>
              <div style={styles.reportPanel}>
                <h4 style={styles.subheading}>Recharge Requests</h4>
                {(finance?.recent_recharge_requests || []).slice(0, 8).map((req) => (
                  <div key={req.id} style={styles.timelineItem}>
                    <strong>Rs {req.amount}</strong>
                    <div style={styles.smallMeta}>{req.status}{req.reference_note ? ` · ${req.reference_note}` : ""}</div>
                  </div>
                ))}
                {!(finance?.recent_recharge_requests || []).length ? <p style={styles.subtitle}>No recharge requests yet.</p> : null}
              </div>
            </div>
          </section>
        )}

        {showPatientModal ? (
          <div style={styles.modalBackdrop}>
            <div style={styles.modal}>
              <div style={styles.modalHeader}>
                <h3 style={styles.sectionTitle}>Add TMC Patient</h3>
                <button type="button" style={styles.secondaryButton} onClick={() => setShowPatientModal(false)}>Close</button>
              </div>
              {patientMsg ? (
                <div style={patientMsg.includes("added") ? styles.successNotice : styles.errorNotice}>
                  {patientMsg}
                  <button type="button" style={styles.dismissBtn} onClick={() => setPatientMsg("")}>×</button>
                </div>
              ) : null}
              <form onSubmit={submitPatient} style={styles.patientCreateGrid}>
                <input style={styles.input} placeholder="Patient full name" value={patientForm.name} onChange={(e) => setPatientForm({ ...patientForm, name: e.target.value })} required />
                <input style={styles.input} type="number" min="0" max="120" placeholder="Age" value={patientForm.age} onChange={(e) => setPatientForm({ ...patientForm, age: e.target.value })} required />
                <select style={styles.input} value={patientForm.gender} onChange={(e) => setPatientForm({ ...patientForm, gender: e.target.value })}>
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                  <option value="O">Other</option>
                </select>
                <button type="submit" disabled={patientSaving} style={styles.primaryButton}>{patientSaving ? "Adding..." : "Save Patient"}</button>
              </form>
            </div>
          </div>
        ) : null}

        {chatConsultation ? (
          <ConsultationDetailModal
            consultation={chatConsultation}
            events={chatEvents}
            onClose={() => setChatConsultation(null)}
            viewerRole="tmc"
          >
            {chatStatus === "COMPLETED" ? (
              <div style={styles.followUpBox}>
                <div>
                  <strong style={{ color: "#123a6f" }}>Need to ask the doctor again for this TMC patient?</strong>
                  <p style={styles.muted}>
                    {chatConsultation.follow_up?.next_is_billable
                      ? "This follow-up is outside the free allowance and will be charged from the TMC wallet before it is sent."
                      : `Free follow-ups remaining: ${chatConsultation.follow_up?.free_remaining ?? 0}`}
                  </p>
                  {followUpMsg ? <p style={styles.followUpMessage}>{followUpMsg}</p> : null}
                </div>
                <button
                  type="button"
                  style={styles.primaryButton}
                  disabled={followUpBusy || !chatConsultation.follow_up?.can_request}
                  onClick={() => requestTMCFollowUp(chatConsultation)}
                >
                  {chatConsultation.follow_up?.active_status === "PENDING"
                    ? "Request pending"
                    : chatConsultation.follow_up?.next_is_billable
                      ? "Paid follow-up"
                      : "Resume chat"}
                </button>
              </div>
            ) : followUpMsg ? (
              <p style={styles.followUpMessage}>{followUpMsg}</p>
            ) : null}
            <ConsultationChatPanel
              consultationId={chatConsultation.id}
              status={chatStatus}
              pollMs={5000}
            />
          </ConsultationDetailModal>
        ) : null}
        </main>
        <Footer />
      </div>
    </div>
  );
};

const Card = ({ label, value }) => (
  <article style={styles.card}>
    <div style={styles.cardLabel}>{label}</div>
    <div style={styles.cardValue}>{value}</div>
  </article>
);

const DoctorSearchCard = ({ doctor, selected, onSelect }) => {
  const modes = Array.isArray(doctor.consultation_modes) ? doctor.consultation_modes : [];
  const location = [doctor.city, doctor.state].filter(Boolean).join(", ");

  return (
    <article style={selected ? styles.doctorCardSelected : styles.doctorCard}>
      <div style={styles.doctorCardTop}>
        <div style={styles.doctorAvatar}>
          {doctor.photo ? (
            <img src={doctor.photo} alt="" style={styles.doctorPhoto} />
          ) : (
            <span>{`${doctor.first_name || "D"}`.slice(0, 1)}</span>
          )}
        </div>
        <div>
          <strong>Dr. {doctor.first_name} {doctor.last_name}</strong>
          <div style={styles.smallMeta}>{doctor.specialty || "General Physician"}</div>
        </div>
      </div>
      <div style={styles.doctorDetails}>
        <span>{doctor.qualification || "Qualification not listed"}</span>
        <span>{doctor.experience || "Experience not listed"}</span>
        <span>{doctor.hospital_or_clinic_name || "Clinic not listed"}</span>
        <span>{location || "Location not listed"}</span>
      </div>
      <div style={styles.cardFooterRow}>
        <span style={styles.feePill}>{doctor.consultation_fee ? `Rs ${doctor.consultation_fee}` : "Fee not set"}</span>
        {modes.slice(0, 2).map((mode) => (
          <span key={mode} style={styles.modePill}>{mode}</span>
        ))}
        <button type="button" style={selected ? styles.selectedButton : styles.primaryButton} onClick={onSelect}>
          {selected ? "Selected" : "Select Doctor"}
        </button>
      </div>
    </article>
  );
};

const genderLabel = (value) => {
  if (value === "M") return "Male";
  if (value === "F") return "Female";
  if (value === "O") return "Other";
  return "Sex not set";
};

const styles = {
  page: {
    minHeight: "100vh",
    background: "linear-gradient(180deg, #eef5fb 0%, #f8fbfe 46%, #eef4f8 100%)",
    color: "#10243e",
    fontFamily: "Segoe UI, system-ui, sans-serif",
    display: "flex",
    flexDirection: "column",
  },
  main: { flex: 1 },
  heroPanel: {
    background: "linear-gradient(135deg, #002043 0%, #0f4c81 62%, #14b8a6 100%)",
    color: "#fff",
    borderRadius: 18,
    padding: 20,
    display: "flex",
    justifyContent: "space-between",
    gap: 18,
    flexWrap: "wrap",
    boxShadow: "0 18px 45px rgba(0, 32, 67, 0.22)",
  },
  kicker: { display: "block", fontSize: 12, fontWeight: 800, letterSpacing: 0, textTransform: "uppercase", opacity: 0.82, marginBottom: 6 },
  title: { margin: "0 0 6px", color: "#fff", fontSize: "clamp(1.5rem, 3vw, 2.2rem)", lineHeight: 1.12 },
  heroCopy: { color: "rgba(255,255,255,0.86)", margin: 0, maxWidth: 620, fontSize: 15 },
  heroStats: { display: "grid", gridTemplateColumns: "repeat(3, minmax(96px, 1fr))", gap: 10, alignSelf: "stretch" },
  heroStat: {
    minWidth: 96,
    border: "1px solid rgba(255,255,255,0.2)",
    background: "rgba(255,255,255,0.12)",
    borderRadius: 12,
    padding: 12,
    display: "grid",
    alignContent: "center",
    gap: 2,
  },
  subtitle: { color: "#4c6480", marginTop: 4 },
  muted: { color: "#4c6480", fontSize: 13, margin: "4px 0" },
  sectionMenu: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
    gap: 10,
    margin: "16px 0",
  },
  sectionMenuItem: {
    textAlign: "left",
    border: "1px solid #d7e5f5",
    background: "rgba(255,255,255,0.88)",
    color: "#10243e",
    borderRadius: 12,
    padding: 12,
    cursor: "pointer",
    display: "grid",
    gap: 4,
    boxShadow: "0 8px 20px rgba(0,32,67,0.06)",
  },
  sectionMenuActive: {
    textAlign: "left",
    border: "1px solid #1762bf",
    background: "#e8f4ff",
    color: "#10243e",
    borderRadius: 12,
    padding: 12,
    cursor: "pointer",
    display: "grid",
    gap: 4,
    boxShadow: "0 6px 14px rgba(23,98,191,0.14)",
  },
  cards: { display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: 12, margin: "16px 0" },
  card: { background: "#fff", border: "1px solid #d7e5f5", borderRadius: 12, padding: 14, boxShadow: "0 6px 14px rgba(0,0,0,0.06)" },
  cardLabel: { color: "#4c6480", fontSize: 12, fontWeight: 700 },
  cardValue: { color: "#113864", fontSize: 24, fontWeight: 800 },
  section: { background: "rgba(255,255,255,0.94)", border: "1px solid #e0ebf6", borderRadius: 16, padding: 18, boxShadow: "0 14px 34px rgba(0,32,67,0.08)", marginTop: 14 },
  sectionHeader: { display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", flexWrap: "wrap" },
  sectionTitle: { marginTop: 0, color: "#123a6f" },
  subheading: { color: "#123a6f", margin: "18px 0 10px" },
  form: { display: "grid", gap: 10, alignItems: "end" },
  rechargeForm: { display: "grid", gap: 10, alignItems: "end" },
  input: { height: 42, borderRadius: 10, border: "1px solid #c6d7eb", padding: "0 12px", fontSize: 14, boxSizing: "border-box", background: "#fbfdff" },
  searchInput: { height: 44, borderRadius: 12, border: "1px solid #c6d7eb", padding: "0 14px", fontSize: 14, boxSizing: "border-box", background: "#fbfdff", minWidth: 0 },
  primaryButton: { background: "#1762bf", color: "#fff", border: "none", borderRadius: 8, padding: "8px 12px", fontWeight: 700, cursor: "pointer" },
  secondaryButton: { background: "#edf4fd", color: "#174577", border: "1px solid #8ab0dc", borderRadius: 8, padding: "6px 10px", cursor: "pointer", fontWeight: 700 },
  notice: { background: "#edf7ee", border: "1px solid #b7dcbc", color: "#185a2b", borderRadius: 8, padding: 10, margin: "8px 0 12px" },
  lockNotice: { background: "#fff7e6", border: "1px solid #f0c36d", color: "#7a4b00", borderRadius: 8, padding: 10, margin: "8px 0 12px" },
  successNotice: { background: "#eef8f2", border: "1px solid #acd9bf", color: "#123a2a", borderRadius: 8, padding: "10px 12px", margin: "8px 0 12px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 },
  errorNotice: { background: "#fdeeee", border: "1px solid #efb4b4", color: "#711f1f", borderRadius: 8, padding: "10px 12px", margin: "8px 0 12px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 },
  dismissBtn: { background: "rgba(255,255,255,0.75)", border: "1px solid rgba(18,58,111,0.2)", borderRadius: 6, width: 24, height: 24, fontWeight: 800, cursor: "pointer", fontSize: 16, lineHeight: "20px" },
  followUpBox: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
    flexWrap: "wrap",
    background: "#eefaf4",
    border: "1px solid #b9dfc9",
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
  },
  followUpMessage: { margin: "4px 0 0", color: "#17623c", fontSize: 13, fontWeight: 700 },
  profileGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10, alignItems: "end" },
  qualificationGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 10, alignItems: "end", marginBottom: 12 },
  patientCreateGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 10, alignItems: "end", marginBottom: 14 },
  patientGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10, marginTop: 12 },
  personCard: { border: "1px solid #d7e5f5", borderRadius: 12, padding: 12, background: "#fbfdff", display: "grid", gap: 6 },
  selectionGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 14, marginBottom: 14 },
  finderPanel: { border: "1px solid #d7e5f5", background: "#f8fbfe", borderRadius: 14, padding: 14, minWidth: 0 },
  finderHeader: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, marginBottom: 10 },
  toolbarRow: { display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginTop: 10 },
  actionGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: 12 },
  actionCard: { textAlign: "left", border: "1px solid #d7e5f5", borderRadius: 12, background: "#fbfdff", padding: 14, display: "grid", gap: 6, cursor: "pointer", color: "#10243e" },
  consultForm: { display: "grid", gridTemplateColumns: "minmax(220px, 1fr) auto", gap: 10, alignItems: "end" },
  searchRow: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 8 },
  optionList: { display: "grid", gap: 8, marginTop: 8, maxHeight: 300, overflowY: "auto" },
  optionButton: { textAlign: "left", border: "1px solid #d7e5f5", background: "#fff", borderRadius: 10, padding: 10, cursor: "pointer", display: "grid", gap: 4, color: "#10243e" },
  optionActive: { textAlign: "left", border: "1px solid #1762bf", background: "#edf4fd", borderRadius: 10, padding: 10, cursor: "pointer", display: "grid", gap: 4, color: "#10243e", boxShadow: "0 8px 18px rgba(23,98,191,0.12)" },
  doctorResultGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 10, marginTop: 10, maxHeight: 430, overflowY: "auto", paddingRight: 4 },
  doctorCard: { border: "1px solid #d7e5f5", background: "#fff", borderRadius: 14, padding: 12, display: "grid", gap: 10, boxShadow: "0 8px 20px rgba(0,32,67,0.05)" },
  doctorCardSelected: { border: "1px solid #1762bf", background: "#edf7ff", borderRadius: 14, padding: 12, display: "grid", gap: 10, boxShadow: "0 10px 24px rgba(23,98,191,0.16)" },
  doctorCardTop: { display: "grid", gridTemplateColumns: "44px minmax(0, 1fr)", gap: 10, alignItems: "center" },
  doctorAvatar: { width: 44, height: 44, borderRadius: 12, background: "#dbeafe", color: "#123a6f", display: "grid", placeItems: "center", fontWeight: 800, overflow: "hidden" },
  doctorPhoto: { width: "100%", height: "100%", objectFit: "cover" },
  doctorDetails: { display: "grid", gap: 4, color: "#4c6480", fontSize: 13 },
  cardFooterRow: { display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" },
  feePill: { borderRadius: 999, background: "#e8f4ff", color: "#123a6f", padding: "4px 8px", fontSize: 12, fontWeight: 800 },
  modePill: { borderRadius: 999, background: "#e9fbf7", color: "#0d6e64", padding: "4px 8px", fontSize: 12, fontWeight: 700 },
  selectedButton: { background: "#0d6e64", color: "#fff", border: "none", borderRadius: 8, padding: "8px 12px", fontWeight: 700, cursor: "pointer" },
  emptyState: { border: "1px dashed #b7cbe3", borderRadius: 12, background: "#f7fbff", color: "#4c6480", padding: 14, display: "grid", gap: 8 },
  modalBackdrop: { position: "fixed", inset: 0, background: "rgba(5,20,36,0.45)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 2000, padding: 16 },
  modal: { width: "min(560px, 100%)", background: "#fff", borderRadius: 10, border: "1px solid #c6d7eb", boxShadow: "0 18px 50px rgba(0,0,0,0.25)", padding: 16 },
  modalHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, marginBottom: 12 },
  fileLabel: {
    minHeight: 40,
    borderRadius: 8,
    border: "1px dashed #8ab0dc",
    padding: "8px 10px",
    display: "flex",
    flexDirection: "column",
    gap: 6,
    color: "#174577",
    fontSize: 12,
    fontWeight: 700,
    boxSizing: "border-box",
  },
  documentLinks: { display: "flex", gap: 12, flexWrap: "wrap", marginTop: 12 },
  tableWrap: { overflowX: "auto" },
  table: { width: "100%", borderCollapse: "collapse" },
  tableActions: { display: "flex", gap: 8, flexWrap: "wrap" },
  badge: { display: "inline-block", borderRadius: 14, background: "#e6f0fb", color: BRAND_NAVY, padding: "2px 8px", fontSize: 12, fontWeight: 700 },
  timeline: { listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 8 },
  timelineItem: { border: "1px solid #d7e5f5", borderRadius: 10, padding: 10, background: "#fbfdff" },
  requestList: { display: "grid", gap: 8, marginTop: 12 },
  smallMeta: { color: "#4c6480", fontSize: 12, marginTop: 4 },
  reportSplit: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 12 },
  reportPanel: { border: "1px solid #d7e5f5", borderRadius: 8, padding: 12, background: "#fbfdff" },
  consultationList: { display: "grid", gap: 12, marginTop: 12 },
  consultationCard: { border: "1px solid #d7e5f5", borderRadius: 12, padding: 14, background: "#fbfdff", display: "grid", gap: 10 },
  consultationHeader: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 },
  consultationTitle: { color: "#123a6f", fontSize: 15 },
  consultationMeta: { color: "#4c6480", fontSize: 13, marginTop: 4 },
  statusMessage: { color: "#10243e", fontSize: 14, padding: "8px 12px", background: "#f0f7ff", borderRadius: 8, border: "1px solid #c6d7eb" },
  postponedNote: { background: "#fff7e6", border: "1px solid #f0c36d", borderRadius: 8, padding: 10, fontSize: 13, color: "#7a4b00" },
  followUpIndicator: { background: "#e8f4ff", border: "1px solid #8ab0dc", borderRadius: 8, padding: 8, fontSize: 13, color: "#123a6f", fontWeight: 700 },
  cardActions: { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 4 },
};

export default TMCDashboard;
