import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";

const TELEMEDICINE_CENTERS = [
  {
    id: 1,
    name: "IRME Telemedicine Center - Satara",
    state: "Maharashtra",
    district: "Satara",
    pincode: "415001",
    contact: "+91 90000 11001",
    coordinator: "Ms. Neha Kulkarni",
    mode: "Video + In-Person Facilitation",
  },
  {
    id: 2,
    name: "IRME Rural Health Hub - Solapur",
    state: "Maharashtra",
    district: "Solapur",
    pincode: "413001",
    contact: "+91 90000 11002",
    coordinator: "Mr. Sandeep Patil",
    mode: "Video + Diagnostics Support",
  },
  {
    id: 3,
    name: "IRME Tele-Assist Point - Belagavi",
    state: "Karnataka",
    district: "Belagavi",
    pincode: "590001",
    contact: "+91 90000 11003",
    coordinator: "Ms. Riya Deshpande",
    mode: "Video + Prescription Pickup",
  },
  {
    id: 4,
    name: "IRME Telemedicine Support Center - Gulbarga",
    state: "Karnataka",
    district: "Kalaburagi",
    pincode: "585101",
    contact: "+91 90000 11004",
    coordinator: "Mr. Imran Shaikh",
    mode: "Video + Follow-up Coordination",
  },
  {
    id: 5,
    name: "IRME eHealth Kendra - Raichur",
    state: "Karnataka",
    district: "Raichur",
    pincode: "584101",
    contact: "+91 90000 11005",
    coordinator: "Ms. Asha Nayak",
    mode: "Video + Nursing Desk",
  },
  {
    id: 6,
    name: "IRME Telemedicine Center - Nanded",
    state: "Maharashtra",
    district: "Nanded",
    pincode: "431601",
    contact: "+91 90000 11006",
    coordinator: "Mr. Kiran Jadhav",
    mode: "Video + Lab Collection Support",
  },
];

const Home = () => {
  const [filters, setFilters] = useState({
    state: "",
    district: "",
    pincode: "",
  });

  const states = useMemo(
    () => [...new Set(TELEMEDICINE_CENTERS.map((c) => c.state))].sort(),
    []
  );

  const districts = useMemo(() => {
    const scoped = filters.state
      ? TELEMEDICINE_CENTERS.filter((c) => c.state === filters.state)
      : TELEMEDICINE_CENTERS;
    return [...new Set(scoped.map((c) => c.district))].sort();
  }, [filters.state]);

  const filteredCenters = useMemo(() => {
    return TELEMEDICINE_CENTERS.filter((center) => {
      const stateMatch = !filters.state || center.state === filters.state;
      const districtMatch =
        !filters.district || center.district === filters.district;
      const pinMatch =
        !filters.pincode ||
        center.pincode.toLowerCase().includes(filters.pincode.toLowerCase().trim());
      return stateMatch && districtMatch && pinMatch;
    });
  }, [filters]);

  const onFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => {
      if (name === "state") {
        return { ...prev, state: value, district: "" };
      }
      return { ...prev, [name]: value };
    });
  };

  const clearFilters = () => {
    setFilters({ state: "", district: "", pincode: "" });
  };

  return (
    <div style={styles.page}>
      <header style={styles.topbar}>
        <div style={styles.brandBlock}>
          <p style={styles.brand}>IRME INSTITUTE</p>
          <p style={styles.tagline}>Rural India Deserves Best Medical Health Services</p>
        </div>
        <div style={styles.topActions}>
          <Link to="/login" style={styles.ghostButton}>Patient Login</Link>
          <Link to="/login" style={styles.ghostButton}>Doctor Login</Link>
          <Link to="/login" style={styles.ghostButton}>TMC Login</Link>
        </div>
      </header>

      <main style={styles.main}>
        <section style={styles.heroSection}>
          <div>
            <h1 style={styles.heroTitle}>Professional Telemedicine for Rural and Urban Patients</h1>
            <p style={styles.heroText}>
              Consult doctors directly online, or connect through nearby telemedicine centers
              for guided consultations, follow-ups, and assisted care.
            </p>
            <div style={styles.ctaRow}>
              <Link to="/register/patient" style={styles.primaryButton}>
                Start Direct Consultation
              </Link>
              <Link to="/login" style={styles.secondaryButton}>
                Book with Existing Account
              </Link>
            </div>
            <div style={styles.quickLinks}>
              <Link to="/register/doctor" style={styles.inlineLink}>
                Register as Doctor
              </Link>
              <Link to="/register/tmc" style={styles.inlineLink}>
                Register Telemedicine Center
              </Link>
            </div>
          </div>
          <div style={styles.heroCard}>
            <h3 style={styles.heroCardTitle}>What You Can Do</h3>
            <ul style={styles.heroList}>
              <li>Find verified doctors and consult online</li>
              <li>Search telemedicine centers by state, district, and pincode</li>
              <li>Contact center coordinators for in-person assistance</li>
              <li>Enable doctor and center onboarding through dedicated registration</li>
            </ul>
          </div>
        </section>

        <section style={styles.searchSection}>
          <div style={styles.searchHeader}>
            <h2 style={styles.sectionTitle}>Find Telemedicine Centers</h2>
            <p style={styles.sectionText}>
              Search centers that facilitate consultations, support patient coordination, and arrange doctor meetings.
            </p>
          </div>

          <div style={styles.filtersGrid}>
            <div style={styles.filterItem}>
              <label style={styles.label}>State</label>
              <select name="state" value={filters.state} onChange={onFilterChange} style={styles.input}>
                <option value="">All States</option>
                {states.map((state) => (
                  <option key={state} value={state}>
                    {state}
                  </option>
                ))}
              </select>
            </div>

            <div style={styles.filterItem}>
              <label style={styles.label}>District</label>
              <select
                name="district"
                value={filters.district}
                onChange={onFilterChange}
                style={styles.input}
              >
                <option value="">All Districts</option>
                {districts.map((district) => (
                  <option key={district} value={district}>
                    {district}
                  </option>
                ))}
              </select>
            </div>

            <div style={styles.filterItem}>
              <label style={styles.label}>Pincode</label>
              <input
                type="text"
                name="pincode"
                value={filters.pincode}
                onChange={onFilterChange}
                style={styles.input}
                placeholder="e.g. 415001"
              />
            </div>

            <button type="button" onClick={clearFilters} style={styles.clearButton}>
              Clear Search
            </button>
          </div>

          <div style={styles.resultHeader}>
            <p style={styles.resultCount}>
              {filteredCenters.length} center{filteredCenters.length !== 1 ? "s" : ""} found
            </p>
          </div>

          <div style={styles.centerGrid}>
            {filteredCenters.map((center) => (
              <article key={center.id} style={styles.centerCard}>
                <h3 style={styles.centerTitle}>{center.name}</h3>
                <p style={styles.centerMeta}>
                  {center.district}, {center.state} - {center.pincode}
                </p>
                <p style={styles.centerMode}>{center.mode}</p>
                <p style={styles.centerContact}>
                  Coordinator: {center.coordinator}
                </p>
                <a href={`tel:${center.contact.replace(/\s/g, "")}`} style={styles.contactButton}>
                  Contact Center: {center.contact}
                </a>
              </article>
            ))}
          </div>
        </section>
      </main>

      <footer style={styles.footer}>
        <p style={styles.footerTitle}>IRME INSTITUTE Telemedicine Platform</p>
        <p style={styles.footerText}>
          Direct doctor consultations and center-facilitated care for better healthcare access.
        </p>
      </footer>
    </div>
  );
};

const styles = {
  page: {
    minHeight: "100vh",
    backgroundColor: "#f5f8fc",
    color: "#10243e",
    fontFamily: "Segoe UI, Arial, sans-serif",
  },
  topbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "16px",
    padding: "20px 28px",
    backgroundColor: "#0b2b55",
    color: "#ffffff",
    borderBottom: "3px solid #1f76d8",
  },
  brandBlock: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  brand: {
    margin: 0,
    fontSize: "22px",
    fontWeight: 800,
    letterSpacing: "0.3px",
  },
  tagline: {
    margin: 0,
    fontSize: "13px",
    opacity: 0.95,
  },
  topActions: {
    display: "flex",
    flexWrap: "wrap",
    gap: "10px",
  },
  ghostButton: {
    color: "#ffffff",
    textDecoration: "none",
    border: "1px solid rgba(255, 255, 255, 0.5)",
    borderRadius: "8px",
    padding: "8px 12px",
    fontSize: "13px",
    fontWeight: 600,
  },
  main: {
    padding: "24px 28px 36px",
    maxWidth: "1200px",
    margin: "0 auto",
  },
  heroSection: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    gap: "20px",
    background:
      "linear-gradient(140deg, rgba(11,43,85,0.95) 0%, rgba(31,118,216,0.92) 100%)",
    color: "#ffffff",
    borderRadius: "18px",
    padding: "32px",
    boxShadow: "0 10px 24px rgba(16, 36, 62, 0.2)",
  },
  heroTitle: {
    margin: 0,
    fontSize: "34px",
    lineHeight: 1.2,
  },
  heroText: {
    marginTop: "14px",
    fontSize: "16px",
    lineHeight: 1.7,
    maxWidth: "760px",
  },
  ctaRow: {
    marginTop: "22px",
    display: "flex",
    gap: "12px",
    flexWrap: "wrap",
  },
  primaryButton: {
    textDecoration: "none",
    backgroundColor: "#3be18e",
    color: "#07301c",
    fontWeight: 700,
    padding: "12px 16px",
    borderRadius: "10px",
    fontSize: "14px",
  },
  secondaryButton: {
    textDecoration: "none",
    border: "1px solid rgba(255,255,255,0.7)",
    color: "#ffffff",
    fontWeight: 700,
    padding: "12px 16px",
    borderRadius: "10px",
    fontSize: "14px",
  },
  quickLinks: {
    marginTop: "14px",
    display: "flex",
    gap: "14px",
    flexWrap: "wrap",
  },
  inlineLink: {
    color: "#d6ebff",
    textDecoration: "underline",
    fontSize: "14px",
    fontWeight: 600,
  },
  heroCard: {
    backgroundColor: "rgba(255,255,255,0.12)",
    border: "1px solid rgba(255,255,255,0.25)",
    borderRadius: "14px",
    padding: "20px",
  },
  heroCardTitle: {
    marginTop: 0,
    marginBottom: "10px",
    fontSize: "18px",
  },
  heroList: {
    margin: 0,
    paddingLeft: "18px",
    display: "grid",
    gap: "9px",
    fontSize: "14px",
    lineHeight: 1.5,
  },
  searchSection: {
    marginTop: "24px",
    backgroundColor: "#ffffff",
    borderRadius: "16px",
    padding: "24px",
    boxShadow: "0 8px 20px rgba(0,0,0,0.08)",
  },
  searchHeader: {
    marginBottom: "16px",
  },
  sectionTitle: {
    margin: 0,
    fontSize: "28px",
    color: "#123a6f",
  },
  sectionText: {
    margin: "8px 0 0",
    color: "#4c6480",
    lineHeight: 1.6,
  },
  filtersGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    gap: "12px",
    alignItems: "end",
  },
  filterItem: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  label: {
    fontSize: "13px",
    fontWeight: 600,
    color: "#244a75",
  },
  input: {
    height: "40px",
    borderRadius: "8px",
    border: "1px solid #c6d7eb",
    padding: "0 10px",
    fontSize: "14px",
  },
  clearButton: {
    height: "40px",
    borderRadius: "8px",
    border: "1px solid #8ab0dc",
    backgroundColor: "#edf4fd",
    color: "#174577",
    fontWeight: 700,
    cursor: "pointer",
  },
  resultHeader: {
    marginTop: "16px",
    marginBottom: "12px",
  },
  resultCount: {
    margin: 0,
    color: "#224f80",
    fontWeight: 600,
  },
  centerGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
    gap: "14px",
  },
  centerCard: {
    border: "1px solid #d7e5f5",
    borderRadius: "12px",
    padding: "14px",
    backgroundColor: "#fbfdff",
  },
  centerTitle: {
    margin: 0,
    color: "#113864",
    fontSize: "17px",
  },
  centerMeta: {
    margin: "8px 0 0",
    fontSize: "13px",
    color: "#4e6987",
  },
  centerMode: {
    margin: "8px 0 0",
    fontSize: "13px",
    color: "#1a3d65",
    fontWeight: 600,
  },
  centerContact: {
    margin: "10px 0",
    fontSize: "13px",
    color: "#3b5877",
  },
  contactButton: {
    textDecoration: "none",
    display: "inline-block",
    backgroundColor: "#1762bf",
    color: "#ffffff",
    borderRadius: "8px",
    padding: "9px 12px",
    fontSize: "13px",
    fontWeight: 700,
  },
  footer: {
    marginTop: "24px",
    backgroundColor: "#0b2b55",
    color: "#cfe4ff",
    textAlign: "center",
    padding: "20px",
  },
  footerTitle: {
    margin: 0,
    fontWeight: 700,
  },
  footerText: {
    margin: "8px 0 0",
    fontSize: "14px",
  },
};

export default Home;
