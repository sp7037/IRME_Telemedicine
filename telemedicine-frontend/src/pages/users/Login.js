import React, { useState } from "react";
import { loginUser } from "../../api/users";
import { useNavigate } from "react-router-dom";
import HomeHeader from "../../components/HomeHeader";
import HomeFooter from "../../components/HomeFooter";


const Login = () => {
  const [credentials, setCredentials] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setCredentials({ ...credentials, [e.target.name]: e.target.value });
  };

  const handleLogin = async (e) => {
    e.preventDefault(); // ✅ Prevent default GET request
  
    setLoading(true);
    setError("");
  
    try {
      const data = await loginUser(credentials.email, credentials.password);
  
      if (data.tokens.access) {
        localStorage.setItem("token", data.tokens.access); // ✅ Save access token
        localStorage.setItem("refresh_token", data.tokens.refresh); // ✅ Save refresh token
        localStorage.setItem("userType", data.user_type || "unknown"); // ✅ Save user role
  
        alert("✅ Login successful!");
  
        // Redirect based on user role
        switch (data.user_type) {
          case "patient":
            navigate("/dashboard/patient");
            break;
          case "doctor":
            navigate("/dashboard/doctor");
            break;
          case "tmc":
            navigate("/dashboard/tmc");
            break;
          default:
            navigate("/dashboard");
        }
      } else {
        setError("❌ Login failed. Please try again.");
      }
    } catch (error) {
      console.error("Login Error:", error.message);
  
      // Show specific error messages
      if (error.message.includes("Invalid email or password")) {
        setError("❌ Incorrect email or password.");
      } else {
        setError("❌ Login failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <>
      <HomeHeader />
      <div style={styles.container}>
        <div style={styles.loginBox}>
          <h2>🔑 Login</h2>

          {/* ✅ Show Error Message */}
          {error && <p style={styles.error}>{error}</p>}

          <form onSubmit={handleLogin} style={styles.form}>
            <input type="email" name="email" placeholder="Email" onChange={handleChange} required style={styles.input} />
            <input type="password" name="password" placeholder="Password" onChange={handleChange} required style={styles.input} />
            
            <button type="submit" disabled={loading} style={styles.button}>
              {loading ? "Logging in..." : "Login"}
            </button>
          </form>

          {/* Links for better navigation */}
          <div style={styles.links}>
            <a href="/forgot-password" style={styles.link}>Forgot Password?</a>
            <span> | </span>
            <a href="/register/patient" style={styles.link}>Register as Patient</a>
          </div>
        </div>
      </div>
      <HomeFooter />
    </>
  );
};

// ✅ Modern Styling
const styles = {
  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    backgroundColor: "#f5f8fc",
    paddingBottom: "50px",
  },
  loginBox: {
    backgroundColor: "#fff",
    border: "1px solid #d7e5f5",
    padding: "30px",
    borderRadius: "14px",
    boxShadow: "0 8px 20px rgba(0,0,0,0.08)",
    textAlign: "center",
    width: "350px",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  input: {
    padding: "12px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    fontSize: "16px",
  },
  button: {
    padding: "12px",
    backgroundColor: "#1762bf",
    color: "#fff",
    fontSize: "16px",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
  },
  buttonDisabled: {
    backgroundColor: "#cccccc",
    cursor: "not-allowed",
  },
  error: {
    color: "red",
    fontSize: "14px",
    marginBottom: "10px",
  },
  links: {
    marginTop: "10px",
    fontSize: "14px",
  },
  link: {
    color: "#007bff",
    textDecoration: "none",
  },
};

export default Login;
