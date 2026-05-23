import React from "react";
import { Link } from "react-router-dom";
import PublicLayout from "../../components/site/PublicLayout";
import Breadcrumbs from "../../components/marketing/Breadcrumbs";
import { m } from "../../constants/marketingLayout";

const main = {
  flex: 1,
  maxWidth: "1120px",
  margin: "0 auto",
  padding: "24px 20px 48px",
  width: "100%",
  boxSizing: "border-box",
};

const JoinIRMEPage = () => (
  <PublicLayout>
    <main style={main}>
      <Breadcrumbs
        items={[
          { label: "Home", to: "/" },
          { label: "Join IRME", current: true },
        ]}
      />

      <section style={m.hero}>
        <h1 style={m.heroH1}>Join IRME Telemedicine</h1>
        <p style={m.heroLead}>
          IRME Telemedicine connects patients, doctors, and local telemedicine centers for
          professional online consultations and assisted care. Choose the path that fits you—
          clinical practice, operating a center, or building skills through our support program.
        </p>
      </section>

      <div style={{ ...m.section, ...m.sectionBody }}>
        <p style={{ marginTop: 0, marginBottom: 0 }}>
          Whether you are a registered doctor, a clinic operator, or someone who wants to learn
          telemedicine support work, IRME offers clear entry points. Eligibility and approval are{" "}
          <strong>subject to verification</strong> and <strong>platform policy</strong>.
        </p>
      </div>

      <div style={m.cardGrid}>
        <article className="site-card-soft" style={m.card}>
          <h2 style={m.cardTitle}>Join as Consultant Doctor</h2>
          <p style={m.cardText}>
            Consult patients online and become part of the IRME Telemedicine doctor network.
            Services must stay within your qualification, registration, and applicable guidelines.
          </p>
          <Link
            to="/join/doctor"
            className="site-cta-green"
            style={{ ...m.btnPrimary, marginTop: "16px", display: "inline-block" }}
          >
            Join as Doctor
          </Link>
        </article>

        <article className="site-card-soft" style={m.card}>
          <h2 style={m.cardTitle}>Join as Telemedicine Center / TMC</h2>
          <p style={m.cardText}>
            Start a local assisted telemedicine center and help patients access online doctors
            with guidance and coordination at your location.
          </p>
          <Link
            to="/tmc"
            className="site-cta-green"
            style={{ ...m.btnPrimary, marginTop: "16px", display: "inline-block" }}
          >
            Start TMC
          </Link>
        </article>

        <article className="site-card-soft" style={m.card}>
          <h2 style={m.cardTitle}>Telemedicine Support Program</h2>
          <p style={m.cardText}>
            Learn telemedicine support and digital health operations to assist consultations and
            TMC operations. Duration and fees are confirmed during counselling.
          </p>
          <Link
            to="/telemedicine-course"
            style={{
              marginTop: "16px",
              display: "inline-block",
              textDecoration: "none",
              border: "2px solid #062B4F",
              color: "#062B4F",
              fontWeight: 700,
              padding: "10px 18px",
              borderRadius: "10px",
            }}
          >
            View Course
          </Link>
        </article>
      </div>

      <section style={{ ...m.section, textAlign: "center" }}>
        <h2 style={m.sectionTitle}>Already registered?</h2>
        <p style={m.lead}>
          Use the <strong>Login</strong> menu to access your patient, doctor, or TMC account.
        </p>
        <Link to="/login" className="site-cta-green" style={m.btnPrimary}>
          Go to Login
        </Link>
      </section>
    </main>
  </PublicLayout>
);

export default JoinIRMEPage;
