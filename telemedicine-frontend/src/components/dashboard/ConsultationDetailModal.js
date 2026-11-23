import React, { useEffect, useRef, useState, useCallback, useMemo } from "react";
import StatusBadge from "./StatusBadge";
import ConsultationTimeline from "./ConsultationTimeline";
import VideoPanel from "./VideoPanel";
import { getConsultationVideoJoin, requestConsultationVideo, respondConsultationVideo } from "../../api/users";
import { isTerminalStatus, getStatusMessage } from "../../utils/consultationStatus";
import { shouldCloseVideo, shouldClearCredentials, cleanupVideoSession } from "../../utils/videoLifecycle";
import { getFriendlyVideoError } from "../../utils/videoErrors";
import InlineNotification from "./InlineNotification";

const ConsultationDetailModal = ({
  consultation,
  events,
  onClose,
  actions,
  children,
  viewerRole = "patient",
  onVideoStateChange,
  autoRequestVideo = false,
}) => {
  const [minimized, setMinimized] = useState(false);
  const [timelineOpen, setTimelineOpen] = useState(false);
  const [videoOpen, setVideoOpen] = useState(false);
  const [videoJoin, setVideoJoin] = useState(null);
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoError, setVideoError] = useState("");
  const [videoState, setVideoState] = useState(consultation?.video || { status: "NONE" });
  const previousStatusRef = useRef(null);
  const videoSessionRef = useRef(null);

  const consultationStatus = useMemo(() => ({
    status: consultation?.status,
    follow_up: consultation?.follow_up,
  }), [consultation?.status, consultation?.follow_up]);

  const handleSessionReady = useCallback((session) => {
    videoSessionRef.current = session;
  }, []);

  useEffect(() => {
    setVideoState(consultation?.video || { status: "NONE" });
  }, [
    consultation?.video?.id,
    consultation?.video?.status,
    consultation?.video?.provider,
    consultation?.video?.responded_at,
  ]);

  useEffect(() => {
    const currentEffectiveStatus = consultationStatus.follow_up?.active_status === "IN_PROGRESS"
      ? "IN_PROGRESS"
      : consultationStatus.status;

    if (shouldCloseVideo(consultationStatus, previousStatusRef.current)) {
      if (videoSessionRef.current) {
        cleanupVideoSession(videoSessionRef.current).catch((err) => {
          console.warn("Video cleanup error:", err);
        });
        videoSessionRef.current = null;
      }
      setVideoOpen(false);
      setVideoJoin(null);
      setVideoError("");
    }

    if (shouldClearCredentials(consultationStatus)) {
      setVideoJoin(null);
    }

    previousStatusRef.current = currentEffectiveStatus;
  }, [consultationStatus]);

  useEffect(() => {
    if (videoSessionRef.current) {
      cleanupVideoSession(videoSessionRef.current).catch((err) => {
        console.warn("Video cleanup on consultation switch:", err);
      });
      videoSessionRef.current = null;
    }
    setVideoState(consultation?.video || { status: "NONE" });
    setVideoJoin(null);
    setVideoOpen(false);
    setVideoError("");
    previousStatusRef.current = null;
  }, [
    consultation?.id,
    consultation?.video?.id,
    consultation?.video?.status,
    consultation?.video?.provider,
    consultation?.video?.responded_at,
  ]);

  useEffect(() => {
    return () => {
      if (videoSessionRef.current) {
        cleanupVideoSession(videoSessionRef.current).catch((err) => {
          console.warn("Video cleanup on unmount:", err);
        });
      }
    };
  }, []);

  if (!consultation) return null;

  const applyVideoState = (next) => {
    setVideoState(next);
    if (typeof onVideoStateChange === "function") {
      onVideoStateChange(next, consultation);
    }
  };

  const requestVideo = async () => {
    setVideoError("");
    setVideoLoading(true);
    try {
      const data = await requestConsultationVideo(consultation.id);
      applyVideoState(data.video || { status: "REQUESTED" });
      setVideoOpen(false);
    } catch (err) {
      setVideoError(getFriendlyVideoError(err, "Could not request video consultation."));
    } finally {
      setVideoLoading(false);
    }
  };

  const respondVideo = async (action) => {
    setVideoError("");
    setVideoLoading(true);
    try {
      const data = await respondConsultationVideo(consultation.id, action);
      applyVideoState(data.video || { status: action === "accept" ? "ACCEPTED" : "REJECTED" });
      setVideoOpen(false);
    } catch (err) {
      setVideoError(getFriendlyVideoError(err, "Could not respond to video request."));
    } finally {
      setVideoLoading(false);
    }
  };

  const openVideo = async () => {
    setVideoOpen(true);
    setVideoError("");
    if (videoJoin?.consultation_id === consultation.id) return;
    setVideoLoading(true);
    try {
      const data = await getConsultationVideoJoin(consultation.id);
      setVideoJoin(data);
    } catch (err) {
      setVideoError(getFriendlyVideoError(err, "Could not prepare video consultation."));
    } finally {
      setVideoLoading(false);
    }
  };

  useEffect(() => {
    if (!autoRequestVideo || !consultation?.id || viewerRole !== "doctor") return;
    if ((videoState?.status || "NONE") !== "NONE" && videoState?.status !== "REJECTED") return;
    requestVideo();
    // Intentionally run once when autoRequestVideo flips on for this consultation
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRequestVideo, consultation?.id]);

  const renderVideoActions = () => {
    const status = videoState?.status || "NONE";
    const consultationStatus = consultation?.follow_up?.active_status === "IN_PROGRESS"
      ? "IN_PROGRESS"
      : consultation?.status;

    if (isTerminalStatus(consultationStatus) && consultationStatus !== "IN_PROGRESS") {
      return null;
    }

    if (viewerRole === "doctor" && consultation?.completion_required) return null;
    if (viewerRole === "doctor") {
      if (status === "ACCEPTED") {
        return (
          <button type="button" onClick={openVideo} style={styles.primaryBtn}>
            {videoOpen ? "Video room" : "Join video"}
          </button>
        );
      }
      return (
        <button type="button" onClick={requestVideo} style={styles.primaryBtn} disabled={videoLoading}>
          {status === "NONE" ? "Request video" : "Request video again"}
        </button>
      );
    }
    if (status === "REQUESTED") {
      return (
        <>
          <button type="button" onClick={() => respondVideo("accept")} style={styles.primaryBtn} disabled={videoLoading}>
            Accept video
          </button>
          <button type="button" onClick={() => respondVideo("reject")} style={styles.cancelBtn} disabled={videoLoading}>
            Reject video
          </button>
        </>
      );
    }
    if (status === "ACCEPTED") {
      return (
        <button type="button" onClick={openVideo} style={styles.primaryBtn}>
          {videoOpen ? "Video room" : "Join video"}
        </button>
      );
    }
    return null;
  };

  if (minimized) {
    return (
      <div style={styles.minimizedBar}>
        <button type="button" style={styles.minimizedMain} onClick={() => setMinimized(false)}>
          Consultation #{consultation.id} - {consultation.patient_name || consultation.doctor_name || "Open"}
        </button>
        <button type="button" style={styles.minimizedClose} onClick={onClose} aria-label="Close consultation">
          x
        </button>
      </div>
    );
  }

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={styles.header}>
          <div>
            <h3 style={{ margin: 0, color: "#123a6f" }}>Consultation #{consultation.id}</h3>
            <div style={styles.headerMeta}>{consultation.consultation_label || consultation.status}</div>
          </div>
          <div style={styles.headerActions}>
            {actions}
            {renderVideoActions()}
            <button type="button" onClick={() => setTimelineOpen((v) => !v)} style={styles.ghostBtn}>
              {timelineOpen ? "Hide timeline" : "Show timeline"}
            </button>
            <button type="button" onClick={() => setMinimized(true)} style={styles.ghostBtn}>
              Minimize
            </button>
            <button type="button" onClick={onClose} style={styles.cancelBtn}>
              Close
            </button>
          </div>
        </div>

        <div style={styles.scrollBody}>
          {(() => {
            const statusMsg = getStatusMessage(consultation, viewerRole);
            return statusMsg ? (
              <InlineNotification
                type={statusMsg.severity}
                title={statusMsg.title}
                message={statusMsg.message}
              />
            ) : null;
          })()}

          <div style={styles.infoGrid}>
            <Info label="Doctor" value={consultation.doctor_name} />
            <Info label="Patient" value={consultation.patient_name} />
            <Info label="Type" value={consultation.consultation_type} />
            <div style={styles.infoItem}>
              <span style={styles.infoLabel}>Status</span>
              <StatusBadge status={consultation.status} />
            </div>
            {consultation.tmc_name ? <Info label="TMC" value={consultation.tmc_name} /> : null}
            {consultation.formatted_time ? <Info label="Scheduled" value={consultation.formatted_time} /> : null}
          </div>

          {timelineOpen ? (
            <section style={styles.timelineSection}>
              <h4 style={styles.timelineTitle}>Event timeline</h4>
              <div style={styles.timelineScroll}>
                <ConsultationTimeline events={events} />
              </div>
            </section>
          ) : null}

          {!videoOpen && videoState?.status === "REQUESTED" && viewerRole !== "doctor" ? (
            <div style={styles.videoNotice}>The doctor requested a video consultation. Accept when you are comfortable.</div>
          ) : null}
          {!videoOpen && videoState?.status === "REQUESTED" && viewerRole === "doctor" ? (
            <div style={styles.videoNotice}>Waiting for patient… Video request sent. Chat remains available.</div>
          ) : null}
          {!videoOpen && videoState?.status === "ACCEPTED" ? (
            <div style={styles.videoNotice}>
              {viewerRole === "doctor" ? "Patient accepted – join now when you are ready." : "Video is ready – join now when you are ready."}
            </div>
          ) : null}
          {!videoOpen && videoState?.status === "REJECTED" && viewerRole === "doctor" ? (
            <div style={styles.videoError}>Patient declined – continue in chat. You can request video again when ready.</div>
          ) : null}
          {!videoOpen && consultation?.completion_required && viewerRole === "doctor" ? (
            <div style={styles.videoError}>
              This consultation has been live for more than 24 hours. Mark it complete before continuing chat or video.
            </div>
          ) : null}
          {!videoOpen && videoError ? <div style={styles.videoError}>{videoError}</div> : null}

          {videoOpen ? (
            videoLoading ? (
              <div style={styles.videoNotice}>Preparing secure video room...</div>
            ) : videoError ? (
              <div style={styles.videoError}>{videoError}</div>
            ) : videoJoin ? (
              <VideoPanel 
                join={videoJoin} 
                onLeave={() => setVideoOpen(false)}
                onSessionReady={handleSessionReady}
              />
            ) : null
          ) : null}

          <div style={styles.contentPane}>{children}</div>
        </div>
      </div>
    </div>
  );
};

const Info = ({ label, value }) => (
  <div style={styles.infoItem}>
    <span style={styles.infoLabel}>{label}</span>
    <strong style={styles.infoValue}>{value || "-"}</strong>
  </div>
);

const styles = {
  overlay: {
    position: "fixed",
    inset: 0,
    backgroundColor: "rgba(0,0,0,0.45)",
    zIndex: 9999,
    display: "grid",
    placeItems: "center",
    padding: 18,
  },
  modal: {
    width: "min(1180px, 96vw)",
    maxHeight: "calc(100vh - 36px)",
    overflow: "hidden",
    background: "#fff",
    borderRadius: 12,
    border: "1px solid #d7e5f5",
    boxShadow: "0 10px 24px rgba(16, 36, 62, 0.2)",
    display: "flex",
    flexDirection: "column",
  },
  header: {
    position: "sticky",
    top: 0,
    zIndex: 2,
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
    padding: "14px 18px",
    background: "#fff",
    borderBottom: "1px solid #e2ecf7",
  },
  headerMeta: { color: "#4c6480", fontSize: 13, marginTop: 4 },
  headerActions: { display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" },
  scrollBody: {
    overflowY: "auto",
    padding: 18,
  },
  ghostBtn: {
    border: "1px solid #8ab0dc",
    background: "#edf4fd",
    color: "#174577",
    borderRadius: 8,
    padding: "8px 12px",
    fontWeight: 700,
    cursor: "pointer",
  },
  primaryBtn: {
    border: "none",
    background: "#1762bf",
    color: "#fff",
    borderRadius: 8,
    padding: "8px 12px",
    fontWeight: 800,
    cursor: "pointer",
  },
  videoNotice: {
    border: "1px solid #c8ddf4",
    background: "#edf4fd",
    color: "#174577",
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
    fontWeight: 700,
  },
  videoError: {
    border: "1px solid #efb4b4",
    background: "#fdeeee",
    color: "#711f1f",
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
    fontWeight: 700,
  },
  cancelBtn: {
    border: "1px solid #d6a4a4",
    background: "#fff5f5",
    color: "#8a1f1f",
    borderRadius: 8,
    padding: "8px 12px",
    fontWeight: 700,
    cursor: "pointer",
  },
  infoGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit,minmax(170px,1fr))",
    gap: 10,
    marginBottom: 14,
    background: "#fbfdff",
    border: "1px solid #d7e5f5",
    borderRadius: 12,
    padding: 12,
  },
  infoItem: { display: "flex", flexDirection: "column", gap: 4, minHeight: 42 },
  infoLabel: { color: "#4c6480", fontSize: 12, fontWeight: 700 },
  infoValue: { color: "#10243e", fontSize: 14 },
  timelineSection: { marginBottom: 16, minWidth: 0 },
  contentPane: { minWidth: 0 },
  timelineTitle: { color: "#123a6f", margin: "0 0 8px", fontSize: "1rem" },
  timelineScroll: {
    maxHeight: "min(260px, 32vh)",
    overflowY: "auto",
    paddingRight: 4,
  },
  minimizedBar: {
    position: "fixed",
    right: 18,
    bottom: 18,
    zIndex: 10000,
    display: "flex",
    alignItems: "center",
    gap: 8,
    background: "#123a6f",
    color: "#fff",
    borderRadius: 10,
    boxShadow: "0 12px 28px rgba(16,36,62,0.28)",
    padding: 8,
  },
  minimizedMain: { background: "transparent", border: 0, color: "#fff", fontWeight: 800, cursor: "pointer", padding: "8px 10px" },
  minimizedClose: { background: "#fff", border: 0, color: "#123a6f", borderRadius: 6, width: 28, height: 28, cursor: "pointer", fontWeight: 800 },
};

export default ConsultationDetailModal;
