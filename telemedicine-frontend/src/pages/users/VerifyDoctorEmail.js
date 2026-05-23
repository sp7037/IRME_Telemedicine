import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import PublicLayout from "../../components/site/PublicLayout";
import { resendRegistrationEmailOTP, verifyRegistrationEmail } from "../../api/users";
import { registrationLayout as L } from "../../constants/registrationLayout";

const VerifyDoctorEmail = () => {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [email, setEmail] = useState(params.get("email") || "");
  const [otp, setOtp] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await verifyRegistrationEmail({ email: email.trim(), otp: otp.trim() });
      setMessage("Email verified. Redirecting to sign in.");
      setTimeout(() => navigate("/login"), 900);
    } catch (err) {
      setError(err.response?.data?.error || err.message || "Verification failed.");
    } finally {
      setBusy(false);
    }
  };

  const resend = async () => {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await resendRegistrationEmailOTP(email.trim());
      setMessage("OTP resent. Check your email inbox.");
    } catch (err) {
      setError(err.response?.data?.error || err.message || "Could not resend OTP.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <PublicLayout>
      <main style={L.main}>
        <section style={L.heroStrip}>
          <h1 style={L.heroTitle}>Verify your email</h1>
          <p style={L.heroSubtitle}>
            Enter the 6-digit OTP we sent to your inbox. You must verify before signing in.
          </p>
        </section>
        <div style={L.card}>
          {message ? <div style={L.bannerSuccess}>{message}</div> : null}
          {error ? <div style={L.bannerError}>{error}</div> : null}
          <form onSubmit={submit} style={L.form}>
            <div style={L.field}>
              <label style={L.label} htmlFor="verify-email">Email</label>
              <input
                id="verify-email"
                className="auth-input"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div style={L.field}>
              <label style={L.label} htmlFor="verify-otp">OTP</label>
              <input
                id="verify-otp"
                className="auth-input"
                inputMode="numeric"
                required
                minLength={6}
                maxLength={6}
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="6-digit OTP"
              />
            </div>
            <button type="submit" disabled={busy} style={L.submitButton}>
              {busy ? "Verifying..." : "Verify email"}
            </button>
          </form>
          <div style={L.footerNote}>
            <button type="button" disabled={busy || !email} onClick={resend} style={{ ...L.inlineLink, background: "transparent", border: 0, cursor: "pointer" }}>
              Resend OTP
            </button>
            <br />
            <Link to="/login" style={L.inlineLink}>Back to sign in</Link>
          </div>
        </div>
      </main>
    </PublicLayout>
  );
};

export default VerifyDoctorEmail;
