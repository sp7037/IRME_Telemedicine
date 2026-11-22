import React, { useEffect, useMemo, useRef, useState } from "react";
import RealtimeKitClient from "@cloudflare/realtimekit";
import { getConsultationVideoJoin } from "../../api/users";

const normalizeCredentials = (payload) => {
  if (!payload) return null;

  const accountId = payload.account_id || payload.accountId;
  const appId = payload.app_id || payload.appId;
  const sessionId = payload.meeting_id || payload.session_id || payload.meetingId || payload.sessionId;
  const token = payload.participant_token || payload.auth_token || payload.authToken || payload.token;

  return {
    raw: payload,
    provider: payload.provider,
    consultationId: payload.consultation_id || payload.consultationId,
    participantId: payload.participant_id || payload.participantId,
    roomName: payload.room_name || payload.roomName || sessionId,
    accountId,
    appId,
    sessionId,
    token,
  };
};

const getFriendlyError = (err) => {
  const detail = err?.response?.data;
  const message = detail?.error || err?.message || "Could not start the video consultation.";

  if (err?.name === "NotAllowedError" || err?.name === "PermissionDeniedError") {
    return "Camera or microphone permission was denied. Please allow access and try joining again.";
  }
  if (err?.name === "NotFoundError" || err?.name === "DevicesNotFoundError") {
    return "No camera or microphone was found on this device.";
  }
  if (err?.name === "NotReadableError" || err?.name === "TrackStartError") {
    return "Your camera or microphone is already in use by another app.";
  }
  if (err?.code === "ERR_NETWORK" || message.toLowerCase().includes("network")) {
    return "Network error while preparing the secure video room. Please check your connection and try again.";
  }
  return message;
};

const isDeviceBusyError = (err) =>
  err?.name === "NotReadableError" ||
  err?.name === "TrackStartError" ||
  String(err?.message || "").toLowerCase().includes("already in use");

const toParticipantArray = (mapLike) => {
  if (!mapLike) return [];
  if (typeof mapLike.toArray === "function") return mapLike.toArray();
  if (typeof mapLike.values === "function") return Array.from(mapLike.values());
  if (Array.isArray(mapLike)) return mapLike;
  return [];
};

const addSdkListener = (target, eventName, handler) => {
  if (!target?.on) return () => {};
  target.on(eventName, handler);
  return () => {
    if (target.off) target.off(eventName, handler);
    else if (target.removeListener) target.removeListener(eventName, handler);
  };
};

const getAudioConstraints = () => ({
  echoCancellation: true,
  noiseSuppression: true,
  autoGainControl: true,
});

const getVideoConstraints = () => ({
  width: { ideal: 1280 },
  height: { ideal: 720 },
  frameRate: { ideal: 30, max: 30 },
  facingMode: "user",
});

const liveTrack = (track) => track && track.readyState === "live" ? track : null;

const mergeLocalTracks = (streamRef, newTracks) => {
  const current = streamRef.current;
  const tracks = [
    ...(current?.getTracks() || []).filter((track) => track.readyState === "live"),
    ...newTracks,
  ];
  streamRef.current = tracks.length ? new MediaStream(tracks) : null;
  return streamRef.current;
};

const VideoPanel = ({ join, consultationId, onLeave }) => {
  const [credentials, setCredentials] = useState(() => normalizeCredentials(join));
  const [loadingMessage, setLoadingMessage] = useState(join ? "" : "Preparing secure video room...");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadCredentials = async () => {
      if (join) {
        setCredentials(normalizeCredentials(join));
        setLoadingMessage("");
        setError("");
        return;
      }

      if (!consultationId) {
        setCredentials(null);
        setLoadingMessage("");
        setError("Missing consultation details for this video room.");
        return;
      }

      setLoadingMessage("Requesting secure video credentials...");
      setError("");

      try {
        const data = await getConsultationVideoJoin(consultationId);
        if (!cancelled) setCredentials(normalizeCredentials(data));
      } catch (err) {
        if (!cancelled) setError(getFriendlyError(err));
      } finally {
        if (!cancelled) setLoadingMessage("");
      }
    };

    loadCredentials();

    return () => {
      cancelled = true;
    };
  }, [join, consultationId]);

  const missingFields = useMemo(() => {
    if (!credentials) return [];
    return ["accountId", "appId", "sessionId", "token"].filter((key) => !credentials[key]);
  }, [credentials]);

  if (error) {
    return (
      <section style={styles.wrap}>
        <div style={styles.errorBox}>{error}</div>
      </section>
    );
  }

  if (loadingMessage || !credentials) {
    return (
      <section style={styles.wrap}>
        <div style={styles.notice}>{loadingMessage || "Preparing secure video room..."}</div>
      </section>
    );
  }

  if (missingFields.length) {
    return (
      <section style={styles.wrap}>
        <div style={styles.errorBox}>
          Missing Cloudflare video credentials: {missingFields.join(", ")}.
        </div>
      </section>
    );
  }

  return <CloudflareRoom credentials={credentials} onLeave={onLeave} />;
};

const CloudflareRoom = ({ credentials, onLeave }) => {
  const localVideoRef = useRef(null);
  const localStreamRef = useRef(null);
  const meetingRef = useRef(null);
  const participantCleanupsRef = useRef([]);

  const [meeting, setMeeting] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [status, setStatus] = useState("Requesting camera and microphone permission...");
  const [error, setError] = useState("");
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [deviceNotice, setDeviceNotice] = useState("");

  useEffect(() => {
    let cancelled = false;
    const cleanups = [];
    const localVideoEl = localVideoRef.current;

    const updateParticipants = (activeMeeting) => {
      const joined = toParticipantArray(activeMeeting?.participants?.joined);
      setParticipants(joined.filter(Boolean));
    };

    const connect = async () => {
      try {
        setError("");
        setDeviceNotice("");
        setStatus("Requesting camera and microphone permission...");

        if (!navigator.mediaDevices?.getUserMedia) {
          throw new Error("This browser does not support secure camera and microphone access.");
        }

        let localStream = null;
        try {
          localStream = await navigator.mediaDevices.getUserMedia({
            audio: getAudioConstraints(),
            video: getVideoConstraints(),
          });
        } catch (mediaErr) {
          if (!isDeviceBusyError(mediaErr)) throw mediaErr;
          setAudioEnabled(false);
          setVideoEnabled(false);
          setDeviceNotice("Joined without camera and microphone because this device is already using them.");
        }

        if (cancelled) {
          localStream?.getTracks().forEach((track) => track.stop());
          return;
        }

        localStreamRef.current = localStream;
        if (localVideoEl && localStream) {
          localVideoEl.srcObject = localStream;
        }

        setStatus("Connecting to Cloudflare video room...");

        const activeMeeting = await RealtimeKitClient.init({
          authToken: credentials.token,
          roomName: credentials.roomName,
          defaults: {
            audio: false,
            video: false,
          },
        });

        if (cancelled) {
          if (activeMeeting?.leave) await activeMeeting.leave();
          return;
        }

        meetingRef.current = activeMeeting;
        setMeeting(activeMeeting);

        const audioTrack = liveTrack(localStream?.getAudioTracks()[0]);
        const videoTrack = liveTrack(localStream?.getVideoTracks()[0]);

        if (audioTrack) await activeMeeting.self.enableAudio(audioTrack);
        if (videoTrack) await activeMeeting.self.enableVideo(videoTrack);

        await activeMeeting.join();

        cleanups.push(
          addSdkListener(activeMeeting.participants?.joined, "participantJoined", () => updateParticipants(activeMeeting)),
          addSdkListener(activeMeeting.participants?.joined, "participantLeft", () => updateParticipants(activeMeeting)),
          addSdkListener(activeMeeting.participants?.joined, "videoUpdate", () => updateParticipants(activeMeeting)),
          addSdkListener(activeMeeting.participants?.joined, "audioUpdate", () => updateParticipants(activeMeeting))
        );

        updateParticipants(activeMeeting);
        setStatus("Connected. Waiting for the other participant...");
      } catch (err) {
        if (!cancelled) {
          setStatus("");
          setError(getFriendlyError(err));
        }
      }
    };

    connect();

    return () => {
      cancelled = true;
      cleanups.forEach((cleanup) => cleanup());
      participantCleanupsRef.current.forEach((cleanup) => cleanup());
      participantCleanupsRef.current = [];
      if (meetingRef.current?.leave) {
        Promise.resolve(meetingRef.current.leave()).catch(() => {});
      }
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (localVideoEl) {
        localVideoEl.srcObject = null;
      }
      setMeeting(null);
    };
  }, [credentials]);

  const toggleAudio = async () => {
    if (!meetingRef.current) return;
    try {
      if (audioEnabled) {
        await meetingRef.current.self.disableAudio();
        localStreamRef.current?.getAudioTracks().forEach((track) => {
          track.stop();
        });
        localStreamRef.current = new MediaStream(localStreamRef.current?.getVideoTracks().filter((track) => track.readyState === "live") || []);
      } else {
        let track = liveTrack(localStreamRef.current?.getAudioTracks()[0]);
        if (!track) {
          const audioStream = await navigator.mediaDevices.getUserMedia({
            audio: getAudioConstraints(),
            video: false,
          });
          track = liveTrack(audioStream.getAudioTracks()[0]);
          mergeLocalTracks(localStreamRef, track ? [track] : []);
        }
        if (track) {
          track.enabled = true;
          await meetingRef.current.self.enableAudio(track);
        }
      }
      setAudioEnabled((value) => !value);
      setDeviceNotice("");
    } catch (err) {
      setError(getFriendlyError(err));
    }
  };

  const toggleVideo = async () => {
    if (!meetingRef.current) return;
    try {
      if (videoEnabled) {
        await meetingRef.current.self.disableVideo();
        localStreamRef.current?.getVideoTracks().forEach((track) => {
          track.stop();
        });
        localStreamRef.current = new MediaStream(localStreamRef.current?.getAudioTracks().filter((track) => track.readyState === "live") || []);
        if (localVideoRef.current) localVideoRef.current.srcObject = localStreamRef.current;
      } else {
        let track = liveTrack(localStreamRef.current?.getVideoTracks()[0]);
        if (!track) {
          const videoStream = await navigator.mediaDevices.getUserMedia({
            audio: false,
            video: getVideoConstraints(),
          });
          track = liveTrack(videoStream.getVideoTracks()[0]);
          const nextStream = mergeLocalTracks(localStreamRef, track ? [track] : []);
          if (localVideoRef.current) localVideoRef.current.srcObject = nextStream;
        }
        if (track) {
          track.enabled = true;
          await meetingRef.current.self.enableVideo(track);
        }
      }
      setVideoEnabled((value) => !value);
      setDeviceNotice("");
    } catch (err) {
      setError(getFriendlyError(err));
    }
  };

  const leaveRoom = async () => {
    setStatus("Leaving video room...");
    try {
      if (meetingRef.current?.leave) await meetingRef.current.leave();
    } finally {
      localStreamRef.current?.getTracks().forEach((track) => track.stop());
      onLeave?.();
      setStatus("Video room closed.");
    }
  };

  return (
    <section style={styles.wrap}>
      <div style={styles.header}>
        <div>
          <div style={styles.title}>Cloudflare video consultation</div>
          <div style={styles.meta}>Session {credentials.sessionId}</div>
        </div>
        <div style={styles.headerActions}>
          <button type="button" onClick={toggleAudio} style={styles.controlBtn} disabled={!meeting || Boolean(error)}>
            {audioEnabled ? "Mute" : "Unmute"}
          </button>
          <button type="button" onClick={toggleVideo} style={styles.controlBtn} disabled={!meeting || Boolean(error)}>
            {videoEnabled ? "Camera off" : "Camera on"}
          </button>
          <button type="button" onClick={leaveRoom} style={styles.leaveBtn}>
            Leave
          </button>
        </div>
      </div>

      {error ? <div style={styles.errorBox}>{error}</div> : null}
      {!error && deviceNotice ? <div style={styles.notice}>{deviceNotice}</div> : null}
      {!error && status ? <div style={styles.notice}>{status}</div> : null}

      <div style={styles.videoGrid}>
        <div style={styles.tile}>
          <video ref={localVideoRef} autoPlay playsInline muted style={styles.video} />
          <div style={styles.tileLabel}>You</div>
        </div>

        {participants.length ? (
          participants.map((participant) => (
            <RemoteParticipantTile key={participant.id} participant={participant} />
          ))
        ) : (
          <div style={styles.emptyTile}>Waiting for the other participant to join...</div>
        )}
      </div>
    </section>
  );
};

const RemoteParticipantTile = ({ participant }) => {
  const videoRef = useRef(null);
  const audioRef = useRef(null);
  const [soundBlocked, setSoundBlocked] = useState(false);

  useEffect(() => {
    const videoEl = videoRef.current;
    const audioEl = audioRef.current;

    const attachVideo = () => {
      if (!videoEl) return;
      if (participant?.registerVideoElement) {
        participant.registerVideoElement(videoEl);
      } else if (liveTrack(participant?.videoTrack)) {
        videoEl.srcObject = new MediaStream([participant.videoTrack]);
      }
    };

    const attachAudio = () => {
      if (!audioEl || !liveTrack(participant?.audioTrack)) return;
      audioEl.srcObject = new MediaStream([participant.audioTrack]);
      audioEl.play()
        .then(() => setSoundBlocked(false))
        .catch(() => setSoundBlocked(true));
    };

    attachVideo();
    attachAudio();

    const cleanupAudio = addSdkListener(participant, "audioUpdate", attachAudio);
    const cleanupVideo = addSdkListener(participant, "videoUpdate", attachVideo);

    return () => {
      cleanupAudio();
      cleanupVideo();
      if (videoEl && participant?.deregisterVideoElement) {
        participant.deregisterVideoElement(videoEl);
      }
      if (videoEl) videoEl.srcObject = null;
      if (audioEl) audioEl.srcObject = null;
    };
  }, [participant]);

  return (
    <div style={styles.tile}>
      <video ref={videoRef} autoPlay playsInline style={styles.video} />
      <audio ref={audioRef} autoPlay playsInline />
      {!participant?.videoEnabled ? <div style={styles.videoOff}>Camera off</div> : null}
      {soundBlocked ? (
        <button type="button" style={styles.soundBtn} onClick={() => audioRef.current?.play().then(() => setSoundBlocked(false)).catch(() => {})}>
          Enable sound
        </button>
      ) : null}
      <div style={styles.tileLabel}>{participant?.name || participant?.id || "Remote participant"}</div>
    </div>
  );
};

const styles = {
  wrap: {
    border: "1px solid #d7e5f5",
    borderRadius: 8,
    background: "#fbfdff",
    padding: 12,
    marginBottom: 14,
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
    marginBottom: 12,
  },
  title: {
    color: "#123a6f",
    fontWeight: 800,
    fontSize: 16,
  },
  meta: {
    color: "#5d7188",
    fontSize: 12,
    marginTop: 3,
    wordBreak: "break-all",
  },
  headerActions: {
    display: "flex",
    gap: 8,
    flexWrap: "wrap",
    justifyContent: "flex-end",
  },
  controlBtn: {
    border: "1px solid #b9cce0",
    background: "#fff",
    color: "#123a6f",
    borderRadius: 6,
    padding: "8px 12px",
    fontWeight: 700,
    cursor: "pointer",
  },
  leaveBtn: {
    border: "1px solid #c94f4f",
    background: "#fff4f4",
    color: "#8a1f1f",
    borderRadius: 6,
    padding: "8px 12px",
    fontWeight: 800,
    cursor: "pointer",
  },
  notice: {
    background: "#eef6ff",
    border: "1px solid #cfe3f8",
    color: "#335a82",
    borderRadius: 6,
    padding: "10px 12px",
    marginBottom: 12,
  },
  errorBox: {
    background: "#fff0f0",
    border: "1px solid #efb9b9",
    color: "#8a1f1f",
    borderRadius: 6,
    padding: "10px 12px",
    fontWeight: 700,
  },
  videoGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
    gap: 12,
  },
  tile: {
    position: "relative",
    minHeight: 260,
    aspectRatio: "16 / 10",
    overflow: "hidden",
    borderRadius: 8,
    background: "#071827",
  },
  video: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    display: "block",
    background: "#071827",
  },
  tileLabel: {
    position: "absolute",
    left: 10,
    bottom: 10,
    maxWidth: "calc(100% - 20px)",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    color: "#fff",
    background: "rgba(7, 24, 39, 0.78)",
    borderRadius: 6,
    padding: "6px 8px",
    fontSize: 12,
    fontWeight: 800,
  },
  videoOff: {
    position: "absolute",
    inset: 0,
    display: "grid",
    placeItems: "center",
    color: "#dce8f5",
    fontWeight: 800,
    background: "#071827",
  },
  soundBtn: {
    position: "absolute",
    right: 10,
    top: 10,
    border: "1px solid rgba(255,255,255,0.42)",
    background: "rgba(7, 24, 39, 0.82)",
    color: "#fff",
    borderRadius: 6,
    padding: "6px 8px",
    fontSize: 12,
    fontWeight: 800,
    cursor: "pointer",
  },
  emptyTile: {
    minHeight: 260,
    aspectRatio: "16 / 10",
    display: "grid",
    placeItems: "center",
    borderRadius: 8,
    color: "#dce8f5",
    background: "#071827",
    padding: 18,
    textAlign: "center",
    fontWeight: 700,
  },
};

export default VideoPanel;
