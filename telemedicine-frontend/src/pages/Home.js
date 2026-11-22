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
          padding: "32px 24px 64px",
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
    marginTop: 32,
    border: "1px solid #e7ecf1",
    borderRadius: 20,
    background: "#ffffff",
    padding: 32,
    boxShadow: "0 4px 6px -1px rgba(0, 32, 67, 0.08)",
  },
  heading: { 
    margin: "0 0 16px", 
    color: "#10243e", 
    fontSize: "1.75rem",
    fontWeight: 700,
    lineHeight: 1.25,
  },
  body: { 
    color: "#4c6480", 
    lineHeight: 1.65, 
    margin: 0,
    fontSize: "1rem",
  },
  grid: { 
    display: "grid", 
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", 
    gap: 20, 
    marginTop: 24,
  },
  card: { 
    border: "1px solid #e7ecf1", 
    borderRadius: 16, 
    background: "#f8fafb", 
    padding: 24,
    transition: "transform 200ms ease, box-shadow 200ms ease",
    cursor: "default",
  },
  cardTitle: { 
    margin: "0 0 12px", 
    color: "#10243e",
    fontSize: "1.125rem",
    fontWeight: 600,
  },
  ctas: { 
    display: "flex", 
    gap: 12, 
    flexWrap: "wrap", 
    marginTop: 24,
  },
  whatsapp: { 
    background: "#22C55E", 
    color: "#fff", 
    textDecoration: "none", 
    borderRadius: 10, 
    padding: "12px 20px", 
    fontWeight: 600,
    fontSize: "0.9375rem",
    boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.1)",
    transition: "background 150ms ease, box-shadow 150ms ease",
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
  },
  secondary: { 
    background: "#e8f2ff", 
    color: "#1762bf", 
    textDecoration: "none", 
    border: "1px solid #9ec9ff", 
    borderRadius: 10, 
    padding: "12px 20px", 
    fontWeight: 600,
    fontSize: "0.9375rem",
    transition: "background 150ms ease, border-color 150ms ease",
    display: "inline-flex",
    alignItems: "center",
  },
};

export default Home;
