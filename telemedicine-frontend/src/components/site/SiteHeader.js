import React, { useState, useEffect, useRef } from "react";
import { Link, NavLink } from "react-router-dom";
import { BRAND_LOGO_HORIZONTAL_WHITE } from "../../constants/brandAssets";
import LanguageSwitcher from "../LanguageSwitcher";
import {
  SITE_HEADER_NAVY,
  SITE_CTA_GREEN,
  BRAND_ACCENT,
} from "../../constants/brandTheme";

const MOBILE_BREAK = 960;

const navLinkStyle = {
  color: "#e8f4fc",
  textDecoration: "none",
  fontWeight: 600,
  fontSize: "14px",
  padding: "8px 4px",
};

const SiteHeader = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(
    typeof window !== "undefined" ? window.innerWidth < MOBILE_BREAK : false
  );
  const [openDrop, setOpenDrop] = useState(null);
  const deskRef = useRef(null);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < MOBILE_BREAK);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    const onDoc = (e) => {
      if (deskRef.current && !deskRef.current.contains(e.target)) {
        setOpenDrop(null);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  const closeMobile = () => setMobileOpen(false);

  const dropPanel = (items) => (
    <div
      style={{
        position: "absolute",
        top: "100%",
        right: 0,
        marginTop: "6px",
        minWidth: "260px",
        backgroundColor: "#ffffff",
        borderRadius: "12px",
        boxShadow: "0 12px 36px rgba(6, 43, 79, 0.18)",
        border: "1px solid #dbe7f3",
        padding: "8px 0",
        zIndex: 50,
      }}
    >
      {items.map(({ to, label }) => (
        <Link
          key={to + label}
          to={to}
          style={{
            display: "block",
            padding: "10px 18px",
            color: "#0f172a",
            textDecoration: "none",
            fontSize: "14px",
            fontWeight: 600,
          }}
          onClick={() => {
            setOpenDrop(null);
            closeMobile();
          }}
        >
          {label}
        </Link>
      ))}
    </div>
  );

  const loginItems = [
    { to: "/login", label: "Patient Login" },
    { to: "/login", label: "Doctor Login" },
    { to: "/login", label: "TMC Login" },
  ];

  const joinItems = [
    { to: "/join/doctor", label: "Join as Consultant Doctor" },
    { to: "/tmc", label: "Join as Telemedicine Center" },
    { to: "/telemedicine-course", label: "Telemedicine Course" },
  ];

  return (
    <header
      style={{
        backgroundColor: SITE_HEADER_NAVY,
        color: "#ffffff",
        borderBottom: `3px solid ${BRAND_ACCENT}`,
        position: "sticky",
        top: 0,
        zIndex: 40,
      }}
    >
      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "14px 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "16px",
        }}
      >
        <Link
          to="/"
          onClick={closeMobile}
          style={{ textDecoration: "none", color: "inherit" }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <img
              src={BRAND_LOGO_HORIZONTAL_WHITE}
              alt="IRME Telemedicine"
              width={isMobile ? "160" : "200"}
              height={isMobile ? "40" : "50"}
              style={{
                height: isMobile ? "40px" : "50px",
                width: "auto",
                maxWidth: "min(340px, 70vw)",
                objectFit: "contain",
                display: "block",
              }}
            />
            <span
              style={{
                fontSize: "11px",
                opacity: 0.92,
                maxWidth: "340px",
                lineHeight: 1.35,
              }}
            >
              Rural India Deserves Best Medical Health Services
            </span>
          </div>
        </Link>

        {!isMobile && (
          <div
            ref={deskRef}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px 14px",
              flexWrap: "wrap",
              justifyContent: "flex-end",
            }}
          >
            <NavLink
              to="/"
              end
              className="site-nav-ctl"
              style={({ isActive }) => ({
                ...navLinkStyle,
                borderBottom: isActive ? `2px solid ${SITE_CTA_GREEN}` : "2px solid transparent",
              })}
            >
              Home
            </NavLink>
            <NavLink
              to="/tmc"
              className="site-nav-ctl"
              style={({ isActive }) => ({
                ...navLinkStyle,
                borderBottom: isActive ? `2px solid ${SITE_CTA_GREEN}` : "2px solid transparent",
              })}
            >
              Open TMC
            </NavLink>
            <NavLink
              to="/telemedicine-course"
              className="site-nav-ctl"
              style={({ isActive }) => ({
                ...navLinkStyle,
                borderBottom: isActive ? `2px solid ${SITE_CTA_GREEN}` : "2px solid transparent",
              })}
            >
              Telemedicine Course
            </NavLink>

            <div style={{ position: "relative" }}>
              <button
                type="button"
                className="site-nav-ctl site-cta-ghost"
                onClick={() =>
                  setOpenDrop((v) => (v === "join" ? null : "join"))
                }
                style={{
                  background: "transparent",
                  border: "1px solid rgba(255,255,255,0.4)",
                  borderRadius: "8px",
                  color: "#fff",
                  fontWeight: 700,
                  fontSize: "13px",
                  padding: "8px 12px",
                  cursor: "pointer",
                }}
                aria-expanded={openDrop === "join"}
                aria-haspopup="true"
              >
                Join IRME ▾
              </button>
              {openDrop === "join" && dropPanel(joinItems)}
            </div>

            <div style={{ position: "relative" }}>
              <button
                type="button"
                className="site-nav-ctl site-cta-ghost"
                onClick={() =>
                  setOpenDrop((v) => (v === "login" ? null : "login"))
                }
                style={{
                  background: "transparent",
                  border: "1px solid rgba(255,255,255,0.4)",
                  borderRadius: "8px",
                  color: "#fff",
                  fontWeight: 700,
                  fontSize: "13px",
                  padding: "8px 12px",
                  cursor: "pointer",
                }}
                aria-expanded={openDrop === "login"}
                aria-haspopup="true"
              >
                Login ▾
              </button>
              {openDrop === "login" && dropPanel(loginItems)}
            </div>

            <LanguageSwitcher compact={true} style={{ marginLeft: "8px" }} />

            <Link
              to="/register/patient"
              className="site-cta-green"
              style={{
                marginLeft: "4px",
                backgroundColor: SITE_CTA_GREEN,
                color: "#052e16",
                fontWeight: 800,
                padding: "10px 16px",
                borderRadius: "10px",
                fontSize: "14px",
                textDecoration: "none",
              }}
            >
              Start Consultation
            </Link>
          </div>
        )}

        {isMobile && (
          <button
            type="button"
            className="site-burger"
            aria-label="Open menu"
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((o) => !o)}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
              {mobileOpen ? (
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
              ) : (
                <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" />
              )}
            </svg>
          </button>
        )}
      </div>

      {isMobile && mobileOpen && (
        <div
          style={{
            borderTop: "1px solid rgba(255,255,255,0.15)",
            padding: "12px 20px 20px",
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            maxHeight: "calc(100vh - 88px)",
            overflowY: "auto",
          }}
        >
          <Link
            to="/"
            onClick={closeMobile}
            style={{ ...navLinkStyle, padding: "12px 8px" }}
          >
            Home
          </Link>
          <Link
            to="/tmc"
            onClick={closeMobile}
            style={{ ...navLinkStyle, padding: "12px 8px" }}
          >
            Open Telemedicine Center
          </Link>
          <Link
            to="/telemedicine-course"
            onClick={closeMobile}
            style={{ ...navLinkStyle, padding: "12px 8px" }}
          >
            Telemedicine Course
          </Link>
          <Link
            to="/join-irme"
            onClick={closeMobile}
            style={{ ...navLinkStyle, padding: "12px 8px" }}
          >
            Join IRME — Overview
          </Link>

          <p
            style={{
              margin: "12px 0 4px",
              fontSize: "11px",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              opacity: 0.65,
            }}
          >
            Join IRME options
          </p>
          {joinItems.map((item) => (
            <Link
              key={item.to + item.label}
              to={item.to}
              onClick={closeMobile}
              style={{
                ...navLinkStyle,
                padding: "10px 8px 10px 16px",
                fontWeight: 500,
              }}
            >
              {item.label}
            </Link>
          ))}

          <p
            style={{
              margin: "12px 0 4px",
              fontSize: "11px",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              opacity: 0.65,
            }}
          >
            Login
          </p>
          {loginItems.map((item, i) => (
            <Link
              key={`${item.label}-${i}`}
              to={item.to}
              onClick={closeMobile}
              style={{
                ...navLinkStyle,
                padding: "10px 8px 10px 16px",
                fontWeight: 500,
              }}
            >
              {item.label}
            </Link>
          ))}

          <div style={{ padding: "12px 8px", marginTop: "8px" }}>
            <LanguageSwitcher />
          </div>

          <Link
            to="/register/patient"
            onClick={closeMobile}
            className="site-cta-green"
            style={{
              marginTop: "16px",
              textAlign: "center",
              backgroundColor: SITE_CTA_GREEN,
              color: "#052e16",
              fontWeight: 800,
              padding: "14px 16px",
              borderRadius: "10px",
              textDecoration: "none",
            }}
          >
            Start Consultation
          </Link>
        </div>
      )}
    </header>
  );
};

export default SiteHeader;
