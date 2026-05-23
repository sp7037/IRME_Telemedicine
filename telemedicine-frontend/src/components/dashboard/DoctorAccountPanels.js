import React, { useEffect, useState } from "react";
import {
  getDoctorProfile,
  updateDoctorProfile,
  lookupPincode,
  getDoctorAvailability,
  updateDoctorAvailability,
  getDoctorSchedules,
  createDoctorSchedule,
  updateDoctorSchedule,
  deleteDoctorSchedule,
} from "../../api/users";
import { setAuthItem } from "../../utils/authSession";
import { INDIAN_STATES_AND_UTS } from "../../constants/indianStates";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const DOCTOR_PROFILE_TEXT_FIELDS = [
  ["qualification", "Qualification"],
  ["degree", "Degree"],
  ["college_university_name", "College / University"],
  ["passing_year", "Passing year"],
  ["specialty", "Specialty"],
  ["experience", "Experience"],
  ["license_number", "License number"],
  ["registration_number", "Registration number"],
  ["state_medical_council", "State medical council"],
  ["major_diseases_specializations", "Major diseases / specializations"],
  ["previous_hospitals_served", "Previous hospitals"],
  ["hospital_or_clinic_name", "Hospital or clinic name"],
  ["consultation_fee", "Consultation fee"],
  ["max_daily_consultations", "Max daily consultations"],
];

const card = {
  background: "#fff",
  border: "1px solid #d7e5f5",
  borderRadius: 14,
  padding: 16,
  boxShadow: "0 8px 20px rgba(0,0,0,0.06)",
  marginBottom: 14,
};
const label = { display: "block", fontSize: 13, fontWeight: 700, color: "#244a75", marginBottom: 6 };
const input = {
  width: "100%",
  maxWidth: 480,
  height: 40,
  borderRadius: 8,
  border: "1px solid #c6d7eb",
  padding: "0 10px",
  fontSize: 14,
  boxSizing: "border-box",
};
const btnPrimary = {
  background: "#1762bf",
  color: "#fff",
  border: "none",
  borderRadius: 8,
  padding: "10px 18px",
  fontWeight: 700,
  cursor: "pointer",
  marginTop: 12,
};
const title = { margin: "0 0 12px", color: "#123a6f" };
const muted = { color: "#4c6480", fontSize: 14 };
const smallButton = {
  border: "1px solid #c6d7eb",
  background: "#fff",
  color: "#123a6f",
  borderRadius: 8,
  padding: "8px 10px",
  fontWeight: 700,
  cursor: "pointer",
};
const noticeCard = {
  border: "1px solid #b7d4f4",
  background: "#f2f7ff",
  color: "#123a6f",
  borderRadius: 10,
  padding: "12px 14px",
  marginBottom: 14,
  lineHeight: 1.45,
};
const modalOverlay = {
  position: "fixed",
  inset: 0,
  background: "rgba(8, 28, 52, 0.42)",
  zIndex: 1100,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 20,
};
const modalBox = {
  width: "min(520px, 100%)",
  background: "#fff",
  borderRadius: 12,
  border: "1px solid #d7e5f5",
  boxShadow: "0 24px 60px rgba(12, 35, 68, 0.26)",
  padding: 22,
};

function extractApiError(error, fallback) {
  const data = error.response?.data;
  if (!data) return error.message || fallback;
  if (typeof data === "string") return data;
  if (data.detail || data.error || data.message) return data.detail || data.error || data.message;
  const firstKey = Object.keys(data)[0];
  const firstValue = firstKey ? data[firstKey] : null;
  if (Array.isArray(firstValue)) return `${firstKey}: ${firstValue.join(", ")}`;
  if (typeof firstValue === "string") return `${firstKey}: ${firstValue}`;
  return fallback;
}

function fileLabelFromUrl(url, fallback = "document") {
  if (!url || typeof url !== "string") return fallback;
  try {
    const path = new URL(url).pathname;
    const base = path.split("/").filter(Boolean).pop();
    return base ? decodeURIComponent(base) : fallback;
  } catch {
    return fallback;
  }
}

function CurrentDoctorDocumentCard({ title, url, showImagePreview }) {
  const linkStyle = { color: "#1762bf", fontWeight: 700, fontSize: 13 };
  if (!url) {
    return (
      <div
        style={{
          marginBottom: 12,
          padding: 10,
          border: "1px solid #e8eef5",
          borderRadius: 8,
          background: "#fafcfe",
        }}
      >
        <div style={{ fontWeight: 700, color: "#123a6f", marginBottom: 4 }}>{title}</div>
        <p style={{ ...muted, margin: 0, fontSize: 13 }}>No file on record yet.</p>
      </div>
    );
  }
  const name = fileLabelFromUrl(url, title);
  const canThumb =
    !!showImagePreview && /\.(jpe?g|png|gif|webp|bmp)(\?|#|$)/i.test(url);
  const preview = canThumb ? (
    <img
      src={url}
      alt=""
      style={{
        maxWidth: 160,
        maxHeight: 160,
        borderRadius: 8,
        objectFit: "cover",
        display: "block",
        marginBottom: 8,
        border: "1px solid #e0eaf5",
      }}
    />
  ) : null;
  return (
    <div
      style={{
        marginBottom: 12,
        padding: 12,
        border: "1px solid #e0eaf5",
        borderRadius: 10,
        background: "#fbfdff",
      }}
    >
      <div style={{ fontWeight: 700, color: "#123a6f", marginBottom: 8 }}>{title}</div>
      {preview}
      {!preview ? (
        <p style={{ ...muted, margin: "0 0 8px", fontSize: 13 }}>
          Saved document — open or download to view.
        </p>
      ) : null}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
        <a href={url} target="_blank" rel="noopener noreferrer" style={linkStyle}>
          Open in new tab
        </a>
        <a href={url} download={name} target="_blank" rel="noopener noreferrer" style={linkStyle}>
          Download
        </a>
      </div>
      <div style={{ fontSize: 12, color: "#6b829e", marginTop: 8, wordBreak: "break-all" }}>{name}</div>
    </div>
  );
}

/** Avoid "Dr. Dr." when first_name already starts with Dr. */
export function formatDoctorDisplayName(firstName, lastName) {
  const f = (firstName || "").trim();
  const l = (lastName || "").trim();
  const combined = `${f} ${l}`.trim();
  if (!combined) return "Doctor";
  if (/^dr\.?\s/i.test(f)) return combined;
  return `Dr. ${combined}`;
}

export function DoctorProfileStatusBadges({ adminVerified, isApproved }) {
  const pill = (ok, okLabel, pendingLabel, colorsOk, colorsPending) => (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 999,
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: "0.01em",
        ...(ok ? colorsOk : colorsPending),
        whiteSpace: "nowrap",
      }}
    >
      {ok ? okLabel : pendingLabel}
    </span>
  );
  return (
    <span style={{ display: "inline-flex", flexWrap: "wrap", gap: "4px 6px", alignItems: "center" }}>
      {pill(
        !!adminVerified,
        "Verified",
        "Pending",
        { background: "#e3f8ea", color: "#146c32", border: "1px solid #b8e2c8" },
        { background: "#fff4cc", color: "#8a6d00", border: "1px solid #f0d68a" }
      )}
      {pill(
        !!isApproved,
        "Active",
        "Inactive",
        { background: "#e4efff", color: "#1f4f8f", border: "1px solid #b8cdf0" },
        { background: "#fde8e8", color: "#9d1d1d", border: "1px solid #f5bcbc" }
      )}
    </span>
  );
}

export function DoctorProfilePanel() {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({
    qualification: "",
    degree: "",
    college_university_name: "",
    passing_year: "",
    specialty: "",
    experience: "",
    license_number: "",
    registration_number: "",
    state_medical_council: "",
    major_diseases_specializations: "",
    previous_hospitals_served: "",
    hospital_or_clinic_name: "",
    clinic_address_street: "",
    city: "",
    state: "",
    pin_code: "",
    consultation_modes: [],
    consultation_fee: "",
    max_daily_consultations: "",
  });
  const [photoFile, setPhotoFile] = useState(null);
  const [identityFile, setIdentityFile] = useState(null);
  const [certFile, setCertFile] = useState(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  const [pinLookupLoading, setPinLookupLoading] = useState(false);
  const [pinLookupErr, setPinLookupErr] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const p = await getDoctorProfile();
        setProfile(p);
        if (p) {
          setForm({
            qualification: p.qualification || "",
            degree: p.degree || p.qualification || "",
            college_university_name: p.college_university_name || "",
            passing_year: p.passing_year || "",
            specialty: p.specialty || "",
            experience: p.experience || "",
            license_number: p.license_number || "",
            registration_number: p.registration_number || "",
            state_medical_council: p.state_medical_council || "",
            major_diseases_specializations: p.major_diseases_specializations || "",
            previous_hospitals_served: p.previous_hospitals_served || "",
            hospital_or_clinic_name: p.hospital_or_clinic_name || "",
            clinic_address_street: p.clinic_address_street || "",
            city: p.city || "",
            state: p.state || "",
            pin_code: p.pin_code || "",
            consultation_modes: p.consultation_modes || [],
            consultation_fee: p.consultation_fee || "",
            max_daily_consultations: p.max_daily_consultations || "",
          });
        }
      } catch (e) {
        setErr(e.message || "Failed to load profile");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const runPinLookup = async (pinOverride) => {
    const pin = String(pinOverride ?? form.pin_code ?? "").trim();
    if (!/^\d{6}$/.test(pin)) {
      setPinLookupErr("Enter a 6-digit PIN code.");
      return;
    }
    setPinLookupErr("");
    setPinLookupLoading(true);
    try {
      const data = await lookupPincode(pin);
      setForm((f) => ({
        ...f,
        pin_code: data.pincode || pin,
        state: data.state || f.state,
        city: data.district || f.city,
      }));
    } catch (e) {
      const detail =
        e.response?.data?.error ||
        e.response?.data?.detail ||
        (typeof e.response?.data === "string" ? e.response.data : null);
      setPinLookupErr(detail || e.message || "Could not look up this PIN.");
    } finally {
      setPinLookupLoading(false);
    }
  };

  const handlePinBlur = () => {
    const pin = String(form.pin_code || "").trim();
    if (/^\d{6}$/.test(pin)) runPinLookup(pin);
  };

  const toggleMode = (mode) => {
    const modes = form.consultation_modes || [];
    setForm({
      ...form,
      consultation_modes: modes.includes(mode) ? modes.filter((item) => item !== mode) : [...modes, mode],
    });
  };

  const showToast = (type, heading, body) => {
    setToast({ type, heading, body });
    window.setTimeout(() => setToast(null), 5200);
  };

  const saveProfile = async () => {
    setErr("");
    setMsg("");
    setSaving(true);
    try {
      const result = await updateDoctorProfile({
        ...form,
        ...(photoFile ? { photo: photoFile } : {}),
        ...(identityFile ? { identity_proof: identityFile } : {}),
        ...(certFile ? { registration_certificate: certFile } : {}),
      });
      const isChangeRequest = !!result?.change_request_created;
      const successMessage =
        result?.message ||
        (isChangeRequest
          ? "Profile change request submitted for admin approval."
          : "Profile submitted successfully. Admin verification is required.");
      setMsg(successMessage);
      showToast(
        "success",
        isChangeRequest ? "Change request submitted" : "Profile submitted",
        successMessage
      );
      setPhotoFile(null);
      setIdentityFile(null);
      setCertFile(null);
      const p = await getDoctorProfile();
      setProfile(p);
      window.dispatchEvent(new Event("irme-doctor-profile-refresh"));
      setAuthItem(
        "doctorOnboarding",
        JSON.stringify({
          profile_completed: !!p?.profile_completed,
          admin_verified: !!p?.admin_verified,
          is_approved: !!p?.is_approved,
          next_step: !p?.profile_completed
            ? "COMPLETE_PROFILE"
            : !p?.admin_verified
              ? "AWAIT_PROFILE_VERIFICATION"
              : !p?.is_approved
                ? "AWAIT_CONSULTATION_APPROVAL"
                : "DASHBOARD",
        })
      );
    } catch (e2) {
      const errorMessage = e2.message || "Update failed";
      setErr(errorMessage);
      showToast("error", "Profile not saved", errorMessage);
    } finally {
      setSaving(false);
      setShowSubmitConfirm(false);
    }
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!profile?.profile_completed) {
      setShowSubmitConfirm(true);
      return;
    }
    await saveProfile();
  };

  if (loading) return <p style={muted}>Loading profile…</p>;

  return (
    <div>
      {toast ? (
        <div
          role={toast.type === "error" ? "alert" : "status"}
          style={{
            position: "fixed",
            top: 88,
            right: 22,
            zIndex: 1200,
            width: "min(420px, calc(100vw - 32px))",
            background: "#fff",
            border: `1px solid ${toast.type === "error" ? "#efb4b4" : "#adddc6"}`,
            borderLeft: `6px solid ${toast.type === "error" ? "#d93838" : "#0f9d58"}`,
            borderRadius: 12,
            boxShadow: "0 18px 42px rgba(12, 35, 68, 0.18)",
            padding: "14px 42px 14px 16px",
            color: "#123a6f",
          }}
        >
          <strong style={{ display: "block", fontSize: 16, marginBottom: 4 }}>{toast.heading}</strong>
          <span style={{ display: "block", color: "#304f72", lineHeight: 1.45 }}>{toast.body}</span>
          <button
            type="button"
            onClick={() => setToast(null)}
            aria-label="Close notification"
            style={{
              position: "absolute",
              top: 8,
              right: 8,
              border: 0,
              background: "transparent",
              color: "#426382",
              fontSize: 22,
              lineHeight: 1,
              cursor: "pointer",
            }}
          >
            x
          </button>
        </div>
      ) : null}
      {showSubmitConfirm ? (
        <div style={modalOverlay} role="dialog" aria-modal="true" aria-labelledby="doctor-profile-confirm-title">
          <div style={modalBox}>
            <h3 id="doctor-profile-confirm-title" style={{ ...title, fontSize: 22 }}>
              Submit profile for verification?
            </h3>
            <p style={{ ...muted, lineHeight: 1.55 }}>
              Please review your doctor profile carefully before saving. After this submission, the approved profile
              cannot be changed directly. Any future edits will be sent as a change request and become active only after
              admin verification.
            </p>
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", flexWrap: "wrap", marginTop: 18 }}>
              <button type="button" style={smallButton} onClick={() => setShowSubmitConfirm(false)} disabled={saving}>
                Review again
              </button>
              <button type="button" style={btnPrimary} onClick={saveProfile} disabled={saving}>
                {saving ? "Submitting..." : "Submit for admin verification"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
      <h2 style={title}>Doctor profile</h2>
      {!profile ? (
        <p style={muted}>Complete all professional details before using doctor features.</p>
      ) : (
        <p style={{ ...muted, marginBottom: 4 }}>
          {formatDoctorDisplayName(profile.first_name, profile.last_name)} · {profile.email}
          {profile.completion_percentage != null ? ` · ${profile.completion_percentage}% complete` : ""}
        </p>
      )}
      {err ? <p style={{ color: "#b00020" }}>{err}</p> : null}
      {msg ? <p style={{ color: "#1b5e20" }}>{msg}</p> : null}
      {!profile?.profile_completed ? (
        <div style={noticeCard}>
          <strong>Review before final submission.</strong> Once this profile is submitted, future changes will require
          admin verification before they become active.
        </div>
      ) : null}
      {profile?.has_pending_changes ? (
        <div style={{ ...noticeCard, borderColor: "#f0d18b", background: "#fff8e8", color: "#694c00" }}>
          <strong>Profile change request(s) pending admin review.</strong>
          {profile.pending_change_requests?.length ? (
            <ul style={{ margin: "10px 0 0", paddingLeft: 22, lineHeight: 1.55 }}>
              {profile.pending_change_requests.map((req) => (
                <li key={req.id}>
                  <strong>Request #{req.id}</strong>
                  {req.requested_at ? (
                    <span style={{ fontWeight: 400 }}>
                      {" "}
                      · {new Date(req.requested_at).toLocaleString()}
                    </span>
                  ) : null}
                  : {(req.summary_parts || []).join(", ") || "Updates awaiting review"}
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ margin: "8px 0 0", fontSize: 14 }}>
              Your current verified profile and documents stay active. Submits and new file uploads are disabled until an
              admin reviews your request.
            </p>
          )}
          <p style={{ margin: "12px 0 0", fontSize: 13, opacity: 0.95 }}>
            Up to three requests may be queued at once. Replacements apply only after approval.
          </p>
        </div>
      ) : null}
      <form onSubmit={onSubmit} style={{ marginTop: 16, position: "relative" }}>
        {saving ? (
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: "rgba(255,255,255,0.9)",
              zIndex: 8,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 14,
              borderRadius: 14,
              padding: 24,
              textAlign: "center",
            }}
            aria-busy="true"
            aria-live="polite"
          >
            <strong style={{ color: "#123a6f", fontSize: 17 }}>Saving your profile…</strong>
            <p style={{ ...muted, margin: 0, maxWidth: 340 }}>
              Uploading photos and documents can take up to a minute. Please keep this page open.
            </p>
            <progress style={{ width: "min(280px, 90%)", height: 14 }} />
          </div>
        ) : null}
        <div style={saving ? { opacity: 0.55, pointerEvents: "none" } : undefined}>
          <div style={card}>
            <h3 style={{ ...title, fontSize: 17 }}>Clinic address</h3>
            <p style={{ ...muted, marginTop: 0 }}>
              Enter your 6-digit PIN code first — we fill state and district when possible (you can edit them). Then add
              street details.
            </p>
            <div style={{ marginBottom: 12 }}>
              <label style={label}>PIN code</label>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center", maxWidth: 480 }}>
                <input
                  name="pin_code"
                  value={form.pin_code || ""}
                  onChange={onChange}
                  onBlur={handlePinBlur}
                  style={{ ...input, maxWidth: 160 }}
                  maxLength={6}
                  inputMode="numeric"
                  autoComplete="postal-code"
                  placeholder="e.g. 110001"
                />
                <button
                  type="button"
                  style={{ ...smallButton, marginTop: 0 }}
                  onClick={() => runPinLookup()}
                  disabled={pinLookupLoading}
                >
                  {pinLookupLoading ? "Looking up…" : "Look up PIN"}
                </button>
              </div>
              {pinLookupErr ? (
                <p style={{ color: "#b00020", fontSize: 13, margin: "8px 0 0" }}>{pinLookupErr}</p>
              ) : null}
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={label}>State</label>
              <select name="state" value={form.state || ""} onChange={onChange} style={input}>
                <option value="">Select state</option>
                {form.state && !INDIAN_STATES_AND_UTS.includes(form.state) ? (
                  <option value={form.state}>{form.state} (from lookup)</option>
                ) : null}
                {INDIAN_STATES_AND_UTS.map((st) => (
                  <option key={st} value={st}>
                    {st}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={label}>District / City</label>
              <input
                name="city"
                value={form.city || ""}
                onChange={onChange}
                style={input}
                placeholder="District or city"
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={label}>Street / building</label>
              <input
                name="clinic_address_street"
                value={form.clinic_address_street || ""}
                onChange={onChange}
                style={input}
                placeholder="Door no., street, locality"
              />
            </div>
          </div>

          <div style={card}>
            <h3 style={{ ...title, fontSize: 17 }}>Professional details</h3>
            {DOCTOR_PROFILE_TEXT_FIELDS.map(([name, lab]) => (
              <div key={name} style={{ marginBottom: 12 }}>
                <label style={label}>{lab}</label>
                <input name={name} value={form[name] || ""} onChange={onChange} style={input} />
              </div>
            ))}
          <div style={{ marginBottom: 12 }}>
            <label style={label}>Consultation modes</label>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              {[
                ["VIDEO", "Video call"],
                ["AUDIO", "Audio call"],
                ["CHAT", "Chat"],
                ["PHYSICAL", "Physical visit"],
              ].map(([value, text]) => (
                <label key={value} style={{ display: "flex", gap: 6, alignItems: "center", color: "#244a75" }}>
                  <input
                    type="checkbox"
                    checked={(form.consultation_modes || []).includes(value)}
                    onChange={() => toggleMode(value)}
                  />
                  {text}
                </label>
              ))}
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={label}>Documents on file</label>
            <p style={{ ...muted, marginTop: 0, marginBottom: 10, fontSize: 13 }}>
              Files shown here are what is stored on your profile today. Replacements are sent with your change request and
              replace these only after an admin approves.
            </p>
            <CurrentDoctorDocumentCard title="Profile photo" url={profile?.photo} showImagePreview />
            <CurrentDoctorDocumentCard title="Identity proof" url={profile?.identity_proof} showImagePreview />
            <CurrentDoctorDocumentCard title="Registration certificate" url={profile?.registration_certificate} showImagePreview />
          </div>
          {profile?.has_pending_changes ? (
            <p style={{ ...muted, margin: "0 0 12px", fontSize: 13 }}>
              New uploads are disabled while a change request is pending admin review.
            </p>
          ) : null}
          <div style={{ marginBottom: 12 }}>
            <label style={label}>Replace profile photo</label>
            <input
              type="file"
              accept="image/*"
              disabled={!!profile?.has_pending_changes}
              onChange={(e) => setPhotoFile(e.target.files?.[0] || null)}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={label}>Replace identity proof</label>
            <input
              type="file"
              accept=".pdf,image/*"
              disabled={!!profile?.has_pending_changes}
              onChange={(e) => setIdentityFile(e.target.files?.[0] || null)}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={label}>Replace registration certificate</label>
            <input
              type="file"
              accept=".pdf,image/*"
              disabled={!!profile?.has_pending_changes}
              onChange={(e) => setCertFile(e.target.files?.[0] || null)}
            />
          </div>
          <button
            type="submit"
            style={{ ...btnPrimary, opacity: saving || profile?.has_pending_changes ? 0.68 : 1 }}
            disabled={saving || !!profile?.has_pending_changes}
          >
            {saving
              ? "Saving..."
              : profile?.has_pending_changes
                ? "Pending admin approval"
                : profile?.profile_completed
                  ? "Submit change request"
                  : "Submit profile for verification"}
          </button>
        </div>
        </div>
      </form>
    </div>
  );
}

export function DoctorAvailabilityPanel() {
  const [data, setData] = useState(null);
  const [form, setForm] = useState({});
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const load = async () => {
    try {
      const d = await getDoctorAvailability();
      setData(d);
      setForm({
        is_available_online: !!d.is_available_online,
        is_available_in_clinic: !!d.is_available_in_clinic,
        next_available_online: d.next_available_online ? d.next_available_online.slice(0, 16) : "",
        next_available_in_clinic: d.next_available_in_clinic ? d.next_available_in_clinic.slice(0, 16) : "",
      });
    } catch (e) {
      setErr(e.message || "Failed to load availability");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const save = async () => {
    setErr("");
    setMsg("");
    try {
      const payload = {
        is_available_online: form.is_available_online,
        is_available_in_clinic: form.is_available_in_clinic,
        next_available_online: form.next_available_online || null,
        next_available_in_clinic: form.next_available_in_clinic || null,
      };
      await updateDoctorAvailability(payload);
      setMsg("Availability saved.");
      await load();
    } catch (e) {
      setErr(e.message || "Save failed");
    }
  };

  if (!data && !err) return <p style={muted}>Loading availability…</p>;

  return (
    <div>
      <h2 style={title}>Availability</h2>
      <p style={muted}>Control whether you appear as available for online and in-clinic consultations.</p>
      {err ? <p style={{ color: "#b00020" }}>{err}</p> : null}
      {msg ? <p style={{ color: "#1b5e20" }}>{msg}</p> : null}
      <div style={card}>
        <label style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12 }}>
          <input
            type="checkbox"
            checked={!!form.is_available_online}
            onChange={(e) => setForm({ ...form, is_available_online: e.target.checked })}
          />
          Available online now
        </label>
        <label style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12 }}>
          <input
            type="checkbox"
            checked={!!form.is_available_in_clinic}
            onChange={(e) => setForm({ ...form, is_available_in_clinic: e.target.checked })}
          />
          Available in clinic now
        </label>
        <div style={{ marginBottom: 12 }}>
          <label style={label}>Next available online (if not available now)</label>
          <input
            type="datetime-local"
            value={form.next_available_online || ""}
            onChange={(e) => setForm({ ...form, next_available_online: e.target.value })}
            style={input}
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={label}>Next available in clinic</label>
          <input
            type="datetime-local"
            value={form.next_available_in_clinic || ""}
            onChange={(e) => setForm({ ...form, next_available_in_clinic: e.target.value })}
            style={input}
          />
        </div>
        <button type="button" style={btnPrimary} onClick={save}>
          Save availability
        </button>
      </div>
    </div>
  );
}

export function DoctorSchedulePanel() {
  const [rows, setRows] = useState([]);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    day_of_week: "Monday",
    start_time: "09:00",
    end_time: "17:00",
    is_online: true,
    consultation_duration_minutes: 15,
    is_active: true,
  });

  const load = async () => {
    try {
      const d = await getDoctorSchedules();
      setRows(Array.isArray(d) ? d : d.results || []);
    } catch (e) {
      setErr(extractApiError(e, "Failed to load schedule"));
    }
  };

  useEffect(() => {
    load();
  }, []);

  const add = async () => {
    setErr("");
    setMsg("");
    setSaving(true);
    try {
      await createDoctorSchedule({
        day_of_week: form.day_of_week,
        start_time: form.start_time.length === 5 ? `${form.start_time}:00` : form.start_time,
        end_time: form.end_time.length === 5 ? `${form.end_time}:00` : form.end_time,
        is_online: form.is_online,
        consultation_duration_minutes: Number(form.consultation_duration_minutes),
        is_active: form.is_active,
      });
      setMsg("Slot added.");
      await load();
    } catch (e) {
      setErr(extractApiError(e, "Could not add slot"));
    } finally {
      setSaving(false);
    }
  };

  const setActive = async (slot, isActive) => {
    setErr("");
    setMsg("");
    try {
      await updateDoctorSchedule(slot.id, { is_active: isActive });
      setMsg(isActive ? "Slot activated." : "Slot paused.");
      await load();
    } catch (e) {
      setErr(extractApiError(e, "Could not update slot"));
    }
  };

  const remove = async (slot) => {
    const ok = window.confirm(`Delete ${slot.day_of_week} ${slot.start_time} - ${slot.end_time}?`);
    if (!ok) return;
    setErr("");
    setMsg("");
    try {
      await deleteDoctorSchedule(slot.id);
      setMsg("Slot deleted.");
      await load();
    } catch (e) {
      setErr(extractApiError(e, "Could not delete slot"));
    }
  };

  const grouped = DAYS.reduce((acc, day) => {
    acc[day] = rows
      .filter((row) => row.day_of_week === day)
      .sort((a, b) => `${a.start_time}`.localeCompare(`${b.start_time}`));
    return acc;
  }, {});

  const trimTime = (value) => (value ? String(value).slice(0, 5) : "--:--");

  return (
    <div>
      <h2 style={title}>Weekly schedule</h2>
      <p style={muted}>Recurring consultation windows. Bookings are allowed only inside active slots and follow each slot duration.</p>
      {err ? <p style={{ color: "#b00020" }}>{err}</p> : null}
      {msg ? <p style={{ color: "#1b5e20" }}>{msg}</p> : null}
      <div style={card}>
        <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", alignItems: "end" }}>
          <div>
            <label style={label}>Day</label>
            <select
              value={form.day_of_week}
              onChange={(e) => setForm({ ...form, day_of_week: e.target.value })}
              style={input}
            >
              {DAYS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={label}>Start</label>
            <input type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} style={input} />
          </div>
          <div>
            <label style={label}>End</label>
            <input type="time" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} style={input} />
          </div>
          <div>
            <label style={label}>Mode</label>
            <select
              value={form.is_online ? "online" : "clinic"}
              onChange={(e) => setForm({ ...form, is_online: e.target.value === "online" })}
              style={input}
            >
              <option value="online">Online</option>
              <option value="clinic">In clinic</option>
            </select>
          </div>
          <div>
            <label style={label}>Slot length</label>
            <select
              value={form.consultation_duration_minutes}
              onChange={(e) => setForm({ ...form, consultation_duration_minutes: e.target.value })}
              style={input}
            >
              {[10, 15, 20, 30, 45, 60].map((minutes) => (
                <option key={minutes} value={minutes}>
                  {minutes} min
                </option>
              ))}
            </select>
          </div>
          <label style={{ display: "flex", gap: 10, alignItems: "center", minHeight: 40, color: "#244a75", fontWeight: 700 }}>
            <input
              type="checkbox"
              checked={!!form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
            />
            Active
          </label>
        </div>
        <button type="button" style={btnPrimary} onClick={add} disabled={saving}>
          {saving ? "Adding..." : "Add slot"}
        </button>
      </div>
      <div style={card}>
        <h3 style={{ ...title, fontSize: 16 }}>Calendar</h3>
        {rows.length === 0 ? (
          <p style={muted}>No slots yet.</p>
        ) : (
          <>
          <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))" }}>
            {DAYS.map((day) => (
              <section
                key={day}
                style={{
                  border: "1px solid #d7e5f5",
                  borderRadius: 8,
                  padding: 12,
                  background: "#f8fbff",
                  minHeight: 130,
                }}
              >
                <h4 style={{ margin: "0 0 10px", color: "#123a6f" }}>{day}</h4>
                {grouped[day].length === 0 ? (
                  <p style={{ ...muted, margin: 0 }}>No slots</p>
                ) : (
                  grouped[day].map((slot) => (
                    <div
                      key={slot.id}
                      style={{
                        border: "1px solid #c6d7eb",
                        borderRadius: 8,
                        padding: 10,
                        marginBottom: 10,
                        background: slot.is_active ? "#fff" : "#eef2f6",
                        opacity: slot.is_active ? 1 : 0.76,
                      }}
                    >
                      <div style={{ fontWeight: 800, color: "#123a6f", marginBottom: 4 }}>
                        {trimTime(slot.start_time)} - {trimTime(slot.end_time)}
                      </div>
                      <div style={{ ...muted, fontSize: 13, marginBottom: 8 }}>
                        {slot.is_online ? "Online" : "Clinic"} - {slot.consultation_duration_minutes || 15} min -{" "}
                        {slot.is_active ? "Active" : "Paused"}
                      </div>
                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                        <button type="button" style={smallButton} onClick={() => setActive(slot, !slot.is_active)}>
                          {slot.is_active ? "Pause" : "Activate"}
                        </button>
                        <button
                          type="button"
                          style={{ ...smallButton, borderColor: "#f0b8b8", color: "#a11f1f" }}
                          onClick={() => remove(slot)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </section>
            ))}
          </div>
          <ul style={{ display: "none", margin: 0, paddingLeft: 18 }}>
            {rows.map((r) => (
              <li key={r.id} style={{ marginBottom: 6 }}>
                {r.day_of_week}: {r.start_time} – {r.end_time} ({r.is_online ? "Online" : "Clinic"})
              </li>
            ))}
          </ul>
          </>
        )}
      </div>
    </div>
  );
}
