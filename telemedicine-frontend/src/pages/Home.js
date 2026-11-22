import React from "react";
import { Link } from "react-router-dom";
import PublicLayout from "../components/site/PublicLayout";
import Seo from "../components/Seo";
import { whatsappUrl } from "../constants/marketingContact";
import { SITE_CTA_GREEN, SITE_HEADER_NAVY, SITE_DEEP_BLUE } from "../constants/brandTheme";
import "./HomeResponsive.css";

const Home = () => {
  return (
    <PublicLayout>
      <Seo
        title="IRME Telemedicine | Professional Training & Telemedicine Center Network"
        description="IRME Telemedicine offers a 3-month online Telemedicine Assistant Certificate Course and opportunities to open assisted Telemedicine Centers across India. Join India's growing rural healthcare support network."
        canonical="https://telemedicine.irme.in/"
        keywords="telemedicine training, telemedicine certificate course, telemedicine center franchise, rural healthcare, digital health training India"
      />
      <main style={styles.main}>
        {/* Hero Section */}
        <section className="home-hero">
          <div style={styles.heroContent}>
            <h1 style={styles.heroTitle}>
              Empowering Rural Healthcare Through Training and Telemedicine Centers
            </h1>
            <p style={styles.heroSubtitle}>
              IRME Telemedicine connects communities with quality healthcare through professional 
              training programmes and a network of assisted Telemedicine Centers across India.
            </p>
          </div>
          <div style={styles.heroImage}>
            <picture>
              <source 
                media="(max-width: 768px)" 
                srcSet="/images/hero-tmc-mobile.webp" 
                type="image/webp" 
              />
              <source 
                media="(max-width: 768px)" 
                srcSet="/images/hero-tmc-mobile.jpg" 
                type="image/jpeg" 
              />
              <source 
                srcSet="/images/hero-tmc-desktop.webp" 
                type="image/webp" 
              />
              <img 
                src="/images/hero-tmc-desktop.jpg" 
                alt="IRME Telemedicine Center: health worker assisting rural patient with video consultation, connecting with doctor through IRME telemedicine platform"
                style={styles.heroImageImg}
                loading="eager"
              />
            </picture>
          </div>
        </section>

        {/* Core Offerings Section */}
        <section style={styles.section}>
          <h2 style={styles.sectionTitle}>Our Core Programmes</h2>
          <p style={styles.sectionSubtitle}>
            Choose the path that fits your goals—whether you want to build skills in telemedicine 
            support or establish a healthcare service point in your community.
          </p>
          
          <div className="home-offerings-grid">
            {/* Telemedicine Training */}
            <article style={styles.offeringCard}>
              <div style={styles.offeringImage}>
                <img 
                  src="/images/training-classroom.jpg" 
                  alt="Medical training and education"
                  style={styles.offeringImageImg}
                />
              </div>
              <div style={styles.offeringContent}>
                <h3 style={styles.offeringTitle}>
                  Telemedicine Assistant Certificate Course
                </h3>
                <p style={styles.offeringDescription}>
                  3-month online programme to become a certified Telemedicine Assistant. Learn patient 
                  support, consultation workflow, digital health records, and TMC operations.
                </p>
                <div style={styles.offeringBenefits}>
                  <div style={styles.benefitItem}>✓ 3 months online training</div>
                  <div style={styles.benefitItem}>✓ Certificate upon completion</div>
                  <div style={styles.benefitItem}>✓ Practical skills & workflow</div>
                  <div style={styles.benefitItem}>✓ Career support guidance</div>
                </div>
                <div style={styles.offeringCtas}>
                  <Link to="/telemedicine-course" style={styles.btnPrimary}>
                    View Course Details
                  </Link>
                  <a 
                    href={whatsappUrl("I want details about the Telemedicine Assistant Certificate Course.")} 
                    style={styles.btnSecondary}
                  >
                    WhatsApp Enquiry
                  </a>
                </div>
              </div>
            </article>

            {/* TMC Opportunity */}
            <article style={styles.offeringCard}>
              <div style={styles.offeringImage}>
                <img 
                  src="/images/tmc-center.jpg" 
                  alt="Telemedicine center and healthcare facility"
                  style={styles.offeringImageImg}
                />
              </div>
              <div style={styles.offeringContent}>
                <h3 style={styles.offeringTitle}>
                  Open a Telemedicine Center
                </h3>
                <p style={styles.offeringDescription}>
                  Establish a local assisted healthcare point in your community. Connect patients with 
                  verified doctors online while building a professional service opportunity.
                </p>
                <div style={styles.offeringBenefits}>
                  <div style={styles.benefitItem}>✓ Dashboard & platform access</div>
                  <div style={styles.benefitItem}>✓ Operational training provided</div>
                  <div style={styles.benefitItem}>✓ Doctor network connection</div>
                  <div style={styles.benefitItem}>✓ Income opportunity</div>
                </div>
                <div style={styles.offeringCtas}>
                  <Link to="/tmc" style={styles.btnPrimary}>
                    Learn About TMCs
                  </Link>
                  <a 
                    href={whatsappUrl("I want to open a Telemedicine Center with IRME.")} 
                    style={styles.btnSecondary}
                  >
                    WhatsApp TMC Team
                  </a>
                </div>
              </div>
            </article>
          </div>
        </section>

        {/* How It Works */}
        <section style={styles.section}>
          <h2 style={styles.sectionTitle}>How IRME Telemedicine Works</h2>
          <div className="home-steps-grid">
            <div style={styles.stepCard}>
              <div style={styles.stepNumber}>1</div>
              <h3 style={styles.stepTitle}>Patient Visits TMC or Registers Online</h3>
              <p style={styles.stepText}>
                Patients can visit a local Telemedicine Center for assisted care or register 
                directly on the platform for online consultations.
              </p>
            </div>
            <div style={styles.stepCard}>
              <div style={styles.stepNumber}>2</div>
              <h3 style={styles.stepTitle}>Connect with Verified Doctors</h3>
              <p style={styles.stepText}>
                Trained TMC assistants or our platform connects patients with verified doctors 
                for video or chat consultations.
              </p>
            </div>
            <div style={styles.stepCard}>
              <div style={styles.stepNumber}>3</div>
              <h3 style={styles.stepTitle}>Consultation & Digital Records</h3>
              <p style={styles.stepText}>
                Doctors provide consultation, prescriptions, and follow-up care. All records 
                are maintained digitally for easy access.
              </p>
            </div>
          </div>
        </section>

        {/* Trust Indicators */}
        <section style={styles.section}>
          <h2 style={styles.sectionTitle}>Why Choose IRME</h2>
          <div className="home-trust-grid">
            <div style={styles.trustCard}>
              <div style={styles.trustIcon}>🎓</div>
              <h3 style={styles.trustTitle}>Professional Training</h3>
              <p style={styles.trustText}>
                Structured curriculum developed for practical telemedicine support skills
              </p>
            </div>
            <div style={styles.trustCard}>
              <div style={styles.trustIcon}>🏥</div>
              <h3 style={styles.trustTitle}>Verified Doctor Network</h3>
              <p style={styles.trustText}>
                Access to qualified, verified medical professionals across specialties
              </p>
            </div>
            <div style={styles.trustCard}>
              <div style={styles.trustIcon}>📱</div>
              <h3 style={styles.trustTitle}>Digital Platform</h3>
              <p style={styles.trustText}>
                Complete technology platform for consultations, records, and coordination
              </p>
            </div>
            <div style={styles.trustCard}>
              <div style={styles.trustIcon}>🤝</div>
              <h3 style={styles.trustTitle}>Operational Support</h3>
              <p style={styles.trustText}>
                Ongoing guidance and training for TMC operators and assistants
              </p>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section style={styles.ctaSection}>
          <h2 style={styles.ctaTitle}>Ready to Get Started?</h2>
          <p style={styles.ctaText}>
            Join IRME Telemedicine today and be part of India's growing rural healthcare support network.
          </p>
          <div className="home-cta-buttons">
            <Link to="/telemedicine-course" style={styles.btnPrimaryCta}>
              Explore Training Course
            </Link>
            <Link to="/tmc" style={styles.btnPrimaryCta}>
              Start a TMC
            </Link>
            <Link to="/register/patient" style={styles.btnSecondaryCta}>
              Patient Registration
            </Link>
            <Link to="/join/doctor" style={styles.btnSecondaryCta}>
              Join as Doctor
            </Link>
          </div>
          <p style={styles.ctaSmall}>
            Already registered?{" "}
            <Link to="/login" style={styles.ctaLink}>
              Sign in here
            </Link>
          </p>
        </section>

        {/* Additional Info */}
        <section style={styles.infoSection}>
          <h2 style={styles.sectionTitle}>Supporting Rural Healthcare Access</h2>
          <p style={styles.sectionBody}>
            IRME Telemedicine is built around practical healthcare needs: patients who need accessible 
            consultation, local operators who want to establish service points, and learners who want 
            structured training in telemedicine support. The platform combines doctor consultation workflow, 
            patient coordination, digital records, video consultation, and guided follow-up in one system.
          </p>
          <div className="home-info-grid">
            <div style={styles.infoCard}>
              <h3 style={styles.infoCardTitle}>For Learners</h3>
              <p style={styles.infoCardText}>
                Gain certification and practical skills in telemedicine operations, patient support, 
                and digital health workflows through our structured training programme.
              </p>
            </div>
            <div style={styles.infoCard}>
              <h3 style={styles.infoCardTitle}>For Entrepreneurs</h3>
              <p style={styles.infoCardText}>
                Start a local assisted-care point where patients can receive help with digital 
                consultation and follow-up coordination.
              </p>
            </div>
            <div style={styles.infoCard}>
              <h3 style={styles.infoCardTitle}>For Communities</h3>
              <p style={styles.infoCardText}>
                Access quality healthcare through local Telemedicine Centers or direct online 
                consultations with verified doctors.
              </p>
            </div>
          </div>
        </section>
      </main>
    </PublicLayout>
  );
};

const styles = {
  main: {
    flex: 1,
    maxWidth: "1200px",
    margin: "0 auto",
    padding: "40px 24px 64px",
    width: "100%",
    boxSizing: "border-box",
  },

  heroContent: {
    display: "flex",
    flexDirection: "column",
    gap: "24px",
  },
  heroTitle: {
    margin: 0,
    fontSize: "clamp(2rem, 5vw, 3rem)",
    fontWeight: 700,
    lineHeight: 1.2,
    color: SITE_HEADER_NAVY,
    letterSpacing: "-0.02em",
  },
  heroSubtitle: {
    margin: 0,
    fontSize: "1.25rem",
    lineHeight: 1.6,
    color: "#475569",
    fontWeight: 400,
  },
  heroImage: {
    borderRadius: "16px",
    overflow: "hidden",
    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
  },
  heroImageImg: {
    width: "100%",
    height: "auto",
    display: "block",
    objectFit: "cover",
  },

  // Sections
  section: {
    marginTop: "80px",
  },
  sectionTitle: {
    margin: "0 0 16px",
    fontSize: "2.25rem",
    fontWeight: 600,
    color: SITE_HEADER_NAVY,
    textAlign: "center",
    letterSpacing: "-0.01em",
  },
  sectionSubtitle: {
    margin: "0 auto 48px",
    fontSize: "1.125rem",
    lineHeight: 1.7,
    color: "#64748b",
    textAlign: "center",
    maxWidth: "760px",
    fontWeight: 400,
  },
  sectionBody: {
    fontSize: "1.0625rem",
    lineHeight: 1.75,
    color: "#475569",
    maxWidth: "860px",
    margin: "0 auto 32px",
    fontWeight: 400,
  },

  offeringCard: {
    background: "#ffffff",
    borderRadius: "20px",
    overflow: "hidden",
    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    border: "1px solid #e7ecf1",
    transition: "box-shadow 200ms ease, transform 200ms ease",
  },
  offeringImage: {
    height: "250px",
    overflow: "hidden",
    backgroundColor: "#f1f5f9",
  },
  offeringImageImg: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    display: "block",
  },
  offeringContent: {
    padding: "32px",
  },
  offeringTitle: {
    margin: "0 0 16px",
    fontSize: "1.5rem",
    fontWeight: 600,
    color: SITE_HEADER_NAVY,
    lineHeight: 1.3,
  },
  offeringDescription: {
    margin: "0 0 24px",
    fontSize: "1rem",
    lineHeight: 1.65,
    color: "#64748b",
    fontWeight: 400,
  },
  offeringBenefits: {
    display: "grid",
    gap: "12px",
    marginBottom: "28px",
  },
  benefitItem: {
    fontSize: "0.9375rem",
    color: "#475569",
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontWeight: 500,
  },
  offeringCtas: {
    display: "flex",
    gap: "12px",
    flexWrap: "wrap",
  },

  stepCard: {
    textAlign: "center",
    padding: "32px 24px",
    background: "#ffffff",
    borderRadius: "16px",
    border: "1px solid #e7ecf1",
  },
  stepNumber: {
    width: "56px",
    height: "56px",
    borderRadius: "50%",
    background: `linear-gradient(135deg, ${SITE_DEEP_BLUE}, ${SITE_CTA_GREEN})`,
    color: "#ffffff",
    fontSize: "1.5rem",
    fontWeight: 700,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    margin: "0 auto 20px",
  },
  stepTitle: {
    margin: "0 0 12px",
    fontSize: "1.125rem",
    fontWeight: 600,
    color: SITE_HEADER_NAVY,
  },
  stepText: {
    margin: 0,
    fontSize: "1rem",
    lineHeight: 1.6,
    color: "#64748b",
    fontWeight: 400,
  },

  trustCard: {
    textAlign: "center",
    padding: "32px 20px",
  },
  trustIcon: {
    fontSize: "3rem",
    marginBottom: "16px",
  },
  trustTitle: {
    margin: "0 0 12px",
    fontSize: "1.125rem",
    fontWeight: 600,
    color: SITE_HEADER_NAVY,
  },
  trustText: {
    margin: 0,
    fontSize: "0.9375rem",
    lineHeight: 1.6,
    color: "#64748b",
    fontWeight: 400,
  },

  // CTA Section
  ctaSection: {
    marginTop: "80px",
    padding: "56px 40px",
    background: `linear-gradient(135deg, ${SITE_HEADER_NAVY} 0%, ${SITE_DEEP_BLUE} 55%, #0a5c5c 100%)`,
    borderRadius: "24px",
    textAlign: "center",
    color: "#ffffff",
  },
  ctaTitle: {
    margin: "0 0 16px",
    fontSize: "2rem",
    fontWeight: 600,
    letterSpacing: "-0.01em",
  },
  ctaText: {
    margin: "0 auto 32px",
    fontSize: "1.125rem",
    lineHeight: 1.6,
    maxWidth: "640px",
    opacity: 0.95,
    fontWeight: 400,
  },
  ctaSmall: {
    fontSize: "0.9375rem",
    opacity: 0.9,
    margin: 0,
  },
  ctaLink: {
    color: "#a7f3d0",
    fontWeight: 600,
    textDecoration: "none",
  },

  // Info Section
  infoSection: {
    marginTop: "80px",
  },
  infoCard: {
    padding: "32px 28px",
    background: "#ffffff",
    borderRadius: "16px",
    border: "1px solid #e7ecf1",
  },
  infoCardTitle: {
    margin: "0 0 12px",
    fontSize: "1.25rem",
    fontWeight: 600,
    color: SITE_HEADER_NAVY,
  },
  infoCardText: {
    margin: 0,
    fontSize: "1rem",
    lineHeight: 1.65,
    color: "#64748b",
    fontWeight: 400,
  },

  // Buttons
  btnPrimary: {
    display: "inline-block",
    textDecoration: "none",
    backgroundColor: SITE_CTA_GREEN,
    color: "#ffffff",
    fontWeight: 600,
    padding: "12px 24px",
    borderRadius: "10px",
    fontSize: "0.9375rem",
    border: "none",
    cursor: "pointer",
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
    transition: "background 150ms ease, box-shadow 150ms ease",
  },
  btnSecondary: {
    display: "inline-block",
    textDecoration: "none",
    backgroundColor: "#e8f2ff",
    color: "#1762bf",
    fontWeight: 600,
    padding: "12px 24px",
    borderRadius: "10px",
    fontSize: "0.9375rem",
    border: "1px solid #9ec9ff",
    cursor: "pointer",
    transition: "background 150ms ease, border-color 150ms ease",
  },
  btnPrimaryCta: {
    display: "inline-block",
    textDecoration: "none",
    backgroundColor: SITE_CTA_GREEN,
    color: "#ffffff",
    fontWeight: 600,
    padding: "14px 32px",
    borderRadius: "10px",
    fontSize: "1rem",
    border: "none",
    cursor: "pointer",
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.2)",
    transition: "background 150ms ease, box-shadow 150ms ease",
  },
  btnSecondaryCta: {
    display: "inline-block",
    textDecoration: "none",
    backgroundColor: "rgba(255, 255, 255, 0.15)",
    color: "#ffffff",
    fontWeight: 600,
    padding: "14px 32px",
    borderRadius: "10px",
    fontSize: "1rem",
    border: "2px solid rgba(255, 255, 255, 0.4)",
    cursor: "pointer",
    transition: "background 150ms ease, border-color 150ms ease",
  },
};

export default Home;
