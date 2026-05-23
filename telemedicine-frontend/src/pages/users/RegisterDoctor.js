import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import PublicLayout from "../../components/site/PublicLayout";
import { registerUser } from "../../api/users";
import { registrationLayout as L } from "../../constants/registrationLayout";

const RegisterDoctor = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone_number: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState({});
  const [success, setSuccess] = useState("");

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: "" });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      setErrors({ ...errors, confirmPassword: "Passwords do not match." });
      return;
    }

    const payload = {
      first_name: formData.first_name.trim(),
      last_name: formData.last_name.trim(),
      email: formData.email.trim(),
      phone_number: formData.phone_number.trim(),
      password: formData.password,
      role: "doctor",
    };

    try {
      const data = await registerUser(payload);
      setSuccess("Doctor account created. Check your email for the OTP.");
      setErrors({});
      setTimeout(
        () => navigate(`/verify-email?email=${encodeURIComponent(data.email || payload.email)}`),
        900
      );
    } catch (error) {
      setSuccess("");
      if (error.fieldErrors) {
        setErrors(error.fieldErrors);
      } else {
        setErrors({ general: error.message });
      }
    }
  };

  return (
    <PublicLayout>
      <main style={L.main}>
        <section style={L.heroStrip}>
          <h1 style={L.heroTitle}>Register as Doctor</h1>
          <p style={L.heroSubtitle}>
            Join the IRME network to offer teleconsultations. After sign-up you
            must verify your email before signing in and completing your professional profile.
          </p>
        </section>

        <div style={L.card}>
          {success && <div style={L.bannerSuccess}>{success}</div>}
          {errors.general && <div style={L.bannerError}>{errors.general}</div>}

          <form onSubmit={handleSubmit} style={L.form}>
            <div style={L.row}>
              <div style={L.field}>
                <label style={L.label} htmlFor="doc-first_name">
                  First name
                </label>
                <input
                  id="doc-first_name"
                  className="auth-input"
                  name="first_name"
                  autoComplete="given-name"
                  required
                  value={formData.first_name}
                  onChange={handleChange}
                  placeholder="Given name"
                />
              </div>
              <div style={L.field}>
                <label style={L.label} htmlFor="doc-last_name">
                  Last name
                </label>
                <input
                  id="doc-last_name"
                  className="auth-input"
                  name="last_name"
                  autoComplete="family-name"
                  required
                  value={formData.last_name}
                  onChange={handleChange}
                  placeholder="Surname"
                />
              </div>
            </div>

            <div style={L.field}>
              <label style={L.label} htmlFor="doc-email">
                Professional email
              </label>
              <input
                id="doc-email"
                className="auth-input"
                type="email"
                name="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleChange}
                placeholder="doctor@clinic or hospital domain"
              />
              {errors.email && <p style={L.fieldError}>{errors.email}</p>}
            </div>

            <div style={L.field}>
              <label style={L.label} htmlFor="doc-phone">
                Phone number
              </label>
              <input
                id="doc-phone"
                className="auth-input"
                type="tel"
                name="phone_number"
                autoComplete="tel"
                required
                value={formData.phone_number}
                onChange={handleChange}
                placeholder="Primary contact"
              />
              {errors.phone_number && (
                <p style={L.fieldError}>{errors.phone_number}</p>
              )}
            </div>

            <div style={L.row}>
              <div style={L.field}>
                <label style={L.label} htmlFor="doc-password">
                  Password
                </label>
                <input
                  id="doc-password"
                  className="auth-input"
                  type="password"
                  name="password"
                  autoComplete="new-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Create password"
                />
              </div>
              <div style={L.field}>
                <label style={L.label} htmlFor="doc-confirm">
                  Confirm password
                </label>
                <input
                  id="doc-confirm"
                  className="auth-input"
                  type="password"
                  name="confirmPassword"
                  autoComplete="new-password"
                  required
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Confirm password"
                />
              </div>
            </div>
            {errors.confirmPassword && (
              <p style={L.fieldError}>{errors.confirmPassword}</p>
            )}

            <button type="submit" style={L.submitButton}>
              Create doctor account
            </button>
          </form>

          <div style={L.footerNote}>
            Patient registration?{" "}
            <Link to="/register/patient" style={L.inlineLink}>
              Register as patient
            </Link>
            {" · "}
            <Link to="/register/tmc" style={L.inlineLink}>
              Center registration
            </Link>
            <br />
            <span style={{ marginTop: "10px", display: "inline-block" }}>
              Already registered?{" "}
              <Link to="/login" style={L.inlineLink}>
                Sign in
              </Link>
            </span>
          </div>
        </div>
      </main>
    </PublicLayout>
  );
};

export default RegisterDoctor;
