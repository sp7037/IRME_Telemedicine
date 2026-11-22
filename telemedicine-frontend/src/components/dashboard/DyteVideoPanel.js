import React, { useEffect, useRef, useState } from "react";

const CORE_SRC = "https://cdn.dyte.in/core/dyte.js";
const UI_SRC = "https://cdn.jsdelivr.net/npm/@dytesdk/ui-kit/loader/index.es2017.js";
let dyteInitQueue = Promise.resolve();

const loadScript = (src) =>
  new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      if (existing.dataset.loaded === "true") resolve();
      else existing.addEventListener("load", resolve, { once: true });
      return;
    }
    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.onload = () => {
      script.dataset.loaded = "true";
      resolve();
    };
    script.onerror = () => reject(new Error(`Could not load ${src}`));
    document.head.appendChild(script);
  });

const DyteVideoPanel = ({ join }) => {
  const hostRef = useRef(null);
  const meetingRef = useRef(null);
  const [status, setStatus] = useState("Preparing video room...");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const hostEl = hostRef.current;

    const start = async () => {
      if (!join?.auth_token || !hostEl) return;
      setError("");
      setStatus("Loading video call...");
      try {
        await loadScript(CORE_SRC);
        const uiModule = await import(/* webpackIgnore: true */ UI_SRC);
        if (uiModule?.defineCustomElements) {
          await uiModule.defineCustomElements();
        }
        if (!window.DyteClient) {
          throw new Error("Dyte client did not load.");
        }
        const initMeeting = () =>
          window.DyteClient.init({
            authToken: join.auth_token,
            defaults: { audio: true, video: true },
          });
        const meetingPromise = dyteInitQueue.catch(() => {}).then(initMeeting);
        dyteInitQueue = meetingPromise.catch(() => {});
        const meeting = await meetingPromise;
        if (cancelled) {
          try {
            meeting.leave();
          } catch (err) {
            // Ignore cleanup errors.
          }
          return;
        }
        meetingRef.current = meeting;
        hostEl.innerHTML = "";
        const el = document.createElement("dyte-meeting");
        el.setAttribute("mode", "fill");
        el.setAttribute("show-setup-screen", "true");
        el.style.height = "620px";
        el.style.width = "100%";
        el.meeting = meeting;
        hostEl.appendChild(el);
        setStatus("");
      } catch (err) {
        setError(err?.message || "Could not start video call.");
        setStatus("");
      }
    };

    start();
    return () => {
      cancelled = true;
      if (meetingRef.current?.leave) {
        try {
          meetingRef.current.leave();
        } catch (err) {
          // Ignore cleanup errors.
        }
      }
      if (hostEl) hostEl.innerHTML = "";
    };
  }, [join]);

  return (
    <section style={styles.wrap}>
      {status ? <p style={styles.muted}>{status}</p> : null}
      {error ? <p style={styles.error}>{error}</p> : null}
      <div ref={hostRef} style={styles.videoHost} />
    </section>
  );
};

const styles = {
  wrap: {
    border: "1px solid #d7e5f5",
    borderRadius: 14,
    background: "#fbfdff",
    padding: 12,
    marginBottom: 14,
  },
  videoHost: {
    minHeight: 360,
    width: "100%",
    overflow: "hidden",
    borderRadius: 12,
    background: "#071827",
  },
  muted: { color: "#4c6480", margin: "0 0 10px" },
  error: { color: "#8a1f1f", margin: "0 0 10px", fontWeight: 700 },
};

export default DyteVideoPanel;
