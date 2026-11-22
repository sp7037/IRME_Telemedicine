import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import PublicLayout from "../../components/site/PublicLayout";
import { registerUser } from "../../api/users";
import { registrationLayout as L } from "../../constants/registrationLayout";

const RegisterTMC = () => {
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
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
    setErrors({ ...errors, [name]: "" });
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
      role: "tmc",
    };

    try {
      const data = await registerUser(payload);
      setSuccess("Center account created. Check your email for the verification OTP.");
      setErrors({});
      if (data?.next_step === "VERIFY_EMAIL" && data?.email) {
        setTimeout(
          () => navigate(`/verify-email?email=${encodeURIComponent(data.email)}`),
          1200
        );
      } else {
        setTimeout(() => navigate("/login"), 2000);
      }
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
          <h1 style={L.heroTitle}>Register a Telemedicine Center</h1>
          <p style={L.heroSubtitle}>
            Onboard your center as a coordinator account. Use a trusted contact
            person&apos;s name and work email; center details can be completed
            after you sign in.
          </p>
        </section>

        <div style={L.card}>
          {success && <div style={L.bannerSuccess}>{success}</div>}
          {errors.general && <div style={L.bannerError}>{errors.general}</div>}

          <form onSubmit={handleSubmit} style={L.form}>
            <div style={L.row}>
              <div style={L.field}>
                <label style={L.label} htmlFor="tmc-first_name">
                  Coordinator first name
                </label>
                <input
                  id="tmc-first_name"
                  className="auth-input"
                  name="first_name"
                  autoComplete="given-name"
                  required
                  value={formData.first_name}
                  onChange={handleChange}
                  placeholder="e.g. Neha"
                />
              </div>
              <div style={L.field}>
                <label style={L.label} htmlFor="tmc-last_name">
                  Coordinator last name
                </label>
                <input
                  id="tmc-last_name"
                  className="auth-input"
                  name="last_name"
                  autoComplete="family-name"
                  required
                  value={formData.last_name}
                  onChange={handleChange}
                  placeholder="e.g. Kulkarni"
                />
              </div>
            </div>

            <div style={L.field}>
              <label style={L.label} htmlFor="tmc-email">
                Work email
              </label>
              <input
                id="tmc-email"
                className="auth-input"
                type="email"
                name="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleChange}
                placeholder="center@organization.org"
              />
              {errors.email && <p style={L.fieldError}>{errors.email}</p>}
            </div>

            <div style={L.field}>
              <label style={L.label} htmlFor="tmc-phone">
                Phone number
              </label>
              <input
                id="tmc-phone"
                className="auth-input"
                type="tel"
                name="phone_number"
                autoComplete="tel"
                required
                value={formData.phone_number}
                onChange={handleChange}
                placeholder="Desk or coordinator mobile"
              />
              {errors.phone_number && (
                <p style={L.fieldError}>{errors.phone_number}</p>
              )}
            </div>

            <div style={L.row}>
              <div style={L.field}>
                <label style={L.label} htmlFor="tmc-password">
                  Password
                </label>
                <input
                  id="tmc-password"
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
                <label style={L.label} htmlFor="tmc-confirm">
                  Confirm password
                </label>
                <input
                  id="tmc-confirm"
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
              Create center account
            </button>
          </form>

          <div style={L.footerNote}>
            Individual patient?{" "}
            <Link to="/register/patient" style={L.inlineLink}>
              Register as patient
            </Link>
            {" · "}
            <Link to="/register/doctor" style={L.inlineLink}>
              Doctor registration
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

export default RegisterTMC;
