import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import axios from "axios";
import Header from "../../../components/Header";
import PatientBookingReview from "../../../components/dashboard/PatientBookingReview";
import PostponementOutcome, { postponementOutcome } from "../../../components/dashboard/PostponementOutcome";
import Footer from "../../../components/Footer";
import Sidebar from "../../../components/Sidebar";
import StatusBadge from "../../../components/dashboard/StatusBadge";
import ConsultationDetailModal from "../../../components/dashboard/ConsultationDetailModal";
import ConsultationChatPanel from "../../../components/dashboard/ConsultationChatPanel";
import { getStatusMessage } from "../../../utils/consultationStatus";
import { StaleNotification } from "../../../components/dashboard/InlineNotification";
import {
  getUserProfile,
  patchUserProfile,
  getPatientConsultationHistory,
  getActiveConsultation,
  patientRespondToConsultation,
  getConsultationEvents,
  getPrescription,
  downloadPrescriptionPdf,
  getPatientWalletSummary,
  createPatientWalletRechargeRequest,
  createPatientWalletRazorpayOrder,
  verifyPatientWalletRazorpayPayment,
  cancelPatientWalletRechargeRequest,
  requestConsultationFollowUp,
  respondConsultationVideo,
} from "../../../api/users";
import { API_BASE_URL } from "../../../api/config";
import { dashboardContentMarginLeft } from "../../../constants/dashboardLayout";
import {
  DASHBOARD_BORDER,
  DASHBOARD_PAGE_BG,
  DASHBOARD_SECTION_BG,
  DASHBOARD_SHADOW,
} from "../../../constants/brandTheme";
import { getAccessToken } from "../../../utils/authSession";

/** Flatten DRF validation errors for patient-facing messages */
function formatBookingError(err) {
  const data = err?.response?.data;
  if (!data || typeof data !== "object") {
    return err?.message || "Could not start consultation.";
  }
  if (typeof data.wallet === "string") return data.wallet;
  if (Array.isArray(data.wallet) && data.wallet.length) return data.wallet.join(" ");
  if (typeof data.consultation === "string") return data.consultation;
  if (Array.isArray(data.consultation) && data.consultation.length) return data.consultation.join(" ");
  if (typeof data.doctor === "string") return data.doctor;
  if (typeof data.patient === "string") return data.patient;
  if (typeof data.doctor_id === "string") return data.doctor_id;
  if (typeof data.detail === "string") return data.detail;
  const parts = [];
  Object.entries(data).forEach(([key, val]) => {
    if (typeof val === "string") parts.push(val);
    else if (Array.isArray(val)) parts.push(`${key}: ${val.join(", ")}`);
    else if (val && typeof val === "object") {
      Object.values(val).forEach((iv) => {
        if (typeof iv === "string") parts.push(iv);
        else if (Array.isArray(iv)) parts.push(iv.join(", "));
      });
    }
  });
  return parts.length ? parts.join(" ") : "Could not start consultation.";
}

function loadRazorpayCheckout() {
  return new Promise((resolve, reject) => {
    if (window.Razorpay) {
      resolve();
      return;
    }
    const existing = document.querySelector('script[src="https://checkout.razorpay.com/v1/checkout.js"]');
    if (existing) {
      existing.addEventListener("load", resolve, { once: true });
      existing.addEventListener("error", () => reject(new Error("Could not load Razorpay checkout.")), { once: true });
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = resolve;
    script.onerror = () => reject(new Error("Could not load Razorpay checkout."));
    document.head.appendChild(script);
  });
}

const PAGE_TITLES = {
  "/dashboard/patient": "Patient dashboard",
  "/patient/profile": "Your profile",
  "/patient/book": "Book a consultation",
  "/patient/history": "Consultation history",
  "/patient/change-password": "Account security",
};

const followUpStatusLabel = (consultation) => {
  const status = consultation?.follow_up?.active_status;
  if (status === "PENDING") return "Follow-up pending with doctor";
  if (status === "IN_PROGRESS") return "Follow-up accepted / live";
  if (status === "COMPLETED") return "Follow-up completed";
  if (status === "REJECTED") return "Follow-up rejected";
  return null;
};

const followUpHelperText = (consultation) => {
  const status = consultation?.follow_up?.active_status;
  if (status === "PENDING") {
    return "Follow-up request is with the doctor. The doctor must start it before chat/video can resume.";
  }
  if (status === "IN_PROGRESS") {
    return "Follow-up accepted by the doctor. Open history to continue chat or join video when requested.";
  }
  if (status === "REJECTED") {
    return "The doctor rejected this follow-up request.";
  }
  return "Completed consultation. You can request a follow-up when needed.";
};

const followUpButtonText = (consultation) => {
  const status = consultation?.follow_up?.active_status;
  if (status === "PENDING") return "Follow-up pending";
  if (status === "IN_PROGRESS") return "Follow-up accepted";
  if (consultation?.follow_up?.next_is_billable) return "Consult again";
  return "Resume chat";
};

const followUpEmphasis = (consultation) => {
  const status = consultation?.follow_up?.active_status;
  if (status === "PENDING") return "waiting";
  if (status === "IN_PROGRESS") return "live";
  if (status === "REJECTED") return "urgent";
  return undefined;
};

const PatientDashboardRefined = () => {
  const location = useLocation();
  const path = location.pathname;

  const [doctors, setDoctors] = useState([]);
  const [consultations, setConsultations] = useState([]);
  const [active, setActive] = useState(null);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState(null);
  const [events, setEvents] = useState([]);
  const [prescriptionMap, setPrescriptionMap] = useState({});
  const [search, setSearch] = useState("");
  const [specialtyFilter, setSpecialtyFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [wallet, setWallet] = useState(null);
  const [walletRechargeForm, setWalletRechargeForm] = useState({ amount: "", reference_note: "" });
  const [walletRechargeMsg, setWalletRechargeMsg] = useState("");
  const [walletRechargeSaving, setWalletRechargeSaving] = useState(false);
  const [walletExpanded, setWalletExpanded] = useState(false);
  const [bookingReview, setBookingReview] = useState(null);
  const paymentReviewRef = useRef(null);

  useEffect(() => {
    if (bookingReview) paymentReviewRef.current?.scrollIntoView?.({ behavior: "smooth", block: "center" });
  }, [bookingReview]);
  const [bookError, setBookError] = useState("");
  const [notice, setNotice] = useState(null);
  const [followUpMsg, setFollowUpMsg] = useState("");
  const [isStale, setIsStale] = useState(false);
  const consultationStatusRef = useRef(new Map());
  const statusReadyRef = useRef(false);
  const selectedIdRef = useRef(null);
  const mountedRef = useRef(true);

  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    () => typeof window !== "undefined" && window.innerWidth < 768
  );
  const [winW, setWinW] = useState(() => (typeof window !== "undefined" ? window.innerWidth : 1200));

  const [profileUser, setProfileUser] = useState(null);
  const [profileForm, setProfileForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone_number: "",
    gender: "M",
    age: "",
    address: "",
  });
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMsg, setProfileMsg] = useState(null);

  const isNarrow = winW < 768;

  const showNotice = useCallback((type, title, body) => {
    setNotice({ type, title, body, id: Date.now() });
  }, []);

  const statusNoticeFor = useCallback((consultation) => {
    const rejected = postponementOutcome(consultation);
    if (rejected) return { type: "warning", ...rejected };
    const doctor = consultation.doctor_name || "the doctor";
    if (consultation.status === "ACCEPTED") {
      return {
        type: "success",
        title: "Doctor accepted your request",
        body: `${doctor} accepted the consultation. Please stay ready while the doctor starts the session.`,
      };
    }
    if (consultation.status === "QUEUED") {
      return {
        type: "success",
        title: "You are in the doctor's queue",
        body: `${doctor} accepted your request. Queue number: ${consultation.queue_number || "-"}.`,
      };
    }
    if (consultation.status === "IN_PROGRESS") {
      return {
        type: "success",
        title: "Consultation started",
        body: `${doctor} started the consultation. Open the chat/details panel to continue.`,
      };
    }
    if (consultation.status === "POSTPONED") {
      return {
        type: "warning",
        title: "Doctor suggested another time",
        body: `${doctor} proposed ${consultation.formatted_suggested_time || "a new time"}. Please accept or reject it.`,
      };
    }
    if (consultation.status === "REJECTED") {
      return {
        type: "error",
        title: "Doctor rejected the request",
        body: `${doctor} could not accept this consultation. You can request another available doctor.`,
      };
    }
    if (consultation.status === "COMPLETED" || consultation.is_completed) {
      return {
        type: "success",
        title: "Consultation completed",
        body: `${doctor} marked this consultation as completed.`,
      };
    }
    return null;
  }, []);

  const refresh = useCallback(async () => {
    const currentSelectedId = selectedIdRef.current;
    try {
      const [docs, history, current] = await Promise.all([
        axios.get(`${API_BASE_URL}/consultations/available-doctors/`),
        getPatientConsultationHistory(),
        getActiveConsultation(),
      ]);
      const walletData = await getPatientWalletSummary();
      
      if (!mountedRef.current) return;
      
      const historyList = Array.isArray(history) ? history : [];
      const currentConsultation = current && !Array.isArray(current) && current.id ? current : null;
      const statusSnapshot = new Map();
      [currentConsultation, ...historyList].filter(Boolean).forEach((consultation) => {
        statusSnapshot.set(consultation.id, consultation.status);
        const previousStatus = consultationStatusRef.current.get(consultation.id);
        if (statusReadyRef.current && previousStatus && previousStatus !== consultation.status) {
          const update = statusNoticeFor(consultation);
          if (update) showNotice(update.type, update.title, update.body);
        }
      });
      consultationStatusRef.current = statusSnapshot;
      statusReadyRef.current = true;
      setDoctors(Array.isArray(docs.data) ? docs.data : []);
      setConsultations(historyList);
      setActive(currentConsultation);
      setWallet(walletData);
      setIsStale(false);
      
      setSelected((prev) => {
        if (!prev?.id || selectedIdRef.current !== currentSelectedId) return prev;
        const updated = [currentConsultation, ...historyList].filter(Boolean).find((c) => c.id === prev.id);
        return updated && selectedIdRef.current === prev.id ? { ...prev, ...updated } : prev;
      });
    } catch (err) {
      if (mountedRef.current) {
        setIsStale(true);
      }
      throw err;
    }
  }, [showNotice, statusNoticeFor]);

  const loadProfileOnly = useCallback(async () => {
    setProfileMsg(null);
    try {
      const data = await getUserProfile();
      const u = data.user || {};
      const p = data.profile || {};
      setProfileUser(u);
      setProfileForm({
        first_name: u.first_name || "",
        last_name: u.last_name || "",
        email: u.email || "",
        phone_number: u.phone_number || "",
        gender: p.gender || "M",
        age: p.age != null ? String(p.age) : "",
        address: p.address || "",
      });
    } catch (e) {
      setProfileMsg(e?.message || "Could not load profile.");
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
    if (path === "/patient/profile") {
      loadProfileOnly();
      return undefined;
    }
    if (path === "/patient/change-password") {
      return undefined;
    }
    refresh().catch(() => {});
    const t = setInterval(() => refresh().catch(() => {}), 8000);
    return () => clearInterval(t);
  }, [path, refresh, loadProfileOnly]);

  useEffect(() => {
    if (!notice) return undefined;
    const timer = setTimeout(() => setNotice(null), 7000);
    return () => clearTimeout(timer);
  }, [notice]);

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
    const specialtyQ = specialtyFilter.trim().toLowerCase();
    const locationQ = locationFilter.trim().toLowerCase();
    return doctors.filter((d) => {
      const full = [
        d.first_name,
        d.last_name,
        d.specialty,
        d.qualification,
        d.hospital_or_clinic_name,
        d.city,
        d.state,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      const locationText = `${d.city || ""} ${d.state || ""}`.toLowerCase();
      return (
        (!q || full.includes(q)) &&
        (!specialtyQ || String(d.specialty || "").toLowerCase().includes(specialtyQ)) &&
        (!locationQ || locationText.includes(locationQ))
      );
    });
  }, [search, specialtyFilter, locationFilter, doctors]);

  const videoActionConsultation = useMemo(
    () => [active, ...consultations].filter(Boolean).find((c) => c.video?.status === "REQUESTED"),
    [active, consultations]
  );

  const respondToVideoRequest = async (consultation, action) => {
    setBusy(true);
    try {
      await respondConsultationVideo(consultation.id, action);
      await refresh();
      showNotice(
        action === "accept" ? "success" : "warning",
        action === "accept" ? "Video request accepted" : "Video request rejected",
        action === "accept"
          ? "The video room is ready. Open the consultation and join when your camera and mic are ready."
          : "The doctor has been notified that you are not ready for video."
      );
      if (action === "accept") {
        await openDetails({ ...consultation, video: { ...(consultation.video || {}), status: "ACCEPTED" } });
      }
    } catch (err) {
      showNotice("error", "Video response failed", err?.response?.data?.error || err?.message || "Could not respond to video request.");
    } finally {
      setBusy(false);
    }
  };

  const reviewConsultation = async (doctor) => {
    const doctorId = typeof doctor === "object" ? doctor.id : doctor;
    const doctorCard = typeof doctor === "object" ? doctor : doctors.find((d) => String(d.id) === String(doctorId));
    setBusy(true);
    setBookError("");
    setBookingReview(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/consultations/book-consultation/preview/`, {
        params: { doctor_id: doctorId }, headers: { Authorization: `Bearer ${getAccessToken()}` },
      });
      setBookingReview({ ...response.data, doctor: doctorCard || null });
    } catch (err) {
      setBookError(formatBookingError(err));
    } finally {
      setBusy(false);
    }
  };

  const requestConsultation = async (doctorId, expectedTotal) => {
    setBusy(true);
    setBookError("");
    setNotice(null);
    try {
      await axios.post(
        `${API_BASE_URL}/consultations/book-consultation/`,
        { doctor_id: doctorId, consultation_type: "DIRECT", expected_total: expectedTotal },
        { headers: { Authorization: `Bearer ${getAccessToken()}` } }
      );
      const doctor = doctors.find((d) => String(d.id) === String(doctorId));
      const doctorName = doctor ? `Dr. ${doctor.first_name || ""} ${doctor.last_name || ""}`.trim() : "the selected doctor";
      await refresh();
      setBookingReview(null);
      showNotice(
        "success",
        "Consultation request sent",
        `Your request has been sent to ${doctorName}. Please wait for the doctor to accept, reject, or suggest another time.`
      );
    } catch (err) {
      setBookError(formatBookingError(err));
      setBookingReview(null);
      showNotice("error", "Could not send request", formatBookingError(err));
    } finally {
      setBusy(false);
    }
  };

  const openDetails = async (consultation) => {
    selectedIdRef.current = consultation.id;
    setSelected(consultation);
    const [timeline, rx] = await Promise.all([
      getConsultationEvents(consultation.id, { order: "asc" }),
      getPrescription(consultation.id),
    ]);
    if (selectedIdRef.current !== consultation.id) return;
    setEvents(Array.isArray(timeline) ? timeline : []);
    setPrescriptionMap((prev) => ({ ...prev, [consultation.id]: rx }));
  };

  const requestFollowUp = async (consultation) => {
    setBusy(true);
    setFollowUpMsg("");
    try {
      const result = await requestConsultationFollowUp(consultation.id);
      setFollowUpMsg(
        result.is_billable
          ? `Follow-up request sent. Rs ${result.amount_charged} has been charged.`
          : "Follow-up request sent to the doctor."
      );
      await refresh();
      await openDetails({
        ...consultation,
        follow_up: { ...(consultation.follow_up || {}), active_status: "PENDING", can_request: false },
      });
    } catch (err) {
      setFollowUpMsg(err?.message || "Could not request follow-up.");
    } finally {
      setBusy(false);
    }
  };

  const saveProfile = async (e) => {
    e.preventDefault();
    setProfileSaving(true);
    setProfileMsg(null);
    try {
      const payload = {
        first_name: profileForm.first_name,
        last_name: profileForm.last_name,
        email: profileForm.email,
        phone_number: profileForm.phone_number,
        gender: profileForm.gender,
        address: profileForm.address,
      };
      if (profileForm.age !== "" && !Number.isNaN(parseInt(profileForm.age, 10))) {
        payload.age = parseInt(profileForm.age, 10);
      }
      const data = await patchUserProfile(payload);
      if (data.user) setProfileUser(data.user);
      setProfileMsg("Profile saved.");
    } catch (err) {
      setProfileMsg(err?.message || "Save failed.");
    } finally {
      setProfileSaving(false);
    }
  };

  const contentMarginLeft = dashboardContentMarginLeft(isNarrow, sidebarCollapsed);

  const submitWalletRecharge = async (e) => {
    e.preventDefault();
    setWalletRechargeMsg("");
    setWalletRechargeSaving(true);
    let rechargeRequestId = null;
    try {
      const requestData = await createPatientWalletRechargeRequest(walletRechargeForm);
      rechargeRequestId = requestData.id;
      const order = await createPatientWalletRazorpayOrder(rechargeRequestId);
      if (order.razorpay_enabled && order.key_id && order.order_id) {
        await loadRazorpayCheckout();
        let completed = false;
        await new Promise((resolve, reject) => {
          const checkout = new window.Razorpay({
            key: order.key_id,
            amount: order.amount_paise || Math.round(Number(order.amount || 0) * 100),
            currency: order.currency || "INR",
            name: "IRME Telemedicine",
            description: "Patient wallet recharge",
            order_id: order.order_id,
            handler: async (response) => {
              try {
                await verifyPatientWalletRazorpayPayment(rechargeRequestId, response);
                completed = true;
                resolve();
              } catch (err) {
                reject(err);
              }
            },
            modal: {
              ondismiss: async () => {
                if (!completed) {
                  try {
                    await cancelPatientWalletRechargeRequest(rechargeRequestId);
                  } catch (cancelErr) {
                    // The refresh below will still show the latest server state.
                  }
                  reject(new Error("Transaction was cancelled. No amount was added to the wallet."));
                }
              },
            },
          });
          checkout.open();
        });
        setWalletRechargeMsg("Payment successful. Patient wallet credited.");
      } else {
        await cancelPatientWalletRechargeRequest(rechargeRequestId);
        setWalletRechargeMsg("Razorpay is not configured. No pending recharge was created.");
      }
      setWalletRechargeForm({ amount: "", reference_note: "" });
      await refresh();
    } catch (err) {
      if (rechargeRequestId) {
        await cancelPatientWalletRechargeRequest(rechargeRequestId).catch(() => {});
      }
      setWalletRechargeMsg(err?.response?.data?.error || err.message || "Transaction was cancelled. No amount was added to the wallet.");
      await refresh().catch(() => {});
    } finally {
      setWalletRechargeSaving(false);
    }
  };

  const renderWalletAndOverview = () => (
    <>
      <section id="patient-balance" style={styles.walletCompact}>
        <div>
          <h3 style={styles.compactTitle}>Wallet</h3>
          <div style={styles.walletSummaryRow}>
            <strong style={styles.walletBalance}>Rs {wallet?.balance || "0.00"}</strong>
            <span style={styles.walletMiniText}>Credited: Rs {wallet?.total_credited || "0.00"}</span>
            <span style={styles.walletMiniText}>Debited: Rs {wallet?.total_debited || "0.00"}</span>
          </div>
        </div>
        <div style={styles.rowActions}>
          <button type="button" style={styles.primaryBtn} onClick={() => setWalletExpanded((v) => !v)}>
            {walletExpanded ? "Hide wallet" : "Add funds / history"}
          </button>
        </div>
        {walletRechargeMsg ? <div style={styles.inlineNotice}>{walletRechargeMsg}</div> : null}
        {walletExpanded ? (
          <div style={styles.walletExpandedArea}>
            <form onSubmit={submitWalletRecharge} style={styles.walletRechargeForm}>
              <input
                style={styles.input}
                type="number"
                min="1"
                step="0.01"
                required
                placeholder="Amount to add"
                value={walletRechargeForm.amount}
                onChange={(e) => setWalletRechargeForm({ ...walletRechargeForm, amount: e.target.value })}
              />
              <input
                style={styles.input}
                placeholder="Payment note / reference"
                value={walletRechargeForm.reference_note}
                onChange={(e) => setWalletRechargeForm({ ...walletRechargeForm, reference_note: e.target.value })}
              />
              <button type="submit" disabled={walletRechargeSaving} style={styles.primaryBtn}>
                {walletRechargeSaving ? "Creating..." : "Add Funds"}
              </button>
            </form>
            <p style={styles.walletNote}>
              Online recharge opens Razorpay checkout. Your administrator can also record an approved manual credit. All credits appear in your payment history.
            </p>
            <div style={styles.walletHistoryGrid}>
              <div>
                {(wallet?.recent_recharge_requests || []).slice(0, 2).map((req) => (
                  <div key={req.id} style={styles.compactWalletRow}>
                    <div>
                      <div style={styles.rowTitle}>Recharge Rs {req.amount}</div>
                      <div style={styles.rowMeta}>{req.status} - {req.provider}</div>
                    </div>
                    <span style={styles.badgeSoft}>{req.status}</span>
                  </div>
                ))}
              </div>
              <div>
                {(wallet?.recent_entries || []).slice(0, 2).map((entry) => (
                  <div key={entry.id} style={styles.compactWalletRow}>
                    <div>
                      <div style={styles.rowTitle}>{entry.entry_type}</div>
                      <div style={styles.rowMeta}>{entry.description || "Wallet entry"}</div>
                    </div>
                    <strong style={{ color: "#123a6f" }}>Rs {entry.amount}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </section>
    </>
  );

  const renderActiveConsultationSection = () => (
    <>
      {videoActionConsultation ? (
        <section style={styles.actionPanel} role="alert" aria-live="assertive">
          <div>
            <div style={styles.actionEyebrow}>Action needed now</div>
            <h3 style={styles.actionTitle}>Doctor requested a video call</h3>
            <p style={styles.actionText}>
              Dr. {videoActionConsultation.doctor_name || "Doctor"} is asking to start video for consultation #{videoActionConsultation.id}.
              Accept to open the video room, or reject if you are not ready.
            </p>
          </div>
          <div style={styles.actionButtons}>
            <button type="button" style={styles.primaryBtn} disabled={busy} onClick={() => respondToVideoRequest(videoActionConsultation, "accept")}>
              Accept video
            </button>
            <button type="button" style={styles.warnBtn} disabled={busy} onClick={() => respondToVideoRequest(videoActionConsultation, "reject")}>
              Reject
            </button>
            <button type="button" style={styles.secondaryBtn} onClick={() => openDetails(videoActionConsultation)}>
              View consultation
            </button>
          </div>
        </section>
      ) : null}
      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Active consultation</h3>
        {!active ? (
          <p style={styles.muted}>No active consultation.</p>
        ) : (
          <ConsultationCard
            consultation={active}
            helper={active.video?.status === "REQUESTED" ? "Video request pending. Please accept or reject above." : "Consultation is live."}
            emphasis={active.video?.status === "REQUESTED" ? "urgent" : "live"}
            actions={<button style={styles.primaryBtn} onClick={() => openDetails(active)}>Open chat / details</button>}
          />
        )}
      </section>
    </>
  );

  const renderConsultationStatusOverview = () => {
    const rows = [
      {
        key: "QUEUED",
        title: "In queue",
        empty: "No queued consultations.",
        items: grouped.QUEUED,
        helper: (c) => `Doctor accepted. Queue #${c.queue_number || "-"}.`,
        emphasis: undefined,
      },
      {
        key: "PENDING",
        title: "Pending",
        empty: "No pending consultations.",
        items: grouped.PENDING,
        helper: () => "Waiting for the doctor to accept, reject, or suggest another time.",
        emphasis: "waiting",
      },
      {
        key: "POSTPONED",
        title: "Postponed",
        empty: "No postponed consultations.",
        items: grouped.POSTPONED,
        helper: (c) => `Doctor proposed: ${c.formatted_suggested_time || "updated time"}`,
        emphasis: "urgent",
      },
      {
        key: "COMPLETED",
        title: "Completed",
        empty: "No completed consultations.",
        items: path === "/dashboard/patient" ? grouped.COMPLETED : [],
        helper: followUpHelperText,
        emphasis: followUpEmphasis,
      },
    ];

    return (
      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Consultation status</h3>
        {followUpMsg ? <p style={followUpMsg.includes("Could") ? styles.inlineError : styles.inlineSuccess}>{followUpMsg}</p> : null}
        <div style={styles.consultationStatusGrid}>
          {rows.map((row) => (
            <div key={row.key} style={styles.statusColumn}>
              <div style={styles.statusHeader}>
                <strong>{row.title}</strong>
                <span style={styles.statusCount}>{row.items.length}</span>
              </div>
              {row.items.length === 0 ? <p style={styles.emptyStatusText}>{row.empty}</p> : null}
              {row.items.slice(0, row.key === "COMPLETED" ? 3 : 4).map((c) => (
                <ConsultationCard
                  key={`${row.key}-${c.id}`}
                  consultation={c}
                  helper={row.helper(c)}
                  emphasis={typeof row.emphasis === "function" ? row.emphasis(c) : row.emphasis}
                  actions={
                    row.key === "POSTPONED" ? (
                      <div style={styles.rowActions}>
                        <button
                          style={styles.primaryBtn}
                          onClick={async () => {
                            setBusy(true);
                            try {
                              await patientRespondToConsultation(c.id, "approve_postponed");
                              await refresh();
                              showNotice("success", "New time accepted", "Your consultation is pending the doctor's acceptance at the agreed time. No second consultation charge was taken.");
                            } catch (err) {
                              showNotice("error", "Could not accept the new time", err.message || "Please refresh and try again.");
                            } finally { setBusy(false); }
                          }}
                        >
                          Accept
                        </button>
                        <button
                          style={styles.warnBtn}
                          disabled={busy}
                          onClick={async () => {
                            setBusy(true);
                            try {
                              const response = await patientRespondToConsultation(c.id, "reject_postponed");
                              const outcome = postponementOutcome(response.data);
                              if (outcome) showNotice("warning", outcome.title, outcome.body);
                              await refresh();
                            } catch (err) {
                              showNotice("error", "Could not reject the proposed time", err.message || "Please refresh and try again.");
                            } finally { setBusy(false); }
                          }}
                        >
                          Reject
                        </button>
                      </div>
                    ) : row.key === "COMPLETED" ? (
                      <div style={styles.rowActions}>
                        <button style={styles.secondaryBtn} onClick={() => openDetails(c)}>Open history</button>
                        <button
                          style={styles.primaryBtn}
                          disabled={busy || (c.follow_up?.active_status !== "IN_PROGRESS" && !c.follow_up?.can_request)}
                          onClick={() => (c.follow_up?.active_status === "IN_PROGRESS" ? openDetails(c) : requestFollowUp(c))}
                        >
                          {followUpButtonText(c)}
                        </button>
                      </div>
                    ) : (
                      <button style={styles.secondaryBtn} onClick={() => openDetails(c)}>
                        Details
                      </button>
                    )
                  }
                />
              ))}
            </div>
          ))}
        </div>
      </section>
    );
  };

  const renderFindDoctors = () => (
    <Section title="Find doctors" id="patient-book">
      {bookError ? (
        <div role="alert" style={styles.bookErrorBanner}>
          {bookError}
        </div>
      ) : null}
      <div style={styles.doctorSearchGrid}>
        <input
          style={styles.input}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search doctor, hospital, qualification"
        />
        <input
          style={styles.input}
          value={specialtyFilter}
          onChange={(e) => setSpecialtyFilter(e.target.value)}
          placeholder="Specialty"
        />
        <input
          style={styles.input}
          value={locationFilter}
          onChange={(e) => setLocationFilter(e.target.value)}
          placeholder="City or state"
        />
      </div>
      <div style={{ marginTop: 12 }}>
        {filteredDoctors.slice(0, 24).map((d) => (
          <div key={d.id} style={styles.doctorCard}>
            <div style={styles.doctorIdentity}>
              {d.photo ? (
                <img src={d.photo} alt="" style={styles.doctorPhoto} />
              ) : (
                <div style={styles.doctorInitials}>
                  {(d.first_name || "D").slice(0, 1)}
                  {(d.last_name || "").slice(0, 1)}
                </div>
              )}
              <div>
                <div style={styles.rowTitle}>
                  Dr. {d.first_name} {d.last_name}
                </div>
                <div style={styles.rowMeta}>
                  {d.specialty || "General Physician"} · {d.qualification || "Verified doctor"}
                </div>
                <div style={styles.rowMeta}>
                  {[d.hospital_or_clinic_name, d.city, d.state].filter(Boolean).join(", ") || "Online consultation"}
                </div>
                <div style={styles.modeRow}>
                  {(d.consultation_modes || []).slice(0, 4).map((mode) => (
                    <span key={mode} style={styles.modePill}>{mode}</span>
                  ))}
                  {d.consultation_fee ? <span style={styles.feePill}>Base fee Rs {d.consultation_fee}</span> : null}
                </div>
                <small>Review the full fee, including any platform charge, before confirming.</small>
              </div>
            </div>
            <button disabled={busy} style={styles.primaryBtn} onClick={() => reviewConsultation(d)}>
              Review fee & consult
            </button>
          </div>
        ))}
        {filteredDoctors.length === 0 ? <p style={styles.muted}>No matching verified doctors found.</p> : null}
      </div>
    </Section>
  );

  const renderHistoryPage = () => (
    <>
      <Section title="All consultations">
        {consultations.length === 0 ? (
          <p style={styles.muted}>No consultations yet. Use Book to request one.</p>
        ) : (
          [...consultations]
            .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
            .map((c) => (
              <ConsultationCard
                key={c.id}
                consultation={c}
                actions={<button style={styles.secondaryBtn} onClick={() => openDetails(c)}>Timeline</button>}
              />
            ))
        )}
      </Section>
    </>
  );

  const renderProfilePage = () => (
    <section style={styles.section}>
      <h3 style={styles.sectionTitle}>Profile details</h3>
      {profileMsg ? <p style={{ color: profileMsg.includes("saved") ? "#0d6b3a" : "#b00020" }}>{profileMsg}</p> : null}
      {!profileUser && !profileMsg ? <p style={styles.muted}>Loading…</p> : null}
      {profileUser ? (
        <form onSubmit={saveProfile} style={styles.profileForm}>
          <label style={styles.label}>
            First name
            <input
              style={styles.input}
              value={profileForm.first_name}
              onChange={(e) => setProfileForm((f) => ({ ...f, first_name: e.target.value }))}
            />
          </label>
          <label style={styles.label}>
            Last name
            <input
              style={styles.input}
              value={profileForm.last_name}
              onChange={(e) => setProfileForm((f) => ({ ...f, last_name: e.target.value }))}
            />
          </label>
          <label style={styles.label}>
            Email
            <input
              type="email"
              style={styles.input}
              value={profileForm.email}
              onChange={(e) => setProfileForm((f) => ({ ...f, email: e.target.value }))}
            />
          </label>
          <label style={styles.label}>
            Phone
            <input
              style={styles.input}
              value={profileForm.phone_number}
              onChange={(e) => setProfileForm((f) => ({ ...f, phone_number: e.target.value }))}
            />
          </label>
          <label style={styles.label}>
            Gender
            <select
              style={styles.input}
              value={profileForm.gender}
              onChange={(e) => setProfileForm((f) => ({ ...f, gender: e.target.value }))}
            >
              <option value="M">Male</option>
              <option value="F">Female</option>
              <option value="O">Other</option>
            </select>
          </label>
          <label style={styles.label}>
            Age
            <input
              type="number"
              min={0}
              max={120}
              style={styles.input}
              value={profileForm.age}
              onChange={(e) => setProfileForm((f) => ({ ...f, age: e.target.value }))}
            />
          </label>
          <label style={{ ...styles.label, gridColumn: "1 / -1" }}>
            Address
            <textarea
              style={{ ...styles.input, minHeight: 72, resize: "vertical" }}
              value={profileForm.address}
              onChange={(e) => setProfileForm((f) => ({ ...f, address: e.target.value }))}
            />
          </label>
          <button type="submit" disabled={profileSaving} style={styles.primaryBtn}>
            {profileSaving ? "Saving…" : "Save changes"}
          </button>
        </form>
      ) : null}
    </section>
  );

  const renderPasswordPage = () => (
    <section style={styles.section}>
      <h3 style={styles.sectionTitle}>Password</h3>
      <p style={styles.muted}>
        In-app password change is not enabled yet. Log out and use your account recovery flow, or contact support if you
        need help accessing your account.
      </p>
      <a href="/logout" style={{ ...styles.secondaryBtn, display: "inline-block", textDecoration: "none" }}>
        Log out
      </a>
    </section>
  );

  const renderMain = () => {
    if (path === "/patient/profile") return renderProfilePage();
    if (path === "/patient/change-password") return renderPasswordPage();
    if (path === "/patient/book") {
      return (
        <>
          {renderFindDoctors()}
          {renderActiveConsultationSection()}
          {renderConsultationStatusOverview()}
        </>
      );
    }
    if (path === "/patient/history") return renderHistoryPage();
    return (
      <>
        {renderFindDoctors()}
        {renderActiveConsultationSection()}
        {renderConsultationStatusOverview()}
      </>
    );
  };

  const pageTitle = PAGE_TITLES[path] || "Patient dashboard";
  const subtitle =
    path === "/dashboard/patient"
      ? "Wallet, consultations, and booking in one place."
      : path === "/patient/book"
        ? "Request a consultation with an available doctor."
        : path === "/patient/history"
          ? "Review past and current consultations."
          : path === "/patient/profile"
            ? "Update your account and health profile details."
            : path === "/patient/change-password"
              ? "Manage how you sign in."
              : "";
  const selectedChatStatus = selected?.follow_up?.active_status === "IN_PROGRESS" ? "IN_PROGRESS" : selected?.status;

  return (
    <div style={styles.page}>
      <Header role="patient" balance={wallet?.balance} onBalanceClick={() => setWalletExpanded((v) => !v)} />
      <Sidebar
        role="patient"
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
          {notice ? (
            <div role="status" aria-live="polite" style={{ ...styles.noticeToast, ...styles[`notice${notice.type}`] }}>
              <div>
                <div style={styles.noticeTitle}>{notice.title}</div>
                <div style={styles.noticeBody}>{notice.body}</div>
              </div>
              <button type="button" style={styles.noticeClose} onClick={() => setNotice(null)} aria-label="Dismiss notification">
                x
              </button>
            </div>
          ) : null}
          {isStale ? <StaleNotification onRetry={refresh} /> : null}
          <h1 style={styles.title}>{pageTitle}</h1>
          {subtitle ? <p style={styles.subtitle}>{subtitle}</p> : null}
          <PostponementOutcome consultation={consultations.find((c) => c.status === "REJECTED_BY_PATIENT")} role="patient" />
          <button type="button" style={styles.secondaryBtn} onClick={() => setWalletExpanded((v) => !v)}>
            ◉ Balance: Rs {wallet?.balance ?? "…"} · Add funds / payment history
          </button>
          {walletExpanded ? renderWalletAndOverview() : null}
          <div ref={paymentReviewRef}>
            <PatientBookingReview
              preview={bookingReview}
              doctor={bookingReview?.doctor}
              busy={busy}
              onConfirm={() => bookingReview?.can_request && requestConsultation(bookingReview.doctor_id, bookingReview.total)}
              onCancel={() => setBookingReview(null)}
              onFunds={() => setWalletExpanded(true)}
            />
          </div>
          {renderMain()}
        </main>
        <Footer />
      </div>
      <ConsultationDetailModal 
        consultation={selected} 
        events={events} 
        onClose={() => { 
          selectedIdRef.current = null;
          setSelected(null); 
        }} 
        viewerRole="patient"
      >
        {selected && selectedChatStatus === "COMPLETED" ? (
          <div style={styles.followUpBox}>
            <div>
              <strong style={{ color: "#123a6f" }}>Need to ask the doctor again?</strong>
              <p style={styles.muted}>
                {selected.follow_up?.next_is_billable
                  ? "This follow-up is outside the free allowance and will be charged before it is sent."
                  : `Free follow-ups remaining: ${selected.follow_up?.free_remaining ?? 0}`}
              </p>
            </div>
            <button
              style={styles.primaryBtn}
              disabled={busy || !selected.follow_up?.can_request}
              onClick={() => requestFollowUp(selected)}
            >
              {followUpButtonText(selected)}
            </button>
          </div>
        ) : null}
        {selected ? (
          <ConsultationChatPanel consultationId={selected.id} status={selectedChatStatus} pollMs={5000} />
        ) : null}
        {selected && prescriptionMap[selected.id] ? (
          <div style={styles.sectionInset}>
            <h4 style={{ margin: 0, color: "#123a6f" }}>Your prescription</h4>
            {prescriptionMap[selected.id].updated_at ? (
              <p style={styles.muted}>Last updated: {new Date(prescriptionMap[selected.id].updated_at).toLocaleString()}</p>
            ) : null}
            <button style={styles.primaryBtn} onClick={() => downloadPrescriptionPdf(prescriptionMap[selected.id].id)}>
              Download PDF
            </button>
          </div>
        ) : null}
      </ConsultationDetailModal>
    </div>
  );
};

const ConsultationCard = ({ consultation, helper, actions, emphasis }) => {
  const statusInfo = getStatusMessage(consultation, 'patient');
  const displayHelper = helper || statusInfo?.message;
  const displayEmphasis = emphasis || (statusInfo?.severity === 'urgent' ? 'urgent' : statusInfo?.severity === 'success' ? 'live' : undefined);

  return (
    <article style={{ ...styles.card, ...(displayEmphasis ? styles[`card${displayEmphasis}`] : {}) }}>
      <div>
        <div style={styles.rowTitle}>
          Dr. {consultation.doctor_name}
          {consultation.video?.status === "REQUESTED" ? <span style={styles.videoTag}>Video requested</span> : null}
          {followUpStatusLabel(consultation) ? (
            <span style={consultation.follow_up?.active_status === "IN_PROGRESS" ? styles.liveTag : styles.waitingTag}>
              {followUpStatusLabel(consultation)}
            </span>
          ) : null}
        </div>
        <div style={styles.rowMeta}>
          {consultation.formatted_time} · {consultation.consultation_type}
        </div>
        <div style={styles.idLine}>
          Consultation ID: #{consultation.id}
          {consultation.follow_up?.active_session_id ? ` | Follow-up ID: #${consultation.follow_up.active_session_id}` : ""}
        </div>
        <div style={{ marginTop: 6 }}>
          <StatusBadge status={consultation.status} />
        </div>
        {displayHelper ? <p style={styles.helper}>{displayHelper}</p> : null}
      </div>
      {actions}
    </article>
  );
};

const Section = ({ title, children, id }) => (
  <section style={styles.section} id={id}>
    <h3 style={styles.sectionTitle}>{title}</h3>
    {children}
  </section>
);

const styles = {
  page: {
    minHeight: "100vh",
    background: DASHBOARD_PAGE_BG,
    color: "#10243e",
    fontFamily: "Segoe UI, system-ui, sans-serif",
    display: "flex",
    flexDirection: "column",
  },
  main: { flex: 1 },
  title: { margin: "0 0 4px", color: "#002043", fontSize: "clamp(1.35rem, 3vw, 1.9rem)", lineHeight: 1.15 },
  subtitle: { color: "#4c6480", marginTop: 0, marginBottom: 16, fontSize: 14 },
  muted: { color: "#4c6480", margin: 0 },
  inlineSuccess: { color: "#17623c", fontSize: 13, margin: "0 0 10px" },
  inlineError: { color: "#8a1f1f", fontSize: 13, margin: "0 0 10px" },
  section: { marginTop: 14, background: DASHBOARD_SECTION_BG, border: DASHBOARD_BORDER, borderRadius: 16, padding: 18, boxShadow: DASHBOARD_SHADOW },
  sectionInset: { marginBottom: 14, background: "#fbfdff", border: "1px solid #d7e5f5", borderRadius: 12, padding: 12 },
  walletCompact: {
    marginTop: 14,
    background: "#fbfdff",
    border: DASHBOARD_BORDER,
    borderRadius: 14,
    padding: "12px 14px",
    boxShadow: DASHBOARD_SHADOW,
    display: "flex",
    justifyContent: "space-between",
    gap: 12,
    alignItems: "center",
    flexWrap: "wrap",
  },
  compactTitle: { margin: 0, color: "#123a6f", fontSize: "1rem" },
  walletSummaryRow: { display: "flex", gap: 10, alignItems: "baseline", flexWrap: "wrap", marginTop: 4 },
  walletBalance: { color: "#123a6f", fontSize: "1.1rem" },
  walletMiniText: { color: "#4c6480", fontSize: 12, fontWeight: 700 },
  walletExpandedArea: { flexBasis: "100%", borderTop: "1px solid #d7e5f5", paddingTop: 12 },
  walletHistoryGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10, marginTop: 10 },
  compactWalletRow: {
    border: "1px solid #d7e5f5",
    borderRadius: 10,
    padding: 10,
    background: "#fff",
    marginBottom: 8,
    display: "flex",
    justifyContent: "space-between",
    gap: 10,
    alignItems: "center",
  },
  actionPanel: {
    marginTop: 14,
    background: "#fff7ed",
    border: "2px solid #e28a2e",
    borderLeft: "8px solid #d96d16",
    borderRadius: 14,
    padding: 16,
    boxShadow: "0 14px 32px rgba(138, 75, 16, 0.18)",
    display: "flex",
    justifyContent: "space-between",
    gap: 14,
    alignItems: "center",
    flexWrap: "wrap",
  },
  actionEyebrow: { color: "#8a4b10", fontSize: 12, fontWeight: 900, textTransform: "uppercase", letterSpacing: 0 },
  actionTitle: { margin: "3px 0", color: "#6f3505", fontSize: "1.15rem" },
  actionText: { margin: 0, color: "#74491d", fontSize: 14, lineHeight: 1.45 },
  actionButtons: { display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" },
  noticeToast: {
    position: "fixed",
    top: 110,
    right: 16,
    width: "min(420px, calc(100vw - 32px))",
    boxSizing: "border-box",
    maxHeight: "50vh",
    overflowY: "auto",
    zIndex: 2200,
    marginBottom: 14,
    borderRadius: 10,
    padding: "12px 14px",
    border: "1px solid #bad3f0",
    boxShadow: "0 12px 28px rgba(9, 36, 72, 0.16)",
    display: "flex",
    justifyContent: "space-between",
    gap: 12,
    alignItems: "flex-start",
  },
  noticesuccess: {
    background: "#eef8f2",
    borderColor: "#acd9bf",
    color: "#123a2a",
  },
  noticewarning: {
    background: "#fff8e8",
    borderColor: "#efcf88",
    color: "#624000",
  },
  noticeerror: {
    background: "#fdeeee",
    borderColor: "#efb4b4",
    color: "#711f1f",
  },
  noticeTitle: { fontWeight: 800, marginBottom: 3 },
  noticeBody: { fontSize: 14, lineHeight: 1.4 },
  noticeClose: {
    border: "1px solid rgba(18, 58, 111, 0.2)",
    background: "rgba(255,255,255,0.7)",
    color: "#123a6f",
    borderRadius: 8,
    width: 28,
    height: 28,
    fontWeight: 800,
    cursor: "pointer",
    lineHeight: "24px",
  },
  followUpBox: {
    marginBottom: 14,
    background: "#eef8f2",
    border: "1px solid #b8dbc7",
    borderRadius: 10,
    padding: 12,
    display: "flex",
    justifyContent: "space-between",
    gap: 12,
    alignItems: "center",
    flexWrap: "wrap",
  },
  sectionTitle: { margin: 0, marginBottom: 10, color: "#123a6f", fontSize: "1.05rem" },
  consultationStatusGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
    gap: 12,
  },
  statusColumn: {
    border: "1px solid #d7e5f5",
    borderRadius: 12,
    background: "#fbfdff",
    padding: 10,
    minHeight: 86,
  },
  statusHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 8,
    color: "#123a6f",
    marginBottom: 8,
  },
  statusCount: {
    minWidth: 26,
    height: 26,
    borderRadius: 999,
    background: "#edf4fd",
    color: "#174577",
    display: "inline-grid",
    placeItems: "center",
    fontSize: 12,
    fontWeight: 900,
  },
  emptyStatusText: {
    margin: 0,
    color: "#5d7188",
    fontSize: 13,
  },
  card: {
    border: "1px solid #d7e5f5",
    borderRadius: 14,
    padding: 12,
    background: "#fbfdff",
    marginBottom: 10,
    display: "flex",
    justifyContent: "space-between",
    gap: 12,
    alignItems: "center",
    flexWrap: "wrap",
  },
  cardurgent: { borderColor: "#e28a2e", background: "#fffaf2", boxShadow: "0 8px 22px rgba(138, 75, 16, 0.12)" },
  cardwaiting: { borderColor: "#8ab0dc", background: "#f4f8fe" },
  cardlive: { borderColor: "#91d0aa", background: "#f2fbf5" },
  rowTitle: { fontWeight: 700, color: "#113864", fontSize: 14 },
  rowMeta: { color: "#4c6480", fontSize: 13, marginTop: 4 },
  idLine: {
    color: "#174577",
    background: "#edf4fd",
    border: "1px solid #c8ddf4",
    borderRadius: 8,
    padding: "6px 8px",
    marginTop: 8,
    fontSize: 12,
    fontWeight: 800,
    display: "inline-block",
  },
  helper: { color: "#244a75", fontSize: 13, marginTop: 8, marginBottom: 0 },
  rowActions: { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" },
  primaryBtn: {
    background: "#1762bf",
    color: "#fff",
    border: "none",
    borderRadius: 10,
    padding: "8px 12px",
    fontWeight: 700,
    cursor: "pointer",
  },
  secondaryBtn: {
    background: "#edf4fd",
    color: "#174577",
    border: "1px solid #8ab0dc",
    borderRadius: 10,
    padding: "8px 12px",
    fontWeight: 700,
    cursor: "pointer",
  },
  warnBtn: {
    background: "#ffeedd",
    color: "#8a4b10",
    border: "1px solid #ffca9f",
    borderRadius: 10,
    padding: "8px 12px",
    fontWeight: 700,
    cursor: "pointer",
  },
  input: { height: 44, borderRadius: 10, border: "1px solid #c6d7eb", padding: "0 12px", width: "100%", boxSizing: "border-box", background: "#fbfdff", fontSize: 14 },
  doctorSearchGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    gap: 10,
  },
  bookErrorBanner: {
    marginBottom: 12,
    padding: "10px 12px",
    borderRadius: 14,
    background: "#fdeaea",
    border: "1px solid #f0b4b4",
    color: "#7a1f1f",
    fontSize: 14,
    lineHeight: 1.45,
  },
  doctorRow: {
    border: "1px solid #d7e5f5",
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    background: "#fbfdff",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 10,
    flexWrap: "wrap",
  },
  doctorCard: {
    border: "1px solid #d7e5f5",
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    background: "#fbfdff",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
    flexWrap: "wrap",
  },
  doctorIdentity: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    minWidth: 260,
    flex: "1 1 320px",
  },
  doctorPhoto: {
    width: 58,
    height: 58,
    borderRadius: 12,
    objectFit: "cover",
    border: "1px solid #c6d7eb",
    background: "#eef5ff",
  },
  doctorInitials: {
    width: 58,
    height: 58,
    borderRadius: 8,
    background: "#e8f1fb",
    color: "#123a6f",
    border: "1px solid #c6d7eb",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 800,
    fontSize: 18,
  },
  modeRow: { display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 },
  modePill: {
    border: "1px solid #c6d7eb",
    background: "#fff",
    color: "#174577",
    borderRadius: 999,
    padding: "3px 8px",
    fontSize: 11,
    fontWeight: 700,
  },
  feePill: {
    border: "1px solid #b8dbc7",
    background: "#effaf3",
    color: "#17623c",
    borderRadius: 999,
    padding: "3px 8px",
    fontSize: 11,
    fontWeight: 800,
  },
  badgeSoft: {
    borderRadius: 999,
    background: "#e8f1fb",
    color: "#174577",
    padding: "4px 9px",
    fontSize: 12,
    fontWeight: 800,
  },
  videoTag: { marginLeft: 8, padding: "2px 8px", borderRadius: 999, background: "#fff1e8", color: "#8a4b10", fontSize: 12, fontWeight: 900 },
  waitingTag: { marginLeft: 8, padding: "2px 8px", borderRadius: 999, background: "#edf4fd", color: "#174577", fontSize: 12, fontWeight: 900 },
  liveTag: { marginLeft: 8, padding: "2px 8px", borderRadius: 999, background: "#e8f7ef", color: "#17623c", fontSize: 12, fontWeight: 900 },
  walletNote: { color: "#4c6480", fontSize: 12, marginTop: 8, marginBottom: 0 },
  walletRechargeForm: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
    gap: 10,
    alignItems: "end",
    marginTop: 12,
  },
  inlineNotice: {
    marginTop: 10,
    padding: "9px 11px",
    borderRadius: 8,
    background: "#edf7ee",
    border: "1px solid #b7dcbc",
    color: "#185a2b",
    fontSize: 13,
  },
  profileForm: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: 12,
    alignItems: "start",
  },
  label: { display: "flex", flexDirection: "column", gap: 6, fontSize: 13, fontWeight: 600, color: "#113864" },
};

export default PatientDashboardRefined;
