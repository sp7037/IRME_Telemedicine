import React from "react";
import { Link } from "react-router-dom";

const HomeHeader = () => {
  return (
    <header style={styles.header}>
      <h1 style={styles.logo}>🏥 Telemedicine</h1>
      <nav>
        <Link to="/login" style={styles.navLink}>Login</Link>
        <Link to="/register/patient" style={styles.navLink}>Register</Link>
        <Link to="/" style={styles.navLink}>Home</Link>
      </nav>
    </header>
  );
};

const styles = {
  header: {
    background: "#007bff",
    color: "white",
    padding: "15px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.1)",
  },
  logo: {
    margin: "0",
    fontSize: "24px",
  },
  navLink: {
    color: "white",
    textDecoration: "none",
    marginLeft: "15px",
    fontSize: "16px",
    fontWeight: "bold",
  },
};

export default HomeHeader;
