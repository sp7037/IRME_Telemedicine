import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import PublicLayout from "../../components/site/PublicLayout";
import { registerUser } from "../../api/users";
import { registrationLayout as L } from "../../constants/registrationLayout";

const RegisterPatient = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone_number: "",
    password: "",
    confirmPassword: "",
    gender: "",
    age: "",
    address: "",
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

    const userData = {
      first_name: formData.first_name.trim(),
      last_name: formData.last_name.trim(),
      email: formData.email.trim(),
      phone_number: formData.phone_number.trim(),
      password: formData.password,
      role: "patient",
      gender: formData.gender,
      age: formData.age ? parseInt(formData.age, 10) : null,
      address: formData.address.trim(),
    };

    try {
      const data = await registerUser(userData);
      setSuccess("Account created. Check your email for the verification OTP.");
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
          <h1 style={L.heroTitle}>Register as Patient</h1>
          <p style={L.heroSubtitle}>
            Create your account for direct online consultations. Your details
            are used only to coordinate care and verify your profile.
          </p>
        </section>

        <div style={L.card}>
          {success && <div style={L.bannerSuccess}>{success}</div>}
          {errors.general && <div style={L.bannerError}>{errors.general}</div>}

          <form onSubmit={handleSubmit} style={L.form}>
            <div style={L.row}>
              <div style={L.field}>
                <label style={L.label} htmlFor="patient-first_name">
                  First name
                </label>
                <input
                  id="patient-first_name"
                  className="auth-input"
                  type="text"
                  name="first_name"
                  autoComplete="given-name"
                  required
                  onChange={handleChange}
                  value={formData.first_name}
                  placeholder="e.g. Priya"
                />
                {errors.first_name && (
                  <p style={L.fieldError}>{errors.first_name}</p>
                )}
              </div>
              <div style={L.field}>
                <label style={L.label} htmlFor="patient-last_name">
                  Last name
                </label>
                <input
                  id="patient-last_name"
                  className="auth-input"
                  type="text"
                  name="last_name"
                  autoComplete="family-name"
                  required
                  onChange={handleChange}
                  value={formData.last_name}
                  placeholder="e.g. Sharma"
                />
              </div>
            </div>

            <div style={L.field}>
              <label style={L.label} htmlFor="patient-email">
                Email
              </label>
              <input
                id="patient-email"
                className="auth-input"
                type="email"
                name="email"
                autoComplete="email"
                required
                onChange={handleChange}
                value={formData.email}
                placeholder="name@example.com"
              />
              {errors.email && <p style={L.fieldError}>{errors.email}</p>}
            </div>

            <div style={L.field}>
              <label style={L.label} htmlFor="patient-phone">
                Phone number
              </label>
              <input
                id="patient-phone"
                className="auth-input"
                type="tel"
                name="phone_number"
                autoComplete="tel"
                required
                onChange={handleChange}
                value={formData.phone_number}
                placeholder="10-digit mobile"
              />
              {errors.phone_number && (
                <p style={L.fieldError}>{errors.phone_number}</p>
              )}
            </div>

            <div style={L.row}>
              <div style={L.field}>
                <label style={L.label} htmlFor="patient-password">
                  Password
                </label>
                <input
                  id="patient-password"
                  className="auth-input"
                  type="password"
                  name="password"
                  autoComplete="new-password"
                  required
                  onChange={handleChange}
                  value={formData.password}
                  placeholder="Create a strong password"
                />
              </div>
              <div style={L.field}>
                <label style={L.label} htmlFor="patient-confirm">
                  Confirm password
                </label>
                <input
                  id="patient-confirm"
                  className="auth-input"
                  type="password"
                  name="confirmPassword"
                  autoComplete="new-password"
                  required
                  onChange={handleChange}
                  value={formData.confirmPassword}
                  placeholder="Re-enter password"
                />
              </div>
            </div>
            {errors.confirmPassword && (
              <p style={L.fieldError}>{errors.confirmPassword}</p>
            )}

            <div style={L.row}>
              <div style={L.field}>
                <label style={L.label} htmlFor="patient-gender">
                  Gender
                </label>
                <select
                  id="patient-gender"
                  className="auth-select"
                  name="gender"
                  required
                  onChange={handleChange}
                  value={formData.gender}
                >
                  <option value="">Select gender</option>
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                  <option value="O">Other</option>
                </select>
              </div>
              <div style={L.field}>
                <label style={L.label} htmlFor="patient-age">
                  Age
                </label>
                <input
                  id="patient-age"
                  className="auth-input"
                  type="number"
                  name="age"
                  min="1"
                  max="120"
                  required
                  onChange={handleChange}
                  value={formData.age}
                  placeholder="Years"
                />
                {errors.age && <p style={L.fieldError}>{errors.age}</p>}
              </div>
            </div>

            <div style={L.field}>
              <label style={L.label} htmlFor="patient-address">
                Address
              </label>
              <input
                id="patient-address"
                className="auth-input"
                type="text"
                name="address"
                autoComplete="street-address"
                required
                onChange={handleChange}
                value={formData.address}
                placeholder="Village / town, district, state"
              />
              {errors.address && <p style={L.fieldError}>{errors.address}</p>}
            </div>

            <button type="submit" style={L.submitButton}>
              Create patient account
            </button>
          </form>

          <div style={L.footerNote}>
            Are you a care provider?{" "}
            <Link to="/register/doctor" style={L.inlineLink}>
              Register as doctor
            </Link>
            {" · "}
            <Link to="/register/tmc" style={L.inlineLink}>
              Register center
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

export default RegisterPatient;
