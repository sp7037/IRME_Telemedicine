import React, { useMemo, useState } from "react";
import { TELEMEDICINE_CENTERS } from "../../data/telemedicineCenters";
import { SITE_HEADER_NAVY, SITE_DEEP_BLUE } from "../../constants/brandTheme";

const FindCentersSection = ({ showIntro = true }) => {
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
        center.pincode
          .toLowerCase()
          .includes(filters.pincode.toLowerCase().trim());
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
    <section
      className="find-centers-section site-card-soft"
      style={{
        marginTop: showIntro ? "32px" : 0,
        backgroundColor: "#ffffff",
        borderRadius: "18px",
        padding: "clamp(22px, 3vw, 34px)",
        boxShadow: "0 10px 40px rgba(6, 43, 79, 0.09)",
      }}
      aria-labelledby={showIntro ? "find-centers-heading" : undefined}
    >
      {showIntro && (
        <header style={{ marginBottom: "22px" }}>
          <h2
            id="find-centers-heading"
            style={{
              margin: 0,
              fontSize: "clamp(1.35rem, 3vw, 1.75rem)",
              fontWeight: 800,
              color: SITE_HEADER_NAVY,
              letterSpacing: "-0.02em",
              lineHeight: 1.2,
            }}
          >
            Find Telemedicine Centers
          </h2>
          <p
            style={{
              margin: "10px 0 0",
              color: "#64748b",
              lineHeight: 1.65,
              fontSize: "1rem",
              maxWidth: "720px",
            }}
          >
            Search centers that facilitate consultations, support patient coordination,
            and arrange doctor meetings.
          </p>
        </header>
      )}

      <div className="find-centers-filters-grid">
        <div style={s.filterItem}>
          <label style={s.label} htmlFor="fc-state">
            State
          </label>
          <select
            id="fc-state"
            name="state"
            value={filters.state}
            onChange={onFilterChange}
            className="find-centers-field"
          >
            <option value="">All States</option>
            {states.map((state) => (
              <option key={state} value={state}>
                {state}
              </option>
            ))}
          </select>
        </div>

        <div style={s.filterItem}>
          <label style={s.label} htmlFor="fc-district">
            District
          </label>
          <select
            id="fc-district"
            name="district"
            value={filters.district}
            onChange={onFilterChange}
            className="find-centers-field"
          >
            <option value="">All Districts</option>
            {districts.map((district) => (
              <option key={district} value={district}>
                {district}
              </option>
            ))}
          </select>
        </div>

        <div style={s.filterItem}>
          <label style={s.label} htmlFor="fc-pin">
            Pincode
          </label>
          <input
            id="fc-pin"
            type="text"
            name="pincode"
            value={filters.pincode}
            onChange={onFilterChange}
            className="find-centers-field"
            placeholder="e.g. 415001"
            autoComplete="postal-code"
          />
        </div>

        <button
          type="button"
          onClick={clearFilters}
          className="find-centers-clear-btn"
        >
          Clear Search
        </button>
      </div>

      <div style={{ marginTop: "20px", marginBottom: "14px" }}>
        <p
          style={{
            margin: 0,
            color: SITE_DEEP_BLUE,
            fontWeight: 700,
            fontSize: "15px",
          }}
        >
          {filteredCenters.length} center{filteredCenters.length !== 1 ? "s" : ""}{" "}
          found
        </p>
      </div>

      <div className="find-centers-grid">
        {filteredCenters.map((center) => (
          <article
            key={center.id}
            className="find-centers-center-card site-card-soft"
            style={{
              border: "1px solid #e2e8f0",
              borderRadius: "14px",
              padding: "18px 16px",
              backgroundColor: "#ffffff",
              boxShadow: "0 4px 14px rgba(15, 23, 42, 0.04)",
            }}
          >
            <h3
              style={{
                margin: 0,
                color: SITE_HEADER_NAVY,
                fontSize: "17px",
                fontWeight: 800,
                lineHeight: 1.3,
              }}
            >
              {center.name}
            </h3>
            <p style={s.centerMeta}>
              {center.district}, {center.state} - {center.pincode}
            </p>
            <p style={s.centerMode}>{center.mode}</p>
            <p style={{ ...s.centerContact, marginBottom: 0 }}>
              Coordinator: {center.coordinator}
            </p>
            <a
              href={`tel:${center.contact.replace(/\s/g, "")}`}
              className="find-centers-contact-btn"
            >
              Contact Center: {center.contact}
            </a>
          </article>
        ))}
      </div>
    </section>
  );
};

const s = {
  filterItem: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  label: {
    fontSize: "12px",
    fontWeight: 700,
    color: "#475569",
    letterSpacing: "0.02em",
  },
  centerMeta: {
    margin: "10px 0 0",
    fontSize: "13px",
    color: "#64748b",
    lineHeight: 1.45,
  },
  centerMode: {
    margin: "10px 0 0",
    fontSize: "14px",
    color: SITE_HEADER_NAVY,
    fontWeight: 700,
    lineHeight: 1.4,
  },
  centerContact: {
    margin: "10px 0 0",
    fontSize: "13px",
    color: "#64748b",
    lineHeight: 1.45,
  },
};

export default FindCentersSection;
