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

const whoItems = [
  "Registered medical practitioners",
  "Specialists and super-specialists where applicable",
  "General physicians",
  "AYUSH, paramedical, or other professionals only if permitted by applicable rules and platform policy",
];

const benefits = [
  "Online consultation opportunities (subject to availability and verification)",
  "Flexible consultation model within platform rules",
  "Digital doctor profile for verified accounts",
  "Patient reach through TMC network and direct users",
  "Consultation history and dashboard tools as enabled",
  "Professional healthcare network associated with IRME",
];

const JoinDoctorPage = () => (
  <PublicLayout>
    <main style={main}>
      <Breadcrumbs
        items={[
          { label: "Home", to: "/" },
          { label: "Join IRME", to: "/join-irme" },
          { label: "Consultant Doctor", current: true },
        ]}
      />

      <section style={m.hero}>
        <h1 style={m.heroH1}>Consult Patients Online with IRME Telemedicine</h1>
        <p style={m.heroLead}>
          Join our network of doctors and help patients access professional medical advice through
          online consultation—subject to qualification, registration, and IRME verification.
        </p>
        <div style={m.heroCtas}>
          <Link to="/register/doctor" className="site-cta-green" style={m.btnPrimary}>
            Register as Doctor
          </Link>
          <Link to="/login" className="site-cta-ghost" style={m.btnSecondary}>
            Doctor Login
          </Link>
        </div>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Who can join</h2>
        <p style={m.sectionBody}>
          <strong>Eligibility and approval</strong> depend on your qualification, professional
          registration, and IRME platform verification. We do not guarantee approval from this page
          alone.
        </p>
        <ul style={m.list}>
          {whoItems.map((x) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Benefits</h2>
        <div style={m.cardGrid}>
          {benefits.map((t) => (
            <article key={t} className="site-card-soft" style={m.card}>
              <p style={{ ...m.cardText, fontWeight: 600, color: "#0f172a" }}>{t}</p>
            </article>
          ))}
        </div>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Process</h2>
        <ol style={{ ...m.list, listStyle: "decimal" }}>
          <li>Submit doctor registration through the platform.</li>
          <li>Upload or submit qualification and registration details if requested.</li>
          <li>Profile verification by IRME.</li>
          <li>Account activation when requirements are satisfied.</li>
          <li>Start accepting consultations as enabled on your profile.</li>
        </ol>
      </section>

      <p style={m.note}>
        <strong>Compliance:</strong> Doctors must provide only services permitted under their
        qualification, registration, and applicable medical guidelines. IRME does not replace
        statutory licensing or professional responsibility.
      </p>

      <section style={{ ...m.section, ...m.hero, marginTop: "40px" }}>
        <h2 style={{ ...m.heroH1, fontSize: "1.45rem" }}>Next step</h2>
        <div style={m.heroCtas}>
          <Link to="/register/doctor" className="site-cta-green" style={m.btnPrimary}>
            Register as Doctor
          </Link>
          <Link to="/login" className="site-cta-ghost" style={m.btnSecondary}>
            Doctor Login
          </Link>
        </div>
      </section>
    </main>
  </PublicLayout>
);

export default JoinDoctorPage;
