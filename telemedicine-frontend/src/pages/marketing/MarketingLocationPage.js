import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { API_BASE_URL } from "../../api/config";
import PublicLayout from "../../components/site/PublicLayout";
import Seo from "../../components/Seo";
import Breadcrumbs from "../../components/marketing/Breadcrumbs";
import LeadCaptureForm from "../../components/marketing/LeadCaptureForm";
import { m } from "../../constants/marketingLayout";
import { citiesForState, getCityBySlug, getStateBySlug, seoStates } from "../../data/seoLocations";
import { whatsappUrl } from "../../constants/marketingContact";

const main = {
  flex: 1,
  maxWidth: "1120px",
  margin: "0 auto",
  padding: "24px 20px 48px",
  width: "100%",
  boxSizing: "border-box",
};

const nearbyCities = (stateSlug, citySlug) =>
  citiesForState(stateSlug).filter((city) => city.slug !== citySlug).slice(0, 8);

const pageSlug = (type, stateSlug, citySlug) =>
  `${type === "course" ? "course" : "tmc"}-${stateSlug}${citySlug ? `-${citySlug}` : ""}`;

const AdminPageBody = ({ page }) => {
  if (!page?.body) return null;
  return (
    <section style={m.section}>
      {page.body.split(/\n{2,}/).filter(Boolean).map((paragraph) => (
        <p key={paragraph.slice(0, 40)} style={m.sectionBody}>{paragraph}</p>
      ))}
    </section>
  );
};

const LocationLinks = ({ type, stateSlug, citySlug }) => {
  const base = type === "course" ? "/telemedicine-assistant-course" : "/telemedicine-center";
  const localCities = nearbyCities(stateSlug, citySlug);
  return (
    <section style={m.section}>
      <h2 style={m.sectionTitle}>Related locations</h2>
      <div style={m.cardGrid}>
        <Link style={styles.relatedLink} to={`${base}/${stateSlug}`}>
          {type === "course" ? "Telemedicine assistant course" : "Telemedicine center"} in {getStateBySlug(stateSlug)?.name}
        </Link>
        {localCities.map((city) => (
          <Link key={city.slug} style={styles.relatedLink} to={`${base}/${stateSlug}/${city.slug}`}>
            {type === "course" ? "Course" : "Center opportunity"} in {city.name}
          </Link>
        ))}
        {seoStates.filter((state) => state.slug !== stateSlug).slice(0, 5).map((state) => (
          <Link key={state.slug} style={styles.relatedLink} to={`${base}/${state.slug}`}>
            {type === "course" ? "Course" : "TMC"} in {state.name}
          </Link>
        ))}
      </div>
    </section>
  );
};

const TmcLocationContent = ({ state, city, pageOverride }) => {
  const location = city ? `${city.name}, ${state.name}` : state.name;
  const fallbackTitle = city
    ? `Open Telemedicine Center in ${city.name} | IRME TMC Opportunity`
    : `Open Telemedicine Center in ${state.name} | IRME TMC Opportunity`;
  const title = pageOverride?.title || fallbackTitle;
  const description = pageOverride?.meta_description || `Start an assisted telemedicine center in ${location}. IRME supports local operators with digital consultation workflow, patient coordination and onboarding guidance.`;
  const h1 = pageOverride?.h1 || (city ? `Open Telemedicine Center in ${city.name}` : `Open Telemedicine Center in ${state.name}`);
  const intro = pageOverride?.intro || "Build a local assisted healthcare access point where patients can get help with online doctor consultation, basic digital registration, follow-up coordination and privacy-aware support. IRME helps interested centers understand the operational model before activation.";

  return (
    <>
      <Seo
        title={title}
        description={description}
        canonical={`https://telemedicine.irme.in${window.location.pathname}`}
        keywords={`telemedicine center in ${location}, open telemedicine center, TMC franchise, online doctor consultation center`}
        schema={{
          "@context": "https://schema.org",
          "@type": "Service",
          name: `Telemedicine Center Opportunity in ${location}`,
          provider: { "@type": "Organization", name: "IRME Telemedicine" },
          areaServed: location,
          serviceType: "Assisted telemedicine center onboarding",
        }}
      />
      <section style={m.hero}>
        <h1 style={m.heroH1}>{h1}</h1>
        <p style={m.heroLead}>{intro}</p>
        <div style={m.heroCtas}>
          <a href="#callback" className="site-cta-green" style={m.btnPrimary}>Request callback</a>
          <a href={whatsappUrl(`I want to open a telemedicine center in ${location}. Please share details.`)} className="site-cta-ghost" style={m.btnSecondary}>WhatsApp TMC team</a>
        </div>
      </section>

      <AdminPageBody page={pageOverride} />

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Why {location} needs assisted telemedicine access</h2>
        <p style={m.sectionBody}>
          Many patients need guidance before they can use online consultation: registration, symptoms summary, video setup,
          prescription download and follow-up reminders. A well-run Telemedicine Center can become a trusted local bridge
          between patients and verified online doctors, especially for families who are not comfortable managing everything
          on a phone by themselves.
        </p>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>What an IRME Telemedicine Center can support</h2>
        <div style={m.cardGrid}>
          {[
            "Assisted patient onboarding and consultation booking",
            "Online video consultation workflow with doctors",
            "Prescription and follow-up coordination",
            "Basic digital record support inside the platform",
            "Local patient education for non-emergency use",
            "Operational guidance before center activation",
          ].map((item) => (
            <article key={item} style={m.card} className="site-card-soft">
              <p style={{ ...m.cardText, fontWeight: 700, color: "#0f172a" }}>{item}</p>
            </article>
          ))}
        </div>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Who can apply in {location}</h2>
        <p style={m.sectionBody}>
          Existing clinics, pharmacies, computer centers, CSC-style operators, NGOs, community workers and rural
          entrepreneurs can request details. Activation is subject to verification, privacy setup, local suitability and
          platform policy. Emergency medical cases must always be referred to nearby hospitals or emergency services.
        </p>
      </section>

      <section id="callback" style={{ scrollMarginTop: 100 }}>
        <LeadCaptureForm
          interest="TMC"
          title={`Get TMC details for ${location}`}
          locationLabel={location}
          messageHint={`I want to know how to open a telemedicine center in ${location}.`}
        />
      </section>

      <LocationLinks type="tmc" stateSlug={state.slug} citySlug={city?.slug} />
    </>
  );
};

const CourseLocationContent = ({ state, city, pageOverride }) => {
  const location = city ? `${city.name}, ${state.name}` : state.name;
  const fallbackTitle = city
    ? `Telemedicine Assistant Certificate Course in ${city.name} | 3 Months Online`
    : `Telemedicine Assistant Certificate Course in ${state.name} | 3 Months Online`;
  const title = pageOverride?.title || fallbackTitle;
  const description = pageOverride?.meta_description || `Join IRME's 3 months online Telemedicine Assistant Certificate Course for learners in ${location}. Learn patient coordination, online consultation support and digital health workflow.`;
  const h1 = pageOverride?.h1 || (city ? `Telemedicine Assistant Course in ${city.name}` : `Telemedicine Assistant Course in ${state.name}`);
  const intro = pageOverride?.intro || "A 3 months online certificate course for learners who want to support telemedicine operations, patient coordination and digital health workflows. Training is online and designed for all-India participation.";

  return (
    <>
      <Seo
        title={title}
        description={description}
        canonical={`https://telemedicine.irme.in${window.location.pathname}`}
        keywords={`telemedicine assistant course in ${location}, telemedicine certificate course, digital health assistant training, online healthcare course`}
        schema={{
          "@context": "https://schema.org",
          "@type": "Course",
          name: `Telemedicine Assistant Certificate Course in ${location}`,
          provider: { "@type": "Organization", name: "IRME Telemedicine" },
          educationalCredentialAwarded: "Certificate",
          courseMode: "online",
          timeRequired: "P3M",
        }}
      />
      <section style={m.hero}>
        <h1 style={m.heroH1}>{h1}</h1>
        <p style={m.heroLead}>{intro}</p>
        <div style={m.heroCtas}>
          <a href="#callback" className="site-cta-green" style={m.btnPrimary}>Request course callback</a>
          <a href={whatsappUrl(`I want details for the 3 months telemedicine assistant course in ${location}.`)} className="site-cta-ghost" style={m.btnSecondary}>WhatsApp course counsellor</a>
        </div>
      </section>

      <AdminPageBody page={pageOverride} />

      <section style={m.section}>
        <h2 style={m.sectionTitle}>3 months online training for {location}</h2>
        <p style={m.sectionBody}>
          The course focuses on non-clinical support skills: patient intake, consultation flow, appointment coordination,
          privacy-aware handling of records, prescription download support, communication etiquette and basic TMC operations.
          It does not create a medical license and does not authorize independent clinical practice.
        </p>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>What you learn</h2>
        <div style={m.cardGrid}>
          {[
            "Telemedicine basics and patient support workflow",
            "Online consultation room and follow-up coordination",
            "Digital record and privacy fundamentals",
            "Communication skills for assisted healthcare",
            "TMC operation basics and patient guidance",
            "Career pathways in digital health support roles",
          ].map((item) => (
            <article key={item} style={m.card} className="site-card-soft">
              <p style={{ ...m.cardText, fontWeight: 700, color: "#0f172a" }}>{item}</p>
            </article>
          ))}
        </div>
      </section>

      <section style={m.section}>
        <h2 style={m.sectionTitle}>Who should apply</h2>
        <p style={m.sectionBody}>
          Students, clinic assistants, pharmacy staff, rural entrepreneurs, computer center operators and healthcare
          support workers from {location} can request counselling. Basic mobile/computer familiarity is helpful.
        </p>
      </section>

      <section id="callback" style={{ scrollMarginTop: 100 }}>
        <LeadCaptureForm
          interest="COURSE"
          title={`Course counselling for ${location}`}
          locationLabel={location}
          messageHint={`I want details about the 3 months online telemedicine assistant certificate course for ${location}.`}
        />
      </section>

      <LocationLinks type="course" stateSlug={state.slug} citySlug={city?.slug} />
    </>
  );
};

const MarketingLocationPage = ({ type }) => {
  const { stateSlug, citySlug } = useParams();
  const state = getStateBySlug(stateSlug);
  const city = citySlug ? getCityBySlug(stateSlug, citySlug) : null;
  const [pageOverride, setPageOverride] = useState(null);
  const slug = useMemo(() => pageSlug(type, stateSlug, citySlug), [type, stateSlug, citySlug]);

  useEffect(() => {
    let mounted = true;
    setPageOverride(null);
    fetch(`${API_BASE_URL}/marketing/landing-pages/${slug}/`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (mounted && data) setPageOverride(data);
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, [slug]);

  if (!state || (citySlug && !city)) {
    return (
      <PublicLayout>
        <main style={main}>
          <h1 style={m.sectionTitle}>Location not found</h1>
          <p style={m.sectionBody}>Please choose another state or city page.</p>
          <Link to={type === "course" ? "/telemedicine-course" : "/tmc"} style={m.btnPrimary}>Go back</Link>
        </main>
      </PublicLayout>
    );
  }

  return (
    <PublicLayout>
      <main style={main}>
        <Breadcrumbs
          items={[
            { label: "Home", to: "/" },
            { label: type === "course" ? "Telemedicine Course" : "Telemedicine Center", to: type === "course" ? "/telemedicine-course" : "/tmc" },
            { label: city ? city.name : state.name, current: true },
          ]}
        />
        {type === "course" ? (
          <CourseLocationContent state={state} city={city} pageOverride={pageOverride} />
        ) : (
          <TmcLocationContent state={state} city={city} pageOverride={pageOverride} />
        )}
      </main>
    </PublicLayout>
  );
};

const styles = {
  relatedLink: {
    display: "block",
    border: "1px solid #d7e5f5",
    borderRadius: 10,
    background: "#fbfdff",
    color: "#123a6f",
    textDecoration: "none",
    padding: "10px 12px",
    fontWeight: 800,
  },
};

export default MarketingLocationPage;
