import React from "react";
import { Link } from "react-router-dom";
import PublicLayout from "../../components/site/PublicLayout";
import Seo from "../../components/Seo";
import Breadcrumbs from "../../components/marketing/Breadcrumbs";
import LeadCaptureForm from "../../components/marketing/LeadCaptureForm";
import { m } from "../../constants/marketingLayout";
import { seoCities, seoStates } from "../../data/seoLocations";
import { whatsappUrl } from "../../constants/marketingContact";

const main = {
  flex: 1,
  maxWidth: "1120px",
  margin: "0 auto",
  padding: "24px 20px 48px",
  width: "100%",
  boxSizing: "border-box",
};

const whoCards = [
  "Existing clinic or health worker",
  "Medical store owner",
  "NGO or community center",
  "CSC or computer center",
  "Rural entrepreneur",
  "Educational or paramedical institute",
];

const benefitCards = [
  "Serve patients in your locality",
  "Earn consultation-service income where applicable",
  "Digital healthcare identity through the platform",
  "Access to online doctors for patient consultations",
  "Training and operational guidance (as offered for your plan)",
  "Listing on the IRME Telemedicine platform when activated",
];

const getsList = [
  "TMC dashboard access after activation",
  "Patient consultation booking support (as enabled)",
  "Doctor consultation connection workflow",
  "Center profile and listing (subject to verification)",
  "Basic onboarding guidance",
  "Support for operating assisted telemedicine service",
  "Future access to wallet, payment, or reporting features if enabled on the platform",
];

const BecomeTMCPage = () => (
  <PublicLayout>
    <Seo
      title="Join as Telemedicine Center | Open TMC in Your City with IRME"
      description="Open a Telemedicine Center with IRME. Assisted online doctor consultation workflow, patient coordination, digital records and onboarding guidance for local operators across India."
      canonical="https://telemedicine.irme.in/tmc"
      keywords="open telemedicine center, telemedicine center franchise, TMC registration, online doctor consultation center, rural healthcare business"
    />
    <main style={main}>
      <Breadcrumbs
        items={[
          { label: "Home", to: "/" },
          { label: "Join IRME", to: "/join-irme" },
          { label: "Become a TMC", current: true },
        ]}
      />

      <section style={m.hero}>
        <h1 style={m.heroH1}>Start a Telemedicine Center in Your Area with IRME</h1>
        <p style={m.heroLead}>
          Help patients in your locality connect with verified doctors online while building a
          professional healthcare service opportunity—subject to verification and the plan you
          select with IRME.
        </p>
        <div style={m.heroCtas}>
          <Link to="/register/tmc" className="site-cta-green" style={m.btnPrimary}>
            Register as TMC
          </Link>
          <a href={whatsappUrl("I want to open a Telemedicine Center with IRME. Please share details.")} className="site-cta-ghost" style={m.btnSecondary}>
            WhatsApp TMC Team
          </a>
        </div>
      </section>

      <section id="callback" style={{ scrollMarginTop: 100 }}>
        <LeadCaptureForm
          interest="TMC"
          title="Request TMC onboarding call"
          messageHint="I want to open a Telemedicine Center in my city."
        />
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>What is a Telemedicine Center?</h2>
        <p style={m.sectionBody}>
          A Telemedicine Center (TMC) is a <strong>local assisted healthcare point</strong> where
          patients can visit, share basic symptoms and details, and connect with doctors online with
          support from the center operator. The operator helps with coordination, device or
          connectivity basics, and follow-up arrangements—without replacing a doctor&apos;s
          clinical decision-making.
        </p>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Who can start?</h2>
        <div style={m.cardGrid}>
          {whoCards.map((title) => (
            <article key={title} className="site-card-soft" style={m.card}>
              <p style={{ ...m.cardTitle, fontSize: "1rem" }}>{title}</p>
              <p style={m.cardText}>
                Final fit is reviewed during onboarding; documentation may be required.
              </p>
            </article>
          ))}
        </div>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Benefits for TMCs</h2>
        <div style={m.cardGrid}>
          {benefitCards.map((t) => (
            <article key={t} className="site-card-soft" style={m.card}>
              <p style={{ ...m.cardText, fontWeight: 600, color: "#0f172a" }}>{t}</p>
            </article>
          ))}
        </div>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>What you get after joining</h2>
        <ul style={m.list}>
          {getsList.map((x) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>City and state pages for TMC opportunities</h2>
        <p style={m.sectionBody}>
          Explore local pages for opening a telemedicine center. These pages help applicants understand
          city-wise and state-wise opportunities and give search engines clear location context.
        </p>
        <div style={m.cardGrid}>
          {seoStates.map((state) => (
            <Link key={state.slug} to={`/telemedicine-center/${state.slug}`} style={styles.locationLink}>
              Telemedicine Center in {state.name}
            </Link>
          ))}
          {seoCities.slice(0, 12).map((city) => (
            <Link key={city.slug} to={`/telemedicine-center/${city.stateSlug}/${city.slug}`} style={styles.locationLink}>
              Open TMC in {city.name}
            </Link>
          ))}
        </div>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Process to join</h2>
        <ol style={{ ...m.list, listStyle: "decimal" }}>
          <li>Submit the TMC registration form.</li>
          <li>The IRME team reviews your details.</li>
          <li>Verification or onboarding discussion (call or visit as applicable).</li>
          <li>Account activation when requirements are met.</li>
          <li>Begin assisting patients according to platform guidelines.</li>
        </ol>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Fees and charges</h2>
        <p style={m.note}>
          Registration or onboarding fees, subscription charges, or consultation-service charges{" "}
          <strong>may apply</strong> depending on the selected plan and operational model.{" "}
          <strong>Final charges will be communicated during onboarding</strong>—not on this page.
        </p>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Basic details typically required</h2>
        <ul style={m.list}>
          <li>Center or service name</li>
          <li>Operator name and contact</li>
          <li>Mobile number and email</li>
          <li>Address with state, district, and pincode</li>
          <li>Basic infrastructure description (space, connectivity, privacy for consultation)</li>
          <li>Identity or business documentation if requested for verification</li>
        </ul>
      </section>

      <section style={{ ...m.section, ...m.hero, marginTop: "48px" }}>
        <h2 style={{ ...m.heroH1, fontSize: "1.5rem" }}>
          Ready to start your Telemedicine Center?
        </h2>
        <div style={m.heroCtas}>
          <Link to="/register/tmc" className="site-cta-green" style={m.btnPrimary}>
            Register as TMC
          </Link>
          <a href="#callback" className="site-cta-ghost" style={m.btnSecondary}>
            Request callback
          </a>
        </div>
      </section>
    </main>
  </PublicLayout>
);

const styles = {
  locationLink: {
    border: "1px solid #d7e5f5",
    borderRadius: 10,
    background: "#fbfdff",
    color: "#123a6f",
    textDecoration: "none",
    padding: "10px 12px",
    fontWeight: 800,
  },
};

export default BecomeTMCPage;
