import React, { useMemo, useState } from "react";
import { API_BASE_URL } from "../../api/config";
import { DISPLAY_PHONE, SUPPORT_EMAIL, whatsappUrl } from "../../constants/marketingContact";

const emptyForm = {
  name: "",
  phone: "",
  email: "",
  state: "",
  city: "",
  message: "",
};

const LeadCaptureForm = ({ interest = "GENERAL", title = "Request a callback", locationLabel = "", messageHint = "" }) => {
  const [form, setForm] = useState({ ...emptyForm, message: messageHint });
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const startedAt = useMemo(() => Date.now(), []);

  const onChange = (event) => setForm({ ...form, [event.target.name]: event.target.value });

  const onSubmit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setStatus("");
    try {
      const response = await fetch(`${API_BASE_URL}/marketing/callback/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          interest,
          ...form,
          website: "",
          started_at: startedAt,
          source_path: window.location.pathname,
        }),
      });
      if (!response.ok) throw new Error("Could not submit callback request.");
      setStatus("Thanks. Our team will contact you soon.");
      setForm(emptyForm);
    } catch (error) {
      setStatus(`Please WhatsApp us or email ${SUPPORT_EMAIL}.`);
    } finally {
      setBusy(false);
    }
  };

  const whatsAppMessage = `Hello IRME, I want details about ${title}${locationLabel ? ` in ${locationLabel}` : ""}. My name is ${form.name || ""}.`;

  return (
    <section style={styles.wrap}>
      <div>
        <h2 style={styles.title}>{title}</h2>
        <p style={styles.text}>
          Share your number for a counselling call, or message us directly on WhatsApp at {DISPLAY_PHONE}.
        </p>
      </div>
      <form onSubmit={onSubmit} style={styles.form}>
        <input
          name="website"
          tabIndex="-1"
          autoComplete="off"
          aria-hidden="true"
          style={styles.honeypot}
          onChange={() => {}}
        />
        <input name="name" required placeholder="Full name" value={form.name} onChange={onChange} style={styles.input} />
        <input name="phone" required placeholder="Mobile number" value={form.phone} onChange={onChange} style={styles.input} />
        <input name="email" type="email" placeholder="Email optional" value={form.email} onChange={onChange} style={styles.input} />
        <input name="city" placeholder="City" value={form.city} onChange={onChange} style={styles.input} />
        <input name="state" placeholder="State" value={form.state} onChange={onChange} style={styles.input} />
        <textarea name="message" placeholder="What do you want to know?" value={form.message} onChange={onChange} rows={3} style={{ ...styles.input, height: "auto", paddingTop: 10 }} />
        <div style={styles.actions}>
          <button type="submit" disabled={busy} style={styles.primary}>{busy ? "Sending..." : "Request callback"}</button>
          <a href={whatsappUrl(whatsAppMessage)} target="_blank" rel="noreferrer" style={styles.whatsapp}>WhatsApp now</a>
        </div>
        {status ? <p style={styles.status}>{status}</p> : null}
      </form>
    </section>
  );
};

const styles = {
  wrap: {
    border: "1px solid #b8dbc7",
    borderRadius: 14,
    background: "#f1fbf5",
    padding: 18,
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
    gap: 18,
    alignItems: "start",
  },
  title: { margin: "0 0 6px", color: "#123a6f", fontSize: "1.25rem" },
  text: { margin: 0, color: "#34506f", lineHeight: 1.55 },
  form: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 10 },
  input: { border: "1px solid #bcd0e6", borderRadius: 8, padding: "10px 11px", font: "inherit", minWidth: 0 },
  honeypot: { position: "absolute", left: "-10000px", width: 1, height: 1, opacity: 0 },
  actions: { display: "flex", gap: 10, flexWrap: "wrap", gridColumn: "1 / -1" },
  primary: { border: 0, borderRadius: 8, background: "#1762bf", color: "#fff", padding: "10px 14px", fontWeight: 800, cursor: "pointer" },
  whatsapp: { borderRadius: 8, background: "#16a34a", color: "#fff", padding: "10px 14px", fontWeight: 800, textDecoration: "none" },
  status: { gridColumn: "1 / -1", margin: 0, color: "#17623c", fontWeight: 700 },
};

export default LeadCaptureForm;
