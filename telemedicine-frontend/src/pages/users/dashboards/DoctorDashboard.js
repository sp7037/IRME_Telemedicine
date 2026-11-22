import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useLocation } from "react-router-dom";
import Header from "../../../components/Header";
import PostponementOutcome, { postponementOutcome } from "../../../components/dashboard/PostponementOutcome";
import Footer from "../../../components/Footer";
import Sidebar from "../../../components/Sidebar";
import { dashboardContentMarginLeft } from "../../../constants/dashboardLayout";
import {
  DASHBOARD_BORDER,
  DASHBOARD_PAGE_BG,
  DASHBOARD_SECTION_BG,
  DASHBOARD_SHADOW,
} from "../../../constants/brandTheme";
import StatusBadge from "../../../components/dashboard/StatusBadge";
import ConsultationDetailModal from "../../../components/dashboard/ConsultationDetailModal";
import ConsultationChatPanel from "../../../components/dashboard/ConsultationChatPanel";
import {
  DoctorProfilePanel,
  DoctorAvailabilityPanel,
  DoctorSchedulePanel,
  DoctorProfileStatusBadges,
  formatDoctorDisplayName,
} from "../../../components/dashboard/DoctorAccountPanels";
import {
  getPatientConsultationHistory,
  getDoctorPendingRequests,
  getDoctorQueuedConsultations,
  getActiveConsultation,
  doctorRespondToRequest,
  startConsultation,
  completeConsultation,
  doctorRespondToFollowUp,
  getConsultationEvents,
  getDoctorEarningsSummary,
  getPrescription,
  createPrescription,
  updatePrescription,
  downloadPrescriptionPdf,
  getPrescriptionVersions,
  getDoctorProfile,
} from "../../../api/users";

const NEEDS_CONSULT_DATA = new Set([
  "/dashboard/doctor",
  "/doctor/queue",
  "/doctor/appointments",
  "/doctor/earnings",
  "/doctor/history",
]);

const PAGE_TITLES = {
  "/dashboard/doctor": "Doctor operations",
  "/doctor/profile": "Profile",
  "/doctor/availability": "Availability",
  "/doctor/schedule": "Schedule",
  "/doctor/queue": "Consultation queue",
  "/doctor/appointments": "Appointments & requests",
  "/doctor/earnings": "Earnings",
  "/doctor/history": "Consultation history",
};

/** Experience line for dashboard card: "10" → "10 years exp"; keeps text like "5 yrs" as-is. */
function formatDoctorExperience(raw) {
  if (raw === null || raw === undefined) return "—";
  const s = String(raw).trim();
  if (!s) return "—";
  if (/year|yr|exp|month/i.test(s)) return s;
  if (/^\d+(\.\d+)?$/.test(s)) return `${s} years exp`;
  return s;
}

function formatActiveDuration(minutes) {
  if (minutes === null || minutes === undefined) return "more than 24 hours";
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours >= 24) return `${hours}h ${mins}m`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

const DoctorDashboard = () => {
  const location = useLocation();
  const path = location.pathname;

  const [all, setAll] = useState([]);
  const [pending, setPending] = useState([]);
  const [queued, setQueued] = useState([]);
  const [active, setActive] = useState(null);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState(null);
  const [events, setEvents] = useState([]);
  const [prescription, setPrescription] = useState(null);
  const [rxVersions, setRxVersions] = useState(null);
  const [postponeDate, setPostponeDate] = useState("");
  const [earnings, setEarnings] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [doctorCard, setDoctorCard] = useState(null);
  const [notice, setNotice] = useState(null);
  const requestSeenRef = useRef(new Map());
  const requestReadyRef = useRef(false);
  const consultationStatusRef = useRef(new Map());

  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    () => typeof window !== "undefined" && window.innerWidth < 768
  );
  const [winW, setWinW] = useState(() => (typeof window !== "undefined" ? window.innerWidth : 1200));

  const isNarrow = winW < 768;
  const needsConsultData = NEEDS_CONSULT_DATA.has(path);

  const showNotice = useCallback((type, title, body) => {
    setNotice({ type, title, body, id: Date.now() });
  }, []);

  const formatRequestIdentity = useCallback((request) => {
    const patient = request.patient_name || "Patient";
    const patientId = request.patient || request.patient_id || "-";
    return `${patient} | Patient ID: ${patientId} | Consultation ID: ${request.id}`;
  }, []);

  const refresh = useCallback(async () => {
    setLoadError(null);
    const [history, pend, queue, current] = await Promise.all([
      getPatientConsultationHistory(),
      getDoctorPendingRequests(),
      getDoctorQueuedConsultations(),
      getActiveConsultation(),
    ]);
    const earningData = await getDoctorEarningsSummary();
    const pendingList = Array.isArray(pend) ? pend : [];
    const nextSeen = new Map();
    pendingList.forEach((request) => {
      const key = `${request.is_follow_up_request ? "follow" : "consult"}:${request.is_follow_up_request ? request.follow_up_session_id || request.id : request.id}`;
      nextSeen.set(key, request.status || "PENDING");
      if (requestReadyRef.current && !requestSeenRef.current.has(key)) {
        showNotice(
          request.is_follow_up_request ? "warning" : "urgent",
          request.is_follow_up_request ? "Patient requested to resume chat" : "New consultation request",
          `${formatRequestIdentity(request)}. Please review and take action.`
        );
      }
    });
    if (!requestReadyRef.current && pendingList.length > 0) {
      const followUps = pendingList.filter((request) => request.is_follow_up_request).length;
      showNotice(
        "urgent",
        `${pendingList.length} pending request${pendingList.length > 1 ? "s" : ""} waiting`,
        followUps
          ? `${followUps} patient resume-chat request${followUps > 1 ? "s" : ""} and ${pendingList.length - followUps} consultation request${pendingList.length - followUps === 1 ? "" : "s"} need action.`
          : "New consultation requests are waiting. Please review and accept, reject, or suggest another time."
      );
    }
    requestSeenRef.current = nextSeen;
    requestReadyRef.current = true;
    const historyList = Array.isArray(history) ? history : [];
    historyList.forEach((consultation) => {
      const previous = consultationStatusRef.current.get(consultation.id);
      if (previous && previous !== consultation.status) {
        const outcome = postponementOutcome(consultation, "doctor");
        if (outcome) showNotice("warning", outcome.title, outcome.body);
      }
    });
    consultationStatusRef.current = new Map(historyList.map((c) => [c.id, c.status]));
    setAll(historyList);
    setPending(pendingList);
    setQueued(Array.isArray(queue) ? queue : []);
    setActive(current && !Array.isArray(current) && current.id ? current : null);
    setEarnings(earningData);
  }, [formatRequestIdentity, showNotice]);

  useEffect(() => {
    const onR = () => {
      const w = window.innerWidth;
      setWinW(w);
      if (w >= 768) setSidebarCollapsed(false);
    };
    window.addEventListener("resize", onR);
    return () => window.removeEventListener("resize", onR);
  }, []);

  useEffect(() => {
    let cancelled = false;
    getDoctorProfile()
      .then((p) => {
        if (!cancelled && p) setDoctorCard(p);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [path]);

  useEffect(() => {
    const onRefreshCard = () => {
      getDoctorProfile()
        .then((p) => {
          if (p) setDoctorCard(p);
        })
        .catch(() => {});
    };
    window.addEventListener("irme-doctor-profile-refresh", onRefreshCard);
    return () => window.removeEventListener("irme-doctor-profile-refresh", onRefreshCard);
  }, []);

  useEffect(() => {
    if (!needsConsultData) return undefined;
    refresh().catch((err) => {
      setLoadError(err?.message || "Could not load dashboard data.");
      console.error(err);
    });
    const t = setInterval(
      () =>
        refresh().catch((err) => {
          setLoadError(err?.message || "Refresh failed.");
          console.error(err);
        }),
      8000
    );
    return () => clearInterval(t);
  }, [needsConsultData, refresh]);

  useEffect(() => {
    if (!notice) return undefined;
    const timer = setTimeout(() => setNotice(null), notice.type === "urgent" ? 10000 : 8000);
    return () => clearTimeout(timer);
  }, [notice]);

  const completed = useMemo(
    () => all.filter((c) => c.status === "COMPLETED" || c.is_completed).slice(0, 8),
    [all]
  );
  const postponed = useMemo(() => all.filter((c) => c.status === "POSTPONED"), [all]);
  const followUpPending = useMemo(() => pending.filter((c) => c.is_follow_up_request), [pending]);
  const newConsultPending = useMemo(() => pending.filter((c) => !c.is_follow_up_request), [pending]);
  const historySorted = useMemo(
    () => [...all].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)),
    [all]
  );

  const openDetail = async (consultation) => {
    setSelected(consultation);
    setPrescription(null);
    setRxVersions(null);
    const [e, rx, v] = await Promise.all([
      getConsultationEvents(consultation.id, { order: "asc" }),
      getPrescription(consultation.id).catch(() => null),
      getPrescriptionVersions(consultation.id).catch(() => null),
    ]);
    setEvents(Array.isArray(e) ? e : []);
    setPrescription(rx && rx.id ? rx : null);
    setRxVersions(v && v.version_rows ? v : null);
  };

  const refreshPrescriptionDetail = async (consultationId) => {
    const [rx, v, e] = await Promise.all([
      getPrescription(consultationId).catch(() => null),
      getPrescriptionVersions(consultationId).catch(() => null),
      getConsultationEvents(consultationId, { order: "asc" }).catch(() => []),
    ]);
    setPrescription(rx && rx.id ? rx : null);
    setRxVersions(v && v.version_rows ? v : null);
    setEvents(Array.isArray(e) ? e : []);
  };

  const handleAction = async (consultationId, status) => {
    setBusy(true);
    try {
      const item = pending.find((p) => p.id === consultationId);
      if (item?.is_follow_up_request && item?.follow_up_session_id) {
        await doctorRespondToFollowUp(item.follow_up_session_id, status === "REJECTED" ? "REJECTED" : "ACCEPTED");
      } else {
        await doctorRespondToRequest(
          consultationId,
          status,
          status === "POSTPONED" ? new Date(postponeDate).toISOString() : null
        );
      }
      setPostponeDate("");
      await refresh();
      showNotice(
        status === "REJECTED" ? "warning" : "success",
        item?.is_follow_up_request
          ? status === "REJECTED" ? "Resume chat rejected" : "Resume chat accepted"
          : status === "POSTPONED" ? "New time suggested" : status === "REJECTED" ? "Consultation request rejected" : "Consultation request accepted",
        `${formatRequestIdentity(item || { id: consultationId })}.`
      );
    } catch (err) {
      const message = err?.message || "Could not process this request.";
      showNotice("warning", "Action blocked", message);
      setLoadError(null);
      await refresh().catch((refreshErr) => {
        setLoadError(refreshErr?.message || "Refresh failed.");
        console.error(refreshErr);
      });
    } finally {
      setBusy(false);
    }
  };

  const handleCompleteSelected = async () => {
    if (!selected?.id || busy) return;
    setBusy(true);
    try {
      await completeConsultation(selected.id);
      const updated = { ...selected, status: "COMPLETED", is_completed: true };
      setSelected(updated);
      await Promise.all([refresh(), refreshPrescriptionDetail(selected.id)]);
    } finally {
      setBusy(false);
    }
  };

  const contentMarginLeft = dashboardContentMarginLeft(isNarrow, sidebarCollapsed);
  const mainPaddingTop = 16;

  const renderAccountPanel = () => {
    if (path === "/doctor/profile") return <DoctorProfilePanel />;
    if (path === "/doctor/availability") return <DoctorAvailabilityPanel />;
    if (path === "/doctor/schedule") return <DoctorSchedulePanel />;
    return null;
  };

  const renderOperations = () => (
    <>
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

      {loadError ? (
        <div style={styles.errorBanner} role="alert">
          <strong>Could not load data.</strong> {loadError}{" "}
          <button
            type="button"
            style={styles.retryBtn}
            onClick={() =>
              refresh().catch((err) => {
                setLoadError(err?.message || "Retry failed.");
                console.error(err);
              })
            }
          >
            Retry
          </button>
          <p style={styles.errorHint}>
            If you recently updated the code, run <code>python manage.py migrate</code> on the server.
          </p>
        </div>
      ) : null}

      {active?.completion_required ? (
        <section style={styles.completionLockPanel} role="alert" aria-live="assertive">
          <div>
            <div style={styles.actionEyebrow}>Completion required</div>
            <h3 style={styles.urgentTitle}>Consultation #{active.id} is still marked live</h3>
            <p style={styles.urgentText}>
              This consultation has been in progress for {formatActiveDuration(active.active_duration_minutes)}.
              Chat and video are locked until you mark it complete.
            </p>
          </div>
          <div style={styles.rowActions}>
            <button type="button" style={styles.completeBtn} disabled={busy} onClick={async () => { await completeConsultation(active.id); await refresh(); }}>
              Mark complete
            </button>
            <button type="button" style={styles.secondaryBtn} onClick={() => openDetail(active)}>
              Review details
            </button>
          </div>
        </section>
      ) : null}

      <div style={styles.cards}>
        <Metric label="Active" value={active ? 1 : 0} />
        <Metric label="Queued" value={queued.length} />
        <Metric label="New Requests" value={newConsultPending.length} />
        <Metric label="Follow-ups" value={followUpPending.length} />
        <Metric label="Completed" value={completed.length} />
        <Metric label="Total Earnings" value={earnings ? `Rs ${earnings.total_earnings}` : "Rs 0.00"} />
      </div>

      {pending.length > 0 ? (
        <section style={styles.urgentPanel}>
          <div>
            <h3 style={styles.urgentTitle}>
              {pending.length} doctor action{pending.length > 1 ? "s" : ""} pending
            </h3>
            <p style={styles.urgentText}>
              New consultations must be accepted or rejected. Follow-up requests start only after your current active consultation is completed.
            </p>
          </div>
          <div style={styles.urgentList}>
            {pending.slice(0, 3).map((request) => (
              <div key={`${request.is_follow_up_request ? "f" : "c"}-${request.id}-${request.follow_up_session_id || ""}`} style={styles.urgentItem}>
                <strong>{request.is_follow_up_request ? "Resume chat" : "Consultation"} #{request.id}</strong>
                <span>{request.patient_name || "Patient"} | Patient ID: {request.patient || request.patient_id || "-"}</span>
                <span style={styles.workflowHint}>
                  {request.is_follow_up_request ? "Patient is asking to reopen a completed consultation." : "Patient is waiting for your decision."}
                </span>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Active Consultation</h3>
        {!active ? (
          <Empty text="No active consultation. Accept a pending request or start from queue." />
        ) : (
          <RowCard
            consultation={active}
            emphasis="live"
            helper={active.video?.status === "REQUESTED" ? "Video request sent. Waiting for patient or TMC to accept." : "Current consultation is live."}
            actions={
              <div style={styles.rowActions}>
                <button style={styles.primaryBtn} type="button" onClick={() => openDetail(active)}>
                  Open Consultation
                </button>
                <button
                  style={styles.secondaryBtn}
                  type="button"
                  onClick={async () => {
                    await completeConsultation(active.id);
                    await refresh();
                  }}
                >
                  Mark Completed
                </button>
              </div>
            }
          />
        )}
      </section>

      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Queue</h3>
        {queued.length === 0 ? (
          <Empty text="Queue is empty." />
        ) : (
          queued.map((q) => (
            <RowCard
              key={q.id}
              consultation={q}
              label={`Queue #${q.queue_number || "-"}`}
              actions={
                <div style={styles.rowActions}>
                  <button
                    style={styles.primaryBtn}
                    type="button"
                    onClick={async () => {
                      await startConsultation(q.id);
                      await refresh();
                    }}
                  >
                    Start
                  </button>
                  <button style={styles.secondaryBtn} type="button" onClick={() => openDetail(q)}>
                    Preview
                  </button>
                </div>
              }
            />
          ))
        )}
      </section>

      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Pending Requests</h3>
        {pending.length === 0 ? (
          <Empty text="No pending requests." />
        ) : (
          pending.map((pItem) => (
            <div key={pItem.id} style={{ ...styles.card, ...(pItem.is_follow_up_request ? styles.cardfollow : styles.cardurgent) }}>
              <RowCard
                consultation={pItem}
                emphasis={pItem.is_follow_up_request ? "follow" : "urgent"}
                helper={
                  pItem.is_follow_up_request
                    ? "Follow-up request from an existing patient. Complete any active consultation before starting this."
                    : "New consultation request. Accept to move patient into your queue, reject if unavailable, or suggest another time."
                }
              />
              <div style={styles.idLine}>
                Consultation ID: {pItem.id} | Patient ID: {pItem.patient || pItem.patient_id || "-"}
                {pItem.is_follow_up_request ? ` | Follow-up ID: ${pItem.follow_up_session_id || "-"}` : ""}
              </div>
              <div style={styles.rowActions}>
                <button style={styles.primaryBtn} type="button" disabled={busy} onClick={() => handleAction(pItem.id, "ACCEPTED")}>
                  {pItem.is_follow_up_request ? "Start follow-up chat" : "Accept request"}
                </button>
                <button style={styles.secondaryBtn} type="button" disabled={busy} onClick={() => handleAction(pItem.id, "REJECTED")}>
                  {pItem.is_follow_up_request ? "Reject follow-up" : "Reject request"}
                </button>
                {!pItem.is_follow_up_request ? (
                  <>
                    <input type="datetime-local" value={postponeDate} onChange={(e) => setPostponeDate(e.target.value)} style={styles.input} />
                    <button style={styles.warnBtn} type="button" disabled={busy || !postponeDate} onClick={() => handleAction(pItem.id, "POSTPONED")}>
                      Postpone
                    </button>
                  </>
                ) : null}
                <button type="button" style={styles.secondaryBtn} onClick={() => openDetail(pItem)}>View chat</button>
              </div>
            </div>
          ))
        )}
      </section>

      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Postponed Consultations</h3>
        {postponed.length === 0 ? (
          <Empty text="No postponed consultations." />
        ) : (
          postponed.map((pItem) => <RowCard key={pItem.id} consultation={pItem} />)
        )}
      </section>

      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Completed (Recent)</h3>
        {completed.length === 0 ? (
          <Empty text="No completed consultations yet." />
        ) : (
          completed.map((c) => (
            <RowCard
              key={c.id}
              consultation={c}
              actions={
                <button style={styles.secondaryBtn} type="button" onClick={() => openDetail(c)}>
                  Open History
                </button>
              }
            />
          ))
        )}
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
    </>
  );

  const renderQueuePage = () => (
    <>
      {loadError ? <p style={{ color: "#b00020" }}>{loadError}</p> : null}
      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Active</h3>
        {!active ? <Empty text="None." /> : <RowCard consultation={active} actions={<button type="button" style={styles.primaryBtn} onClick={() => openDetail(active)}>Open</button>} />}
      </section>
      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Queue</h3>
        {queued.length === 0 ? <Empty text="Empty." /> : queued.map((q) => (
          <RowCard key={q.id} consultation={q} label={`#${q.queue_number || "-"}`} actions={
            <div style={styles.rowActions}>
              <button type="button" style={styles.primaryBtn} onClick={async () => { await startConsultation(q.id); await refresh(); }}>Start</button>
              <button type="button" style={styles.secondaryBtn} onClick={() => openDetail(q)}>Details</button>
            </div>
          } />
        ))}
      </section>
    </>
  );

  const renderAppointmentsPage = () => (
    <>
      {loadError ? <p style={{ color: "#b00020" }}>{loadError}</p> : null}
      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Active</h3>
        {!active ? <Empty text="None." /> : <RowCard consultation={active} actions={<button type="button" style={styles.secondaryBtn} onClick={() => openDetail(active)}>Open</button>} />}
      </section>
      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Pending</h3>
        {pending.length === 0 ? <Empty text="None." /> : pending.map((pItem) => (
          <div key={pItem.id} style={styles.card}>
            <RowCard consultation={pItem} />
            <div style={styles.idLine}>
              Consultation ID: {pItem.id} | Patient ID: {pItem.patient || pItem.patient_id || "-"}
              {pItem.is_follow_up_request ? ` | Follow-up ID: ${pItem.follow_up_session_id || "-"}` : ""}
            </div>
            <div style={styles.rowActions}>
              <button type="button" style={styles.primaryBtn} disabled={busy} onClick={() => handleAction(pItem.id, "ACCEPTED")}>
                {pItem.is_follow_up_request ? "Start follow-up" : "Accept"}
              </button>
              <button type="button" style={styles.secondaryBtn} disabled={busy} onClick={() => handleAction(pItem.id, "REJECTED")}>Reject</button>
              {!pItem.is_follow_up_request ? (
                <>
                  <input type="datetime-local" value={postponeDate} onChange={(e) => setPostponeDate(e.target.value)} style={styles.input} />
                  <button type="button" style={styles.warnBtn} disabled={busy || !postponeDate} onClick={() => handleAction(pItem.id, "POSTPONED")}>Postpone</button>
                </>
              ) : null}
              <button type="button" style={styles.secondaryBtn} onClick={() => openDetail(pItem)}>View chat</button>
            </div>
          </div>
        ))}
      </section>
      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Postponed</h3>
        {postponed.length === 0 ? <Empty text="None." /> : postponed.map((pItem) => <RowCard key={pItem.id} consultation={pItem} />)}
      </section>
    </>
  );

  const renderEarningsPage = () => (
    <>
      {loadError ? <p style={{ color: "#b00020" }}>{loadError}</p> : null}
      <div style={styles.cards}>
        <Metric label="Total Earnings" value={earnings ? `Rs ${earnings.total_earnings}` : "Rs 0.00"} />
        <Metric label="Records" value={earnings?.total_records ?? "—"} />
      </div>
      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Recent</h3>
        {!earnings?.recent_earnings?.length ? <Empty text="No earnings yet." /> : earnings.recent_earnings.map((e) => (
          <div key={e.consultation_id} style={styles.rowCard}>
            <div>
              <div style={styles.rowTitle}>#{e.consultation_id}</div>
              <div style={styles.rowMeta}>{e.billing_type} · {e.status}</div>
            </div>
            <strong style={{ color: "#123a6f" }}>Rs {e.earning_amount}</strong>
          </div>
        ))}
      </section>
    </>
  );

  const renderHistoryPage = () => (
    <>
      {loadError ? <p style={{ color: "#b00020" }}>{loadError}</p> : null}
      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>All consultations</h3>
        {historySorted.length === 0 ? <Empty text="No history." /> : historySorted.map((c) => (
          <RowCard key={c.id} consultation={c} actions={<button type="button" style={styles.secondaryBtn} onClick={() => openDetail(c)}>Timeline</button>} />
        ))}
      </section>
    </>
  );

  const renderMain = () => {
    const panel = renderAccountPanel();
    if (panel) return panel;
    if (path === "/doctor/queue") return renderQueuePage();
    if (path === "/doctor/appointments") return renderAppointmentsPage();
    if (path === "/doctor/earnings") return renderEarningsPage();
    if (path === "/doctor/history") return renderHistoryPage();
    return renderOperations();
  };

  const pageTitle = PAGE_TITLES[path] || "Doctor dashboard";
  const subtitle =
    path === "/dashboard/doctor"
      ? "Clear workflow from requests to completion."
      : "Use the sidebar to switch sections.";

  return (
    <div style={styles.page}>
      <Header role="doctor" />
      <Sidebar
        role="doctor"
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
            padding: `${mainPaddingTop}px 16px 48px`,
            maxWidth: "100%",
            boxSizing: "border-box",
          }}
        >
          {path !== "/dashboard/doctor" && notice ? (
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
          <h1 style={styles.title}>{pageTitle}</h1>
          <PostponementOutcome consultation={all.find((c) => c.status === "REJECTED_BY_PATIENT")} role="doctor" />
          <p style={styles.subtitle}>{subtitle}</p>
          {doctorCard && (doctorCard.photo || doctorCard.first_name) ? (
            <div
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 14,
                marginBottom: 16,
                padding: 12,
                background: "#fff",
                border: "1px solid #d7e5f5",
                borderRadius: 12,
                maxWidth: 560,
                boxShadow: "0 4px 14px rgba(0,0,0,0.05)",
              }}
            >
              {doctorCard.photo ? (
                <img
                  src={doctorCard.photo}
                  alt=""
                  style={{
                    width: 64,
                    height: 64,
                    borderRadius: 12,
                    objectFit: "cover",
                    border: "1px solid #c6d7eb",
                    flexShrink: 0,
                  }}
                />
              ) : (
                <div
                  style={{
                    width: 64,
                    height: 64,
                    borderRadius: 12,
                    background: "#e6f0fb",
                    color: "#123a6f",
                    display: "grid",
                    placeItems: "center",
                    fontWeight: 800,
                    fontSize: 22,
                    flexShrink: 0,
                  }}
                  aria-hidden
                >
                  {(doctorCard.first_name?.[0] || "D") + (doctorCard.last_name?.[0] || "")}
                </div>
              )}
              <div style={{ minWidth: 0, flex: 1 }}>
                <div
                  style={{
                    fontWeight: 700,
                    color: "#113864",
                    fontSize: 16,
                    display: "flex",
                    flexWrap: "wrap",
                    alignItems: "center",
                    gap: "8px 10px",
                  }}
                >
                  <span>{formatDoctorDisplayName(doctorCard.first_name, doctorCard.last_name)}</span>
                  <DoctorProfileStatusBadges
                    adminVerified={doctorCard.admin_verified}
                    isApproved={doctorCard.is_approved}
                  />
                </div>
                <div style={{ fontSize: 13, color: "#304f72", marginTop: 8, lineHeight: 1.45 }}>
                  {(doctorCard.degree || doctorCard.qualification || "—").trim()}
                  {" · "}
                  {(doctorCard.specialty || "—").trim()}
                  {" · "}
                  {formatDoctorExperience(doctorCard.experience)}
                </div>
                <div style={{ fontSize: 13, color: "#4c6480", marginTop: 4, lineHeight: 1.45 }}>
                  {(() => {
                    const city = (doctorCard.city || "").trim();
                    const state = (doctorCard.state || "").trim();
                    if (city && state) return `${city} (${state})`;
                    if (city) return city;
                    if (state) return `(${state})`;
                    return "—";
                  })()}
                </div>
              </div>
            </div>
          ) : null}
          {renderMain()}
        </main>
        <Footer />
      </div>
      <ConsultationDetailModal
        consultation={selected}
        events={events}
        onClose={() => { setSelected(null); setPrescription(null); setRxVersions(null); }}
        viewerRole="doctor"
        actions={
          selected?.status === "IN_PROGRESS" && !selected?.is_completed ? (
            <button type="button" style={styles.completeBtn} disabled={busy} onClick={handleCompleteSelected}>
              Mark complete
            </button>
          ) : null
        }
      >
        {selected?.completion_required && selected?.status === "IN_PROGRESS" ? (
          <div style={styles.errorBanner} role="alert">
            <strong>Completion required.</strong> This consultation has been live for more than 24 hours.
            Mark it complete before continuing chat or video.
          </div>
        ) : selected ? (
          <ConsultationChatPanel consultationId={selected.id} status={selected.status} pollMs={5000} />
        ) : null}
        {selected ? (
          <DoctorPrescriptionPanel
            consultation={selected}
            prescription={prescription}
            onSaved={() => refreshPrescriptionDetail(selected.id)}
          />
        ) : null}
        {rxVersions && rxVersions.version_rows && rxVersions.version_rows.length > 0 ? (
          <div style={styles.rxBox}>
            <h4 style={{ margin: "0 0 8px", color: "#123a6f" }}>Prescription version history</h4>
            <p style={styles.rxMeta}>
              Last updated: {rxVersions.last_updated_at ? new Date(rxVersions.last_updated_at).toLocaleString() : "—"} ·{" "}
              {rxVersions.version_rows.length} snapshot(s) on file
            </p>
            <ul style={{ margin: 0, paddingLeft: 18, color: "#244a75", fontSize: 13 }}>
              {rxVersions.version_rows.map((row) => (
                <li key={row.id}>
                  v{row.version_number}
                  {row.created_by_email ? ` · ${row.created_by_email}` : ""}
                  {row.created_at ? ` · ${new Date(row.created_at).toLocaleString()}` : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </ConsultationDetailModal>
    </div>
  );
};

const MEDICINE_TYPE_OPTIONS = ["Tab", "Cap", "Syp", "Cream", "Drop", "Inj", "Inhaler", "Other"];
const FREQUENCY_OPTIONS = ["OD", "BD", "TDS", "QID", "SOS", "HS", "Weekly", "Other"];
const MEDICINE_NOTE_OPTIONS = [
  "Before breakfast",
  "After meal",
  "Before sleep at night",
  "After breakfast",
  "After lunch",
  "After dinner",
  "Empty stomach",
  "With warm water",
];

const emptyMedicineRow = () => ({
  rowKey: `${Date.now()}-${Math.random()}`,
  medicine_type: "Tab",
  name: "",
  strength: "",
  frequency: "BD",
  duration_days: "",
  notes: "",
});

const normalizeMedicineRows = (items) => {
  if (!Array.isArray(items) || items.length === 0) return [emptyMedicineRow()];
  return items.map((item) => {
    if (item && typeof item === "object" && !Array.isArray(item)) {
      return {
        rowKey: `${Date.now()}-${Math.random()}`,
        medicine_type: item.medicine_type || item.type || "Tab",
        name: item.name || "",
        strength: item.strength || item.dosage || item.power || "",
        frequency: item.frequency || "BD",
        duration_days: item.duration_days || item.days || item.duration || "",
        notes: item.notes || item.instructions || "",
      };
    }
    return {
      ...emptyMedicineRow(),
      name: String(item || ""),
      medicine_type: "Other",
      frequency: "Other",
    };
  });
};

const cleanMedicineRows = (rows) =>
  rows
    .map(({ medicine_type, name, strength, frequency, duration_days, notes }) => ({
      medicine_type: (medicine_type || "").trim(),
      name: (name || "").trim(),
      strength: (strength || "").trim(),
      frequency: (frequency || "").trim(),
      duration_days: String(duration_days || "").trim(),
      notes: (notes || "").trim(),
    }))
    .filter((row) => row.name || row.strength || row.notes);

const MedicineTable = ({ rows }) => (
  <div style={styles.rxTableWrap}>
    <table style={styles.rxTable}>
      <thead>
        <tr>
          <th style={styles.rxTh}>Sr.</th>
          <th style={styles.rxTh}>Type</th>
          <th style={styles.rxTh}>Medicine</th>
          <th style={styles.rxTh}>Strength</th>
          <th style={styles.rxTh}>Frequency</th>
          <th style={styles.rxTh}>Days</th>
          <th style={styles.rxTh}>Notes</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => (
          <tr key={`${row.name}-${index}`}>
            <td style={styles.rxTd}>{index + 1}</td>
            <td style={styles.rxTd}>{row.medicine_type || "-"}</td>
            <td style={styles.rxTd}>{row.name || "-"}</td>
            <td style={styles.rxTd}>{row.strength || "-"}</td>
            <td style={styles.rxTd}>{row.frequency || "-"}</td>
            <td style={styles.rxTd}>{row.duration_days || "-"}</td>
            <td style={styles.rxTd}>{row.notes || "-"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const DoctorPrescriptionPanel = ({ consultation, prescription, onSaved }) => {
  const [open, setOpen] = useState(false);
  const [medicineRows, setMedicineRows] = useState([emptyMedicineRow()]);
  const [instructions, setInstructions] = useState("Take medicines as prescribed. Follow up if symptoms persist.");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const canIssue = consultation?.status === "IN_PROGRESS" || consultation?.status === "COMPLETED";
  const canEdit = !!prescription?.can_edit_current;
  const hasPrescription = !!prescription?.id;

  useEffect(() => {
    if (!prescription) return;
    setMedicineRows(normalizeMedicineRows(prescription.medicines));
    setInstructions(prescription.instructions || "");
  }, [prescription]);

  const updateMedicineRow = (rowKey, field, value) => {
    setMedicineRows((rows) => rows.map((row) => (row.rowKey === rowKey ? { ...row, [field]: value } : row)));
  };

  const addMedicineRow = () => {
    setMedicineRows((rows) => [...rows, emptyMedicineRow()]);
  };

  const removeMedicineRow = (rowKey) => {
    setMedicineRows((rows) => (rows.length === 1 ? rows : rows.filter((row) => row.rowKey !== rowKey)));
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!canIssue) return;
    const medicines = cleanMedicineRows(medicineRows);
    if (!medicines.length) {
      setMessage("Add at least one medicine.");
      return;
    }
    const incomplete = medicines.find((row) => !row.medicine_type || !row.name || !row.strength || !row.frequency || !row.duration_days);
    if (incomplete) {
      setMessage("Complete type, medicine, strength, frequency, and days for every medicine row.");
      return;
    }
    setSaving(true);
    setMessage("");
    try {
      if (hasPrescription && canEdit) {
        await updatePrescription(consultation.id, medicines, instructions);
        setMessage("Prescription updated.");
      } else {
        await createPrescription(consultation.id, medicines, instructions);
        setMessage(hasPrescription ? "New prescription issued." : "Prescription issued.");
      }
      setOpen(false);
      await onSaved();
    } catch (error) {
      setMessage(error?.response?.data?.error || error?.message || "Could not save prescription.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={styles.rxBox}>
      <div style={styles.rxHeader}>
        <div>
          <h4 style={{ margin: 0, color: "#123a6f" }}>Prescription</h4>
          {hasPrescription ? (
            <p style={styles.rxMeta}>
              Last issued: {prescription.updated_at ? new Date(prescription.updated_at).toLocaleString() : "-"}
              {canEdit && prescription.edit_deadline ? ` - editable until ${new Date(prescription.edit_deadline).toLocaleTimeString()}` : " - edit window closed"}
            </p>
          ) : (
            <p style={styles.rxMeta}>No prescription has been issued for this consultation.</p>
          )}
        </div>
        <div style={styles.rowActions}>
          {hasPrescription ? (
            <button type="button" style={styles.secondaryBtn} onClick={() => downloadPrescriptionPdf(prescription.id)}>
              Download PDF
            </button>
          ) : null}
          <button type="button" style={styles.primaryBtn} disabled={!canIssue} onClick={() => setOpen((v) => !v)}>
            {hasPrescription ? (canEdit ? "Edit Prescription" : "Issue New Prescription") : "Prescribe"}
          </button>
        </div>
      </div>
      {!canIssue ? <p style={styles.rxMeta}>Start the consultation before issuing a prescription.</p> : null}
      {message ? <p style={{ ...styles.rxMeta, color: /Could|Add|Complete/i.test(message) ? "#8a1f1f" : "#17623c" }}>{message}</p> : null}
      {hasPrescription && prescription?.medicines?.length ? <MedicineTable rows={normalizeMedicineRows(prescription.medicines)} /> : null}
      {open ? (
        <form onSubmit={submit} style={styles.rxForm}>
          <div>
            <div style={styles.rxFormHeader}>
              <strong style={{ color: "#113864" }}>Medicine details</strong>
              <button type="button" style={styles.secondaryBtn} onClick={addMedicineRow}>
                + Add row
              </button>
            </div>
            <div style={styles.rxTableWrap}>
              <datalist id="medicine-note-options">
                {MEDICINE_NOTE_OPTIONS.map((option) => (
                  <option key={option} value={option} />
                ))}
              </datalist>
              <table style={styles.rxTable}>
                <thead>
                  <tr>
                    <th style={styles.rxTh}>Sr.</th>
                    <th style={styles.rxTh}>Type</th>
                    <th style={styles.rxTh}>Medicine name</th>
                    <th style={styles.rxTh}>Strength</th>
                    <th style={styles.rxTh}>Frequency</th>
                    <th style={styles.rxTh}>Days</th>
                    <th style={styles.rxTh}>Notes</th>
                    <th style={styles.rxTh}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {medicineRows.map((row, index) => (
                    <tr key={row.rowKey}>
                      <td style={styles.rxTd}>{index + 1}</td>
                      <td style={styles.rxTd}>
                        <select
                          style={styles.rxSmallInput}
                          value={row.medicine_type}
                          onChange={(e) => updateMedicineRow(row.rowKey, "medicine_type", e.target.value)}
                        >
                          {MEDICINE_TYPE_OPTIONS.map((option) => (
                            <option key={option} value={option}>{option}</option>
                          ))}
                        </select>
                      </td>
                      <td style={styles.rxTd}>
                        <input
                          style={styles.rxInput}
                          value={row.name}
                          onChange={(e) => updateMedicineRow(row.rowKey, "name", e.target.value)}
                          placeholder="Paracetamol"
                        />
                      </td>
                      <td style={styles.rxTd}>
                        <input
                          style={styles.rxSmallInput}
                          value={row.strength}
                          onChange={(e) => updateMedicineRow(row.rowKey, "strength", e.target.value)}
                          placeholder="500 mg"
                        />
                      </td>
                      <td style={styles.rxTd}>
                        <select
                          style={styles.rxSmallInput}
                          value={row.frequency}
                          onChange={(e) => updateMedicineRow(row.rowKey, "frequency", e.target.value)}
                        >
                          {FREQUENCY_OPTIONS.map((option) => (
                            <option key={option} value={option}>{option}</option>
                          ))}
                        </select>
                      </td>
                      <td style={styles.rxTd}>
                        <input
                          style={styles.rxTinyInput}
                          value={row.duration_days}
                          onChange={(e) => updateMedicineRow(row.rowKey, "duration_days", e.target.value.replace(/[^\d]/g, ""))}
                          placeholder="5"
                          inputMode="numeric"
                        />
                      </td>
                      <td style={styles.rxTd}>
                        <input
                          style={styles.rxInput}
                          value={row.notes}
                          list="medicine-note-options"
                          onChange={(e) => updateMedicineRow(row.rowKey, "notes", e.target.value)}
                          placeholder="Before sleep at night"
                        />
                      </td>
                      <td style={styles.rxTd}>
                        <button
                          type="button"
                          style={styles.rxRemoveBtn}
                          onClick={() => removeMedicineRow(row.rowKey)}
                          disabled={medicineRows.length === 1}
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <label style={styles.rxLabel}>
            Instructions
            <textarea
              style={{ ...styles.rxTextarea, minHeight: 82 }}
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="Advice, follow-up, precautions"
            />
          </label>
          <div style={styles.rowActions}>
            <button type="button" style={styles.secondaryBtn} onClick={() => setOpen(false)} disabled={saving}>
              Cancel
            </button>
            <button type="submit" style={styles.primaryBtn} disabled={saving}>
              {saving ? "Saving..." : hasPrescription && canEdit ? "Save Edit" : "Issue Prescription"}
            </button>
          </div>
        </form>
      ) : null}
    </div>
  );
};

const Metric = ({ label, value }) => (
  <article style={styles.metric}>
    <div style={styles.metricLabel}>{label}</div>
    <div style={styles.metricValue}>{value}</div>
  </article>
);

const RowCard = ({ consultation, label, actions, helper, emphasis }) => (
  <article style={{ ...styles.rowCard, ...(emphasis ? styles[`row${emphasis}`] : {}) }}>
    <div>
      <div style={styles.rowTitle}>
        Patient: {consultation.patient_name || "-"}
        {consultation.is_follow_up_request ? <span style={styles.followTag}>Follow-up</span> : null}
        {!consultation.is_follow_up_request && consultation.status === "PENDING" ? <span style={styles.newTag}>New request</span> : null}
        {consultation.video?.status === "REQUESTED" ? <span style={styles.videoTag}>Video waiting</span> : null}
        {consultation.video?.status === "ACCEPTED" ? <span style={styles.liveTag}>Video ready</span> : null}
        {label ? <span style={styles.queueTag}>{label}</span> : null}
      </div>
      <div style={styles.rowMeta}>
        {consultation.consultation_type} - {consultation.formatted_time}
        {consultation.is_follow_up_request ? ` - ${consultation.billing_type} follow-up` : ""}
        {consultation.tmc_name ? ` - TMC: ${consultation.tmc_name}` : ""}
      </div>
      <div style={{ marginTop: 6 }}>
        <StatusBadge status={consultation.status} />
      </div>
      {helper ? <p style={styles.helper}>{helper}</p> : null}
    </div>
    {actions}
  </article>
);

const Empty = ({ text }) => <p style={{ color: "#4c6480", margin: "4px 0" }}>{text}</p>;

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
  cards: { display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", gap: 12, marginTop: 8 },
  metric: { background: "#fff", border: DASHBOARD_BORDER, borderRadius: 14, padding: 14, boxShadow: DASHBOARD_SHADOW },
  metricLabel: { color: "#4c6480", fontSize: 12, fontWeight: 700 },
  metricValue: { color: "#113864", fontSize: "clamp(1.25rem, 4vw, 1.75rem)", fontWeight: 800 },
  section: { marginTop: 14, background: DASHBOARD_SECTION_BG, border: DASHBOARD_BORDER, borderRadius: 16, padding: 18, boxShadow: DASHBOARD_SHADOW },
  sectionTitle: { margin: 0, marginBottom: 10, color: "#123a6f", fontSize: "1.05rem" },
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
  noticeurgent: {
    background: "#fff1e8",
    borderColor: "#f0b27a",
    color: "#643000",
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
  noticeTitle: { fontWeight: 800, marginBottom: 3 },
  noticeBody: { fontSize: 14, lineHeight: 1.4 },
  noticeClose: {
    border: "1px solid rgba(18, 58, 111, 0.2)",
    background: "rgba(255,255,255,0.75)",
    color: "#123a6f",
    borderRadius: 8,
    width: 28,
    height: 28,
    fontWeight: 800,
    cursor: "pointer",
    lineHeight: "24px",
  },
  urgentPanel: {
    marginTop: 14,
    background: "#fff7ed",
    border: "1px solid #f0b27a",
    borderLeft: "6px solid #d96d16",
    borderRadius: 14,
    padding: 14,
    boxShadow: "0 10px 24px rgba(138, 75, 16, 0.14)",
    display: "flex",
    justifyContent: "space-between",
    gap: 14,
    alignItems: "flex-start",
    flexWrap: "wrap",
  },
  completionLockPanel: {
    marginTop: 14,
    background: "#fff4f0",
    border: "1px solid #f0a38c",
    borderLeft: "6px solid #b42318",
    borderRadius: 14,
    padding: 14,
    boxShadow: "0 10px 24px rgba(144, 38, 20, 0.14)",
    display: "flex",
    justifyContent: "space-between",
    gap: 14,
    alignItems: "flex-start",
    flexWrap: "wrap",
  },
  actionEyebrow: {
    color: "#8a1f1f",
    fontSize: 12,
    fontWeight: 900,
    textTransform: "uppercase",
    letterSpacing: 0,
    marginBottom: 4,
  },
  urgentTitle: { margin: 0, color: "#6f3505", fontSize: "1.05rem" },
  urgentText: { margin: "4px 0 0", color: "#74491d", fontSize: 13 },
  urgentList: { display: "grid", gap: 8, minWidth: 260, flex: "1 1 360px" },
  urgentItem: {
    background: "#fff",
    border: "1px solid #f1c294",
    borderRadius: 8,
    padding: "8px 10px",
    display: "grid",
    gap: 3,
    color: "#643000",
    fontSize: 13,
  },
  workflowHint: { color: "#74491d", fontSize: 12, fontWeight: 700 },
  card: { border: "1px solid #d7e5f5", borderRadius: 14, padding: 12, marginBottom: 10, background: "#fbfdff" },
  cardurgent: { borderColor: "#e28a2e", background: "#fffaf2", boxShadow: "0 8px 22px rgba(138, 75, 16, 0.12)" },
  cardfollow: { borderColor: "#91d0aa", background: "#f4fbf7", boxShadow: "0 8px 22px rgba(23, 98, 60, 0.1)" },
  rowCard: {
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
  rowurgent: { borderColor: "#e28a2e", background: "#fffaf2" },
  rowfollow: { borderColor: "#91d0aa", background: "#f4fbf7" },
  rowlive: { borderColor: "#91d0aa", background: "#f2fbf5" },
  rowTitle: { fontWeight: 700, color: "#113864", fontSize: 14 },
  rowMeta: { color: "#4c6480", fontSize: 13, marginTop: 4 },
  helper: { color: "#244a75", fontSize: 13, lineHeight: 1.4, margin: "8px 0 0" },
  idLine: {
    color: "#174577",
    background: "#edf4fd",
    border: "1px solid #c8ddf4",
    borderRadius: 8,
    padding: "7px 9px",
    margin: "8px 0",
    fontSize: 12,
    fontWeight: 700,
  },
  rowActions: { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" },
  queueTag: { marginLeft: 8, padding: "2px 8px", borderRadius: 999, background: "#efe9ff", color: "#4a2f9b", fontSize: 12 },
  followTag: { marginLeft: 8, padding: "2px 8px", borderRadius: 999, background: "#e8f7ef", color: "#17623c", fontSize: 12 },
  newTag: { marginLeft: 8, padding: "2px 8px", borderRadius: 999, background: "#fff1e8", color: "#8a4b10", fontSize: 12, fontWeight: 900 },
  videoTag: { marginLeft: 8, padding: "2px 8px", borderRadius: 999, background: "#fff8e8", color: "#624000", fontSize: 12, fontWeight: 900 },
  liveTag: { marginLeft: 8, padding: "2px 8px", borderRadius: 999, background: "#e8f7ef", color: "#17623c", fontSize: 12, fontWeight: 900 },
  primaryBtn: { background: "#1762bf", color: "#fff", border: "none", borderRadius: 10, padding: "8px 12px", fontWeight: 700, cursor: "pointer" },
  secondaryBtn: { background: "#edf4fd", color: "#174577", border: "1px solid #8ab0dc", borderRadius: 10, padding: "8px 12px", fontWeight: 700, cursor: "pointer" },
  completeBtn: { background: "#0d6e64", color: "#fff", border: "none", borderRadius: 10, padding: "8px 12px", fontWeight: 800, cursor: "pointer" },
  warnBtn: { background: "#fff7ed", color: "#8a4b10", border: "1px solid #ffca9f", borderRadius: 10, padding: "8px 12px", fontWeight: 700, cursor: "pointer" },
  input: { height: 42, borderRadius: 10, border: "1px solid #c6d7eb", padding: "0 12px", background: "#fbfdff", boxSizing: "border-box" },
  rxBox: { marginBottom: 14, background: "#fbfdff", border: "1px solid #d7e5f5", borderRadius: 10, padding: 12 },
  rxHeader: { display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", flexWrap: "wrap" },
  rxMeta: { color: "#4c6480", fontSize: 12, marginTop: 0, marginBottom: 8 },
  rxForm: { display: "grid", gap: 10, marginTop: 10 },
  rxFormHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, marginBottom: 8, flexWrap: "wrap" },
  rxLabel: { display: "grid", gap: 6, color: "#113864", fontWeight: 700, fontSize: 13 },
  rxTableWrap: { width: "100%", overflowX: "auto", border: "1px solid #d7e5f5", borderRadius: 8, background: "#fff", marginBottom: 10 },
  rxTable: { width: "100%", borderCollapse: "collapse", minWidth: 820, fontSize: 13 },
  rxTh: { textAlign: "left", color: "#113864", background: "#eef5fd", borderBottom: "1px solid #d7e5f5", padding: "8px 9px", whiteSpace: "nowrap" },
  rxTd: { borderBottom: "1px solid #edf3fa", padding: "8px 9px", verticalAlign: "middle", color: "#10243e" },
  rxInput: { width: "100%", minWidth: 130, boxSizing: "border-box", border: "1px solid #c6d7eb", borderRadius: 7, padding: "8px 9px", fontSize: 13, fontFamily: "inherit" },
  rxSmallInput: { width: "100%", minWidth: 92, boxSizing: "border-box", border: "1px solid #c6d7eb", borderRadius: 7, padding: "8px 9px", fontSize: 13, fontFamily: "inherit", background: "#fff" },
  rxTinyInput: { width: 68, boxSizing: "border-box", border: "1px solid #c6d7eb", borderRadius: 7, padding: "8px 9px", fontSize: 13, fontFamily: "inherit" },
  rxRemoveBtn: { background: "#fff5f5", color: "#8a1f1f", border: "1px solid #e4b1b1", borderRadius: 7, padding: "7px 9px", fontWeight: 700, cursor: "pointer" },
  rxTextarea: {
    width: "100%",
    minHeight: 120,
    boxSizing: "border-box",
    border: "1px solid #c6d7eb",
    borderRadius: 8,
    padding: "9px 10px",
    fontFamily: "inherit",
    fontSize: 14,
    resize: "vertical",
  },
  errorBanner: {
    background: "#fff4f0",
    border: "1px solid #f0b8a8",
    borderRadius: 12,
    padding: 14,
    marginBottom: 14,
    color: "#5c2a1a",
    fontSize: 14,
  },
  errorHint: { margin: "10px 0 0", fontSize: 12, color: "#6b442a" },
  retryBtn: {
    marginLeft: 8,
    background: "#1762bf",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    padding: "4px 10px",
    fontWeight: 700,
    cursor: "pointer",
  },
};

export default DoctorDashboard;
