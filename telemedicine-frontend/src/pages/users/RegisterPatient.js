import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import HomeHeader from "../../components/HomeHeader";
import HomeFooter from "../../components/HomeFooter";
import { registerUser } from "../../api/users";

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

  // ✅ Handle Input Change
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: "" }); // Clear error when user types
  };

  // ✅ Form Submit Handler
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      setErrors({ ...errors, confirmPassword: "Passwords do not match!" });
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
      await registerUser(userData);
      setSuccess("✅ Registration successful! Redirecting to login...");
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
        <h2>🩺 Register as Patient</h2>
        {success && <p style={styles.success}>{success}</p>}
        {errors.general && <p style={styles.error}>{errors.general}</p>}

        {/* ✅ Form Container with Border & Shadow */}
        <div style={styles.formContainer}>
          <form onSubmit={handleSubmit} style={styles.form}>
            <div style={styles.row}>
              <input type="text" name="first_name" placeholder="First Name" required onChange={handleChange} value={formData.first_name} style={styles.input} />
              <input type="text" name="last_name" placeholder="Last Name" required onChange={handleChange} value={formData.last_name} style={styles.input} />
            </div>
            {errors.first_name && <p style={styles.error}>{errors.first_name}</p>}

            <input type="email" name="email" placeholder="Email" required onChange={handleChange} value={formData.email} style={styles.input} />
            {errors.email && <p style={styles.error}>{errors.email}</p>}

            <input type="text" name="phone_number" placeholder="Phone Number" required onChange={handleChange} value={formData.phone_number} style={styles.input} />
            {errors.phone_number && <p style={styles.error}>{errors.phone_number}</p>}

            <input type="password" name="password" placeholder="Password" required onChange={handleChange} value={formData.password} style={styles.input} />
            <input type="password" name="confirmPassword" placeholder="Confirm Password" required onChange={handleChange} value={formData.confirmPassword} style={styles.input} />
            {errors.confirmPassword && <p style={styles.error}>{errors.confirmPassword}</p>}

            <div style={styles.row}>
              <select name="gender" required onChange={handleChange} value={formData.gender} style={styles.select}>
                <option value="">Select Gender</option>
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="O">Other</option>
              </select>

              <input type="number" name="age" placeholder="Age" required onChange={handleChange} value={formData.age} style={styles.input} />
            </div>
            {errors.age && <p style={styles.error}>{errors.age}</p>}

            <input type="text" name="address" placeholder="Address" required onChange={handleChange} value={formData.address} style={styles.input} />
            {errors.address && <p style={styles.error}>{errors.address}</p>}

            <button type="submit" style={styles.button}>Register</button>
          </form>
        </div>
      </div>
      <HomeFooter />
    </>
  );
};

const styles = {
  container: {
    maxWidth: "600px",
    margin: "50px auto",
    textAlign: "center",
  },
  formContainer: {
    backgroundColor: "#fff",
    padding: "20px",
    borderRadius: "8px",
    boxShadow: "0px 5px 10px rgba(0, 0, 0, 0.2)",
    border: "1px solid #ccc",
  },
  row: {
    display: "flex",
    justifyContent: "space-between",
    gap: "10px",
  },
  input: {
    width: "100%",
    padding: "10px",
    borderRadius: "5px",
    border: "1px solid #ccc",
    fontSize: "16px",
  },
  select: {
    width: "48%",
    padding: "10px",
    borderRadius: "5px",
    border: "1px solid #ccc",
    fontSize: "16px",
  },
  button: {
    width: "100%",
    padding: "12px",
    backgroundColor: "#007bff",
    color: "#fff",
    fontSize: "16px",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    marginTop: "10px",
  },
  error: {
    color: "red",
    fontSize: "14px",
    marginTop: "5px",
  },
  success: {
    color: "green",
    fontSize: "14px",
    marginTop: "10px",
  },
};

export default RegisterPatient;
