import React from "react";
import PublicLayout from "../components/site/PublicLayout";
import Seo from "../components/Seo";
import LeadCaptureForm from "../components/marketing/LeadCaptureForm";
import HeroSection from "../components/home/HeroSection";
import MissionAlignmentSection from "../components/home/MissionAlignmentSection";
import TmcHighlightSection from "../components/home/TmcHighlightSection";
import HowItWorksSection from "../components/home/HowItWorksSection";
import JoinIrmeSection from "../components/home/JoinIrmeSection";
import ImpactSection from "../components/home/ImpactSection";
import FinalCtaSection from "../components/home/FinalCtaSection";
import { whatsappUrl } from "../constants/marketingContact";

const Home = () => {
  return (
    <PublicLayout>
      <Seo
        title="IRME Telemedicine | Online Doctor Consultation, TMC Opportunity and Telemedicine Assistant Course"
        description="IRME Telemedicine supports online doctor consultation, assisted telemedicine centers and a 3 months online Telemedicine Assistant Certificate Course for learners across India."
        canonical="https://telemedicine.irme.in/"
        keywords="telemedicine India, online doctor consultation, telemedicine center, telemedicine assistant course, rural healthcare"
      />
      <main
        style={{
          flex: 1,
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "24px 20px 48px",
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        <HeroSection />
        <MissionAlignmentSection />
        <TmcHighlightSection />
        <HowItWorksSection />
        <JoinIrmeSection />
        <section style={styles.seoSection}>
          <h2 style={styles.heading}>Online telemedicine support for patients, centers and learners</h2>
          <p style={styles.body}>
            IRME Telemedicine is built around three practical needs: patients who need online consultation access,
            local operators who want to open assisted Telemedicine Centers, and learners who want structured training
            in telemedicine support. The platform combines doctor consultation workflow, patient chat, prescription
            records, video consultation and guided follow-up in one digital system.
          </p>
          <div style={styles.grid}>
            <article style={styles.card}>
              <h3 style={styles.cardTitle}>For patients</h3>
              <p style={styles.body}>Book online consultation with available doctors, continue chat during active consultation and download prescription records.</p>
            </article>
            <article style={styles.card}>
              <h3 style={styles.cardTitle}>For Telemedicine Centers</h3>
              <p style={styles.body}>Start a local assisted-care point where patients can receive help with digital consultation and follow-up coordination.</p>
            </article>
            <article style={styles.card}>
              <h3 style={styles.cardTitle}>For learners</h3>
              <p style={styles.body}>Join a 3 months online certificate course focused on telemedicine assistant skills and digital health support workflow.</p>
            </article>
          </div>
          <div style={styles.ctas}>
            <a href={whatsappUrl("Hello IRME, I want details about telemedicine services, TMC or course.")} style={styles.whatsapp}>WhatsApp IRME</a>
            <a href="#callback" style={styles.secondary}>Request callback</a>
          </div>
        </section>
        <ImpactSection />
        <FinalCtaSection />
        <section id="callback" style={{ scrollMarginTop: 100 }}>
          <LeadCaptureForm
            interest="GENERAL"
            title="Talk to IRME"
            messageHint="I want details about IRME Telemedicine."
          />
        </section>
      </main>
    </PublicLayout>
  );
};

const styles = {
  seoSection: {
    marginTop: 28,
    border: "1px solid #d7e5f5",
    borderRadius: 16,
    background: "#fbfdff",
    padding: 20,
  },
  heading: { margin: "0 0 10px", color: "#123a6f", fontSize: "1.45rem" },
  body: { color: "#34506f", lineHeight: 1.65, margin: 0 },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, marginTop: 16 },
  card: { border: "1px solid #d7e5f5", borderRadius: 12, background: "#fff", padding: 14 },
  cardTitle: { margin: "0 0 8px", color: "#123a6f" },
  ctas: { display: "flex", gap: 10, flexWrap: "wrap", marginTop: 16 },
  whatsapp: { background: "#16a34a", color: "#fff", textDecoration: "none", borderRadius: 10, padding: "10px 14px", fontWeight: 800 },
  secondary: { background: "#edf4fd", color: "#174577", textDecoration: "none", border: "1px solid #8ab0dc", borderRadius: 10, padding: "10px 14px", fontWeight: 800 },
};

export default Home;
