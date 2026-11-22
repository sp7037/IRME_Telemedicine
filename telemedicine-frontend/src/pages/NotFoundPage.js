import React from "react";
import { Link } from "react-router-dom";
import PublicLayout from "../components/site/PublicLayout";
import { SITE_HEADER_NAVY, SITE_CTA_GREEN } from "../constants/brandTheme";

const NotFoundPage = () => (
  <PublicLayout>
    <main
      style={{
        flex: 1,
        maxWidth: "640px",
        margin: "0 auto",
        padding: "48px 20px",
        textAlign: "center",
      }}
    >
      <h1 style={{ color: SITE_HEADER_NAVY, fontSize: "2rem" }}>Page not found</h1>
      <p style={{ color: "#475569", lineHeight: 1.6 }}>
        The page you requested does not exist or has moved.
      </p>
      <Link
        to="/"
        className="site-cta-green"
        style={{
          display: "inline-block",
          marginTop: "20px",
          backgroundColor: SITE_CTA_GREEN,
          color: "#052e16",
          fontWeight: 800,
          padding: "12px 22px",
          borderRadius: "10px",
          textDecoration: "none",
        }}
      >
        Back to Home
      </Link>
    </main>
  </PublicLayout>
);

export default NotFoundPage;
