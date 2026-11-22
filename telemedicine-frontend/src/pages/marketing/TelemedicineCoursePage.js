import React from "react";
import { Link } from "react-router-dom";
import PublicLayout from "../../components/site/PublicLayout";
import Seo from "../../components/Seo";
import Breadcrumbs from "../../components/marketing/Breadcrumbs";
import LeadCaptureForm from "../../components/marketing/LeadCaptureForm";
import { m } from "../../constants/marketingLayout";
import { seoCities, seoStates } from "../../data/seoLocations";
import { whatsappUrl } from "../../constants/marketingContact";
import "../../styles/marketingResponsive.css";

const main = {
  flex: 1,
  maxWidth: "1120px",
  margin: "0 auto",
  padding: "24px 20px 48px",
  width: "100%",
  boxSizing: "border-box",
};

const learnItems = [
  "Basics of telemedicine and assisted care",
  "Patient registration and consultation flow",
  "Supporting online doctor consultations safely and respectfully",
  "Introduction to digital records and privacy-aware handling",
  "Communication skills for patient support",
  "Health service ethics and privacy basics",
  "TMC operation basics",
  "Rural healthcare and access models (introductory)",
];

const scopeItems = [
  "Telemedicine center operator or assistant",
  "Patient support executive roles (where offered by employers)",
  "Digital health assistant pathways",
  "Clinic coordination support",
  "Rural healthcare entrepreneurship (may combine with other IRME programs)",
  "Exploring TMC opportunities after training—subject to separate onboarding",
];

const TelemedicineCoursePage = () => (
  <PublicLayout>
    <Seo
      title="3 Months Telemedicine Assistant Certificate Course Online | IRME"
      description="Join IRME's 3 months online Telemedicine Assistant Certificate Course. Learn patient support, online doctor consultation workflow, digital health records and TMC operations."
      canonical="https://telemedicine.irme.in/telemedicine-course"
      keywords="telemedicine assistant course, telemedicine certificate course, digital health assistant training, online healthcare course India"
    />
    <main style={main}>
      <Breadcrumbs
        items={[
          { label: "Home", to: "/" },
          { label: "Telemedicine Course", current: true },
        ]}
      />

      <section className="marketing-hero-with-image" style={{...m.hero, ...m.heroWithImage}}>
        <div style={m.heroContent}>
          <h1 style={m.heroH1}>Telemedicine Assistant Certificate Course</h1>
          <p style={m.heroLead}>
            Learn telemedicine support and digital health operations. Build practical skills to
            support online doctor consultations, patient coordination, and rural healthcare access—
            as a trained assistant, not a substitute for licensed clinical care.
          </p>
          <div style={m.heroCtas}>
            <a href="#inquiry" className="site-cta-green" style={m.btnPrimary}>
              Apply Now
            </a>
            <a href={whatsappUrl("I want details for the 3 months Telemedicine Assistant Certificate Course.")} className="site-cta-ghost" style={m.btnSecondary}>
              WhatsApp Counsellor
            </a>
          </div>
        </div>
        <div className="marketing-hero-image" style={m.heroImage}>
          <img 
            src="/images/training-classroom.jpg" 
            alt="Medical training and telemedicine education"
            style={m.heroImageImg}
          />
        </div>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Course overview</h2>
        <p style={m.sectionBody}>
          This program is designed for <strong>learners</strong> who want to support telemedicine
          operations: assisting patients in a telemedicine setup, collecting basic information,
          coordinating online consultations, supporting appointments, and understanding digital
          health workflows. Exact curriculum and batch structure may vary and will be shared
          during counselling.
        </p>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>What learners will learn</h2>
        <div style={m.cardGrid}>
          {learnItems.map((t) => (
            <article key={t} className="site-card-soft" style={m.card}>
              <p style={{ ...m.cardText, fontWeight: 600, color: "#0f172a" }}>{t}</p>
            </article>
          ))}
        </div>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Eligibility</h2>
        <ul style={m.list}>
          <li>10th / 12th pass preferred (requirements may vary by batch).</li>
          <li>Basic computer and mobile usage is helpful.</li>
          <li>
            Healthcare or paramedical background may be preferred for some batches but is not always
            mandatory—batch-specific rules apply.
          </li>
        </ul>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Duration</h2>
        <p style={m.note}>
          <strong>Course duration:</strong> 3 months online training. Batch timing, counselling,
          assignments and certificate process will be confirmed during admission counselling.
        </p>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>All India online course</h2>
        <p style={m.sectionBody}>
          Learners can join from any Indian state or city because the training is online. City pages
          help students find relevant information for their area while keeping one consistent
          curriculum and counselling process.
        </p>
        <div style={m.cardGrid}>
          {seoStates.map((state) => (
            <Link key={state.slug} to={`/telemedicine-assistant-course/${state.slug}`} style={styles.locationLink}>
              Course in {state.name}
            </Link>
          ))}
          {seoCities.slice(0, 12).map((city) => (
            <Link key={city.slug} to={`/telemedicine-assistant-course/${city.stateSlug}/${city.slug}`} style={styles.locationLink}>
              Course in {city.name}
            </Link>
          ))}
        </div>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Fees</h2>
        <p style={m.sectionBody}>
          <strong>Fee details will be shared during admission counselling.</strong> Any deposits or
          instalments depend on the selected batch and policy at the time of enrolment.
        </p>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Scope and career directions</h2>
        <p style={m.sectionBody}>
          This training may support roles and pathways such as those below. Outcomes are not
          guaranteed and depend on effort, location, and employer or program needs.
        </p>
        <div style={m.cardGrid}>
          {scopeItems.map((t) => (
            <article key={t} className="site-card-soft" style={m.card}>
              <p style={m.cardText}>{t}</p>
            </article>
          ))}
        </div>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>How to apply</h2>
        <ol style={{ ...m.list, listStyle: "decimal" }}>
          <li>Submit an inquiry using the form below or email the counsellor.</li>
          <li>Attend a counselling or information call when scheduled.</li>
          <li>Submit documents as requested for the batch.</li>
          <li>Complete fee confirmation steps if you choose to enrol.</li>
          <li>Begin training according to the batch schedule.</li>
        </ol>
      </section>

      <section id="inquiry" style={{ ...m.section, scrollMarginTop: "100px" }}>
        <h2 style={m.sectionTitle}>Application / inquiry</h2>
        <p style={m.sectionBody}>
          Share your details below. The IRME team will contact you for counselling and batch details.
        </p>
        <LeadCaptureForm
          interest="COURSE"
          title="Request course counselling"
          messageHint="I want details about the 3 months online Telemedicine Assistant Certificate Course."
        />
      </section>

      <section style={{ ...m.section, ...m.hero, marginTop: "40px" }}>
        <h2 style={{ ...m.heroH1, fontSize: "1.4rem" }}>Explore more paths</h2>
        <div style={m.heroCtas}>
          <a href="#inquiry" className="site-cta-ghost" style={m.btnSecondary}>
            Talk to Counsellor
          </a>
          <Link to="/tmc" className="site-cta-green" style={m.btnPrimary}>
            Join as TMC after training
          </Link>
        </div>
      </section>

      <p style={m.disclaimer}>
        This page describes a training-oriented program for support roles. It does not grant a
        medical license or independent clinical practice rights. Emergency cases belong in
        hospitals or emergency services.
      </p>
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

export default TelemedicineCoursePage;
