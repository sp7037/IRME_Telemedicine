import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { loginUser } from "../../api/users";
import PublicLayout from "../../components/site/PublicLayout";
import { registrationLayout as L } from "../../constants/registrationLayout";
import { clearAuthSession, setAuthItem } from "../../utils/authSession";

function getSafeInternalNext(raw) {
  if (!raw || typeof raw !== "string") return null;
  if (!raw.startsWith("/") || raw.startsWith("//") || raw.includes("://")) return null;
  return raw;
}

function nextMatchesRole(next, role) {
  if (!next || !role) return false;
  if (role === "doctor") {
    return next.startsWith("/doctor") || next.startsWith("/dashboard/doctor");
  }
  if (role === "patient") {
    return next.startsWith("/patient") || next.startsWith("/dashboard/patient");
  }
  if (role === "tmc") return next.startsWith("/dashboard/tmc");
  if (role === "admin") {
    return next.startsWith("/dashboard/admin") || next.startsWith("/admin/");
  }
  return false;
}

const Login = () => {
  const [credentials, setCredentials] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const handleChange = (e) => {
    setCredentials({ ...credentials, [e.target.name]: e.target.value });
  };

  const handleLogin = async (e) => {
    e.preventDefault();

    setLoading(true);
    setError("");

    try {
      clearAuthSession();
      const data = await loginUser(credentials.email, credentials.password);

      if (data.tokens.access) {
        const access = String(data.tokens.access).trim();
        const refresh = String(data.tokens.refresh || "").trim();
        setAuthItem("token", access);
        setAuthItem("refresh_token", refresh);
        setAuthItem("userType", data.user_type || "unknown");
        if (data.doctor_onboarding) {
          setAuthItem("doctorOnboarding", JSON.stringify(data.doctor_onboarding));
        } else {
          setAuthItem("doctorOnboarding", null);
        }

        const safeNext = getSafeInternalNext(searchParams.get("next"));
        if (safeNext && nextMatchesRole(safeNext, data.user_type)) {
          navigate(safeNext);
          return;
        }

        switch (data.user_type) {
          case "patient":
            navigate("/dashboard/patient");
            break;
          case "doctor":
            navigate(data.doctor_onboarding?.next_step === "COMPLETE_PROFILE" ? "/doctor/profile" : "/dashboard/doctor");
            break;
          case "tmc":
            navigate("/dashboard/tmc");
            break;
          case "admin":
            navigate("/dashboard/admin");
            break;
          default:
            navigate("/dashboard");
        }
      } else {
        setError("Login failed. Please try again.");
      }
    } catch (err) {
      if (err.nextStep === "VERIFY_EMAIL") {
        navigate(`/verify-email?email=${encodeURIComponent(err.email || credentials.email)}`);
      } else if (err.message && err.message.includes("Invalid email or password")) {
        setError("Incorrect email or password.");
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const buttonStyle = {
    ...L.submitButton,
    opacity: loading ? 0.75 : 1,
    cursor: loading ? "wait" : "pointer",
  };

  return (
    <PublicLayout>
      <main style={L.main}>
        <section style={L.heroStrip}>
          <h1 style={L.heroTitle}>Sign in</h1>
          <p style={L.heroSubtitle}>
            Access your IRME account as a patient, doctor, or telemedicine
            center coordinator. Use the email and password you registered with.
          </p>
        </section>

        <div style={L.card}>
          {error && <div style={L.bannerError}>{error}</div>}

          <form onSubmit={handleLogin} style={L.form}>
            <div style={L.field}>
              <label style={L.label} htmlFor="login-email">
                Email
              </label>
              <input
                id="login-email"
                className="auth-input"
                type="email"
                name="email"
                autoComplete="username"
                value={credentials.email}
                onChange={handleChange}
                required
                placeholder="name@example.com"
              />
            </div>
            <div style={L.field}>
              <label style={L.label} htmlFor="login-password">
                Password
              </label>
              <input
                id="login-password"
                className="auth-input"
                type="password"
                name="password"
                autoComplete="current-password"
                value={credentials.password}
                onChange={handleChange}
                required
                placeholder="Your password"
              />
            </div>

            <button type="submit" disabled={loading} style={buttonStyle}>
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div style={L.footerNote}>
            <Link to="/forgot-password" style={L.inlineLink}>
              Forgot password?
            </Link>
            <br />
            <span style={{ marginTop: "10px", display: "inline-block" }}>
              New to IRME?{" "}
              <Link to="/register/patient" style={L.inlineLink}>
                Register as patient
              </Link>
              {" · "}
              <Link to="/join/doctor" style={L.inlineLink}>
                Doctor info
              </Link>
              {" · "}
              <Link to="/tmc" style={L.inlineLink}>
                Center info
              </Link>
            </span>
            <br />
            <span style={{ marginTop: "10px", display: "inline-block" }}>
              <Link to="/" style={L.inlineLink}>
                Back to home
              </Link>
            </span>
          </div>
        </div>
      </main>
    </PublicLayout>
  );
};

export default Login;
