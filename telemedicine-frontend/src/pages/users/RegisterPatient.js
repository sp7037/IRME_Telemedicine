import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import PublicLayout from "../../components/site/PublicLayout";
import LocationPicker from "../../components/forms/LocationPicker";
import { registerUser } from "../../api/users";
import { registrationLayout as L } from "../../constants/registrationLayout";

/**
 * Redesigned Patient Registration
 * 
 * Improvements:
 * - 2-step flow: Basic Info → Location & Health Details
 * - Mobile-first with large touch targets
 * - +91 mobile prefix with 10-digit validation
 * - Inline validation messages
 * - Location picker with geolocation + PIN code lookup
 * - Cleaner, more focused UI
 */

const RegisterPatientNew = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1: Basic Info, 2: Location & Health

  // Form state
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone_number: "",
    password: "",
    confirmPassword: "",
    gender: "",
    age: "",
    // Location fields
    address: "",
    pincode: "",
    district: "",
    state: "",
    lat: null,
    lng: null,
  });

  const [errors, setErrors] = useState({});
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
    
    // Clear error for this field
    if (errors[name]) {
      setErrors({ ...errors, [name]: "" });
    }

    // Real-time validation for phone number
    if (name === "phone_number") {
      const cleaned = value.replace(/\D/g, "");
      if (cleaned.length > 10) {
        return; // Don't allow more than 10 digits
      }
      setFormData({ ...formData, [name]: cleaned });
    }
  };

  const handleLocationChange = (locationData) => {
    setFormData({
      ...formData,
      address: locationData.address || "",
      pincode: locationData.pincode || "",
      district: locationData.district || "",
      state: locationData.state || "",
      lat: locationData.lat || null,
      lng: locationData.lng || null,
    });
    
    // Clear location-related errors
    setErrors({
      ...errors,
      address: "",
      pincode: "",
      district: "",
      state: "",
    });
  };

  // Validate Step 1
  const validateStep1 = () => {
    const newErrors = {};

    if (!formData.first_name.trim()) {
      newErrors.first_name = "First name is required";
    }

    if (!formData.last_name.trim()) {
      newErrors.last_name = "Last name is required";
    }

    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email";
    }

    const phoneDigits = formData.phone_number.replace(/\D/g, "");
    if (!phoneDigits) {
      newErrors.phone_number = "Mobile number is required";
    } else if (phoneDigits.length !== 10) {
      newErrors.phone_number = "Please enter a valid 10-digit mobile number";
    } else if (!/^[6-9]\d{9}$/.test(phoneDigits)) {
      newErrors.phone_number = "Mobile number must start with 6, 7, 8, or 9";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Validate Step 2
  const validateStep2 = () => {
    const newErrors = {};

    if (!formData.gender) {
      newErrors.gender = "Please select your gender";
    }

    const ageNum = parseInt(formData.age, 10);
    if (!formData.age) {
      newErrors.age = "Age is required";
    } else if (isNaN(ageNum) || ageNum < 1 || ageNum > 120) {
      newErrors.age = "Please enter a valid age (1-120)";
    }

    if (!formData.pincode || formData.pincode.length !== 6) {
      newErrors.pincode = "Please enter a valid 6-digit PIN code";
    }

    if (!formData.address.trim()) {
      newErrors.address = "Address is required";
    }

    if (!formData.district.trim()) {
      newErrors.district = "District is required";
    }

    if (!formData.state.trim()) {
      newErrors.state = "State is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep1()) {
      setStep(2);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const handleBack = () => {
    setStep(1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateStep2()) {
      return;
    }

    setLoading(true);
    setSuccess("");
    setErrors({});

    // Prepare user data for API
    // Note: Backend accepts: first_name, last_name, email, phone_number, password, role, gender, age, address
    // We combine location fields into address field since backend doesn't have separate pincode/district/state fields
    const fullAddress = [
      formData.address,
      formData.district,
      formData.state,
      `PIN: ${formData.pincode}`,
    ]
      .filter(Boolean)
      .join(", ");

    const userData = {
      first_name: formData.first_name.trim(),
      last_name: formData.last_name.trim(),
      email: formData.email.trim(),
      phone_number: formData.phone_number.trim(),
      password: formData.password,
      role: "patient",
      gender: formData.gender,
      age: parseInt(formData.age, 10),
      address: fullAddress,
      // Note: lat/lng are captured but not sent to backend
      // Backend would need to add these fields to store coordinates
    };

    try {
      const data = await registerUser(userData);
      setSuccess("Account created successfully! Check your email for verification.");
      setErrors({});

      if (data?.next_step === "VERIFY_EMAIL" && data?.email) {
        setTimeout(
          () => navigate(`/verify-email?email=${encodeURIComponent(data.email)}`),
          1500
        );
      } else {
        setTimeout(() => navigate("/login"), 2000);
      }
    } catch (error) {
      setLoading(false);
      setSuccess("");
      
      if (error.fieldErrors) {
        setErrors(error.fieldErrors);
        
        // If there's an error in step 1 fields, go back to step 1
        const step1Fields = ["first_name", "last_name", "email", "phone_number", "password"];
        const hasStep1Error = step1Fields.some(field => error.fieldErrors[field]);
        
        if (hasStep1Error && step === 2) {
          setStep(1);
          window.scrollTo({ top: 0, behavior: "smooth" });
        }
      } else {
        setErrors({ general: error.message || "Registration failed. Please try again." });
      }
    }
  };

  return (
    <PublicLayout>
      <main style={L.main}>
        <section style={L.heroStrip}>
          <h1 style={L.heroTitle}>Register as Patient</h1>
          <p style={L.heroSubtitle}>
            Create your account for direct online consultations with verified doctors.
            {step === 2 && " Complete your location and health details to finish registration."}
          </p>
        </section>

        <div style={L.card}>
          {/* Step Indicator */}
          <div style={styles.stepIndicator}>
            <div style={step === 1 ? styles.stepActive : styles.stepCompleted}>
              <span style={styles.stepNumber}>{step > 1 ? "✓" : "1"}</span>
              <span style={styles.stepLabel}>Basic Info</span>
            </div>
            <div style={styles.stepDivider}></div>
            <div style={step === 2 ? styles.stepActive : styles.stepInactive}>
              <span style={styles.stepNumber}>2</span>
              <span style={styles.stepLabel}>Location & Health</span>
            </div>
          </div>

          {success && <div style={L.bannerSuccess}>{success}</div>}
          {errors.general && <div style={L.bannerError}>{errors.general}</div>}

          <form onSubmit={handleSubmit} style={L.form}>
            {/* Step 1: Basic Information */}
            {step === 1 && (
              <>
                <div style={L.row}>
                  <div style={L.field}>
                    <label style={L.label} htmlFor="patient-first_name">
                      First Name <span style={styles.required}>*</span>
                    </label>
                    <input
                      id="patient-first_name"
                      className="auth-input"
                      type="text"
                      name="first_name"
                      autoComplete="given-name"
                      autoFocus
                      value={formData.first_name}
                      onChange={handleChange}
                      placeholder="e.g. Priya"
                    />
                    {errors.first_name && (
                      <p style={L.fieldError}>{errors.first_name}</p>
                    )}
                  </div>

                  <div style={L.field}>
                    <label style={L.label} htmlFor="patient-last_name">
                      Last Name <span style={styles.required}>*</span>
                    </label>
                    <input
                      id="patient-last_name"
                      className="auth-input"
                      type="text"
                      name="last_name"
                      autoComplete="family-name"
                      value={formData.last_name}
                      onChange={handleChange}
                      placeholder="e.g. Sharma"
                    />
                    {errors.last_name && (
                      <p style={L.fieldError}>{errors.last_name}</p>
                    )}
                  </div>
                </div>

                <div style={L.field}>
                  <label style={L.label} htmlFor="patient-email">
                    Email <span style={styles.required}>*</span>
                  </label>
                  <input
                    id="patient-email"
                    className="auth-input"
                    type="email"
                    name="email"
                    autoComplete="email"
                    inputMode="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="your.email@example.com"
                  />
                  {errors.email && <p style={L.fieldError}>{errors.email}</p>}
                </div>

                <div style={L.field}>
                  <label style={L.label} htmlFor="patient-phone">
                    Mobile Number <span style={styles.required}>*</span>
                  </label>
                  <div style={styles.phoneInputContainer}>
                    <span style={styles.phonePrefix}>+91</span>
                    <input
                      id="patient-phone"
                      className="auth-input"
                      style={styles.phoneInput}
                      type="tel"
                      name="phone_number"
                      autoComplete="tel-national"
                      inputMode="numeric"
                      maxLength="10"
                      value={formData.phone_number}
                      onChange={handleChange}
                      placeholder="10-digit mobile"
                    />
                  </div>
                  {errors.phone_number && (
                    <p style={L.fieldError}>{errors.phone_number}</p>
                  )}
                  {formData.phone_number && formData.phone_number.length === 10 && !errors.phone_number && (
                    <p style={styles.validText}>✓ Valid mobile number</p>
                  )}
                </div>

                <div style={L.row}>
                  <div style={L.field}>
                    <label style={L.label} htmlFor="patient-password">
                      Password <span style={styles.required}>*</span>
                    </label>
                    <input
                      id="patient-password"
                      className="auth-input"
                      type="password"
                      name="password"
                      autoComplete="new-password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="At least 8 characters"
                    />
                    {errors.password && (
                      <p style={L.fieldError}>{errors.password}</p>
                    )}
                  </div>

                  <div style={L.field}>
                    <label style={L.label} htmlFor="patient-confirm">
                      Confirm Password <span style={styles.required}>*</span>
                    </label>
                    <input
                      id="patient-confirm"
                      className="auth-input"
                      type="password"
                      name="confirmPassword"
                      autoComplete="new-password"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      placeholder="Re-enter password"
                    />
                    {errors.confirmPassword && (
                      <p style={L.fieldError}>{errors.confirmPassword}</p>
                    )}
                    {formData.password && formData.confirmPassword && 
                     formData.password === formData.confirmPassword && 
                     !errors.confirmPassword && (
                      <p style={styles.validText}>✓ Passwords match</p>
                    )}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleNext}
                  style={L.submitButton}
                >
                  Next: Location & Health Details →
                </button>
              </>
            )}

            {/* Step 2: Location & Health Details */}
            {step === 2 && (
              <>
                <div style={L.row}>
                  <div style={L.field}>
                    <label style={L.label} htmlFor="patient-gender">
                      Gender <span style={styles.required}>*</span>
                    </label>
                    <select
                      id="patient-gender"
                      className="auth-select"
                      name="gender"
                      value={formData.gender}
                      onChange={handleChange}
                    >
                      <option value="">Select gender</option>
                      <option value="M">Male</option>
                      <option value="F">Female</option>
                      <option value="O">Other</option>
                    </select>
                    {errors.gender && <p style={L.fieldError}>{errors.gender}</p>}
                  </div>

                  <div style={L.field}>
                    <label style={L.label} htmlFor="patient-age">
                      Age <span style={styles.required}>*</span>
                    </label>
                    <input
                      id="patient-age"
                      className="auth-input"
                      type="number"
                      name="age"
                      inputMode="numeric"
                      min="1"
                      max="120"
                      value={formData.age}
                      onChange={handleChange}
                      placeholder="Years"
                    />
                    {errors.age && <p style={L.fieldError}>{errors.age}</p>}
                  </div>
                </div>

                <div style={styles.sectionDivider}>
                  <h3 style={styles.sectionTitle}>Location Details</h3>
                  <p style={styles.sectionHint}>
                    Use your current location or enter your PIN code for auto-fill
                  </p>
                </div>

                <LocationPicker
                  value={{
                    address: formData.address,
                    pincode: formData.pincode,
                    district: formData.district,
                    state: formData.state,
                    lat: formData.lat,
                    lng: formData.lng,
                  }}
                  onChange={handleLocationChange}
                  error={errors.address || errors.pincode || errors.district || errors.state}
                />

                <div style={styles.buttonRow}>
                  <button
                    type="button"
                    onClick={handleBack}
                    style={styles.backButton}
                  >
                    ← Back
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    style={{
                      ...L.submitButton,
                      flex: 1,
                      opacity: loading ? 0.7 : 1,
                      cursor: loading ? "wait" : "pointer",
                    }}
                  >
                    {loading ? "Creating account..." : "Create Patient Account"}
                  </button>
                </div>
              </>
            )}
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

const styles = {
  stepIndicator: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: "32px",
    padding: "20px",
    backgroundColor: "#f8fafb",
    borderRadius: "12px",
  },
  stepActive: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "8px",
  },
  stepCompleted: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "8px",
    opacity: 0.7,
  },
  stepInactive: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "8px",
    opacity: 0.4,
  },
  stepNumber: {
    width: "40px",
    height: "40px",
    borderRadius: "50%",
    backgroundColor: "#1762bf",
    color: "#ffffff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 700,
    fontSize: "16px",
  },
  stepLabel: {
    fontSize: "13px",
    fontWeight: 600,
    color: "#10243e",
    textAlign: "center",
  },
  stepDivider: {
    width: "60px",
    height: "2px",
    backgroundColor: "#cbd5e1",
    margin: "0 16px",
  },
  phoneInputContainer: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  phonePrefix: {
    padding: "0 16px",
    height: "44px",
    backgroundColor: "#e8f2ff",
    border: "1px solid #9ec9ff",
    borderRadius: "10px",
    display: "flex",
    alignItems: "center",
    fontWeight: 600,
    color: "#1762bf",
    fontSize: "16px",
  },
  phoneInput: {
    flex: 1,
  },
  required: {
    color: "#ef4444",
  },
  validText: {
    fontSize: "13px",
    color: "#17623c",
    margin: "4px 0 0 0",
    fontWeight: 500,
  },
  sectionDivider: {
    marginTop: "12px",
    marginBottom: "8px",
    paddingTop: "24px",
    borderTop: "2px solid #e7ecf1",
  },
  sectionTitle: {
    margin: "0 0 6px 0",
    fontSize: "1.125rem",
    fontWeight: 600,
    color: "#10243e",
  },
  sectionHint: {
    margin: 0,
    fontSize: "14px",
    color: "#64748b",
  },
  buttonRow: {
    display: "flex",
    gap: "12px",
    marginTop: "12px",
  },
  backButton: {
    padding: "16px 24px",
    backgroundColor: "#e8f2ff",
    color: "#1762bf",
    border: "1px solid #9ec9ff",
    borderRadius: "10px",
    fontSize: "16px",
    fontWeight: 600,
    cursor: "pointer",
    transition: "background 150ms ease",
  },
};

export default RegisterPatientNew;
