import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import HomeHeader from "../../components/HomeHeader";
import HomeFooter from "../../components/HomeFooter";
import { registerUser } from "../../api/users";

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
      setErrors({ ...errors, confirmPassword: "Passwords do not match!" });
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
      await registerUser(payload);
      setSuccess("✅ Doctor registered successfully! Redirecting to login...");
      setErrors({});
      setTimeout(() => navigate("/login"), 2000);
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
    <>
      <HomeHeader />
      <div style={styles.container}>
        <h2>👨‍⚕️ Register as Doctor</h2>
        {success && <p style={styles.success}>{success}</p>}
        {errors.general && <p style={styles.error}>{errors.general}</p>}

        <div style={styles.formContainer}>
          <form onSubmit={handleSubmit} style={styles.form}>
            <div style={styles.row}>
              <input name="first_name" placeholder="First Name" value={formData.first_name} onChange={handleChange} required style={styles.input} />
              <input name="last_name" placeholder="Last Name" value={formData.last_name} onChange={handleChange} required style={styles.input} />
            </div>
            <input type="email" name="email" placeholder="Email" value={formData.email} onChange={handleChange} required style={styles.input} />
            {errors.email && <p style={styles.error}>{errors.email}</p>}
            <input name="phone_number" placeholder="Phone Number" value={formData.phone_number} onChange={handleChange} required style={styles.input} />
            {errors.phone_number && <p style={styles.error}>{errors.phone_number}</p>}

            <div style={styles.row}>
              <input type="password" name="password" placeholder="Password" value={formData.password} onChange={handleChange} required style={styles.input} />
              <input type="password" name="confirmPassword" placeholder="Confirm Password" value={formData.confirmPassword} onChange={handleChange} required style={styles.input} />
            </div>
            {errors.confirmPassword && <p style={styles.error}>{errors.confirmPassword}</p>}

            <button type="submit" style={styles.button}>Register Doctor</button>
          </form>
        </div>
      </div>
      <HomeFooter />
    </>
  );
};

const styles = {
  container: {
    maxWidth: "700px",
    margin: "50px auto",
    textAlign: "center",
  },
  formContainer: {
    backgroundColor: "#fff",
    padding: "25px",
    borderRadius: "8px",
    boxShadow: "0 5px 10px rgba(0,0,0,0.15)",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  row: {
    display: "flex",
    gap: "12px",
  },
  input: {
    width: "100%",
    padding: "12px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    fontSize: "15px",
  },
  button: {
    padding: "12px",
    backgroundColor: "#198754",
    color: "#fff",
    border: "none",
    borderRadius: "6px",
    fontSize: "16px",
    cursor: "pointer",
    marginTop: "10px",
  },
  error: {
    color: "red",
    fontSize: "14px",
  },
  success: {
    color: "green",
    fontSize: "14px",
  },
};

export default RegisterDoctor;
