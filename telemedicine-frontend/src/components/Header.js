import React, { useMemo, useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { BRAND_HORIZONTAL_LOGO_PNG } from "../constants/brandAssets";
import { DASHBOARD_HEADER_OFFSET_PX } from "../constants/dashboardLayout";
import { getUserType } from "../utils/authSession";

import {
  BRAND_BLUE_MID,
  BRAND_BLUE_BRIGHT,
  BRAND_NAVY,
} from "../constants/brandTheme";

const THEME = {
  bg: `linear-gradient(90deg, ${BRAND_NAVY} 0%, ${BRAND_BLUE_MID} 55%, ${BRAND_BLUE_BRIGHT} 100%)`,
  text: "#ffffff",
  accent: "#9ec9ff",
};

/**
 * Dashboard header: links follow the current authenticated role (patient | doctor | tmc | admin).
 * Optional `role` prop overrides when storage is wrong.
 */
const Header = ({ role: roleProp, balance, onBalanceClick }) => {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [winW, setWinW] = useState(typeof window !== "undefined" ? window.innerWidth : 1024);

  useEffect(() => {
    const onR = () => setWinW(window.innerWidth);
    window.addEventListener("resize", onR);
    return () => window.removeEventListener("resize", onR);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const role = roleProp || getUserType() || "patient";

  const links = useMemo(() => {
    if (role === "doctor") {
      return [
        { to: "/dashboard/doctor", label: "Operations" },
        { to: "/doctor/profile", label: "Profile" },
        { to: "/doctor/availability", label: "Availability" },
        { to: "/doctor/schedule", label: "Schedule" },
        { to: "/doctor/appointments", label: "Appointments" },
        { to: "/doctor/queue", label: "Queue" },
        { to: "/doctor/earnings", label: "Earnings" },
        { to: "/doctor/history", label: "History" },
      ];
    }
    if (role === "tmc") {
      return [{ to: "/dashboard/tmc", label: "TMC dashboard" }];
    }
    if (role === "admin") {
      return [
        { to: "/dashboard/admin", label: "Operations" },
        { to: "/admin/fees", label: "Fees" },
        { to: "/admin/tmc-wallets", label: "TMC wallets" },
        { to: "/admin/doctors", label: "Doctors" },
        { to: "/admin/patients", label: "Patients" },
        { to: "/admin/reports", label: "Reports" },
      ];
    }
    return [
      { to: "/dashboard/patient", label: "Dashboard" },
      { to: "/patient/profile", label: "Profile" },
      { to: "/patient/book", label: "Book" },
      { to: "/patient/history", label: "History" },
    ];
  }, [role]);

  const profileHref =
    role === "doctor" ? "/doctor/profile" : role === "tmc" ? "/dashboard/tmc" : role === "admin" ? "/dashboard/admin" : "/patient/profile";
  const dashboardHref =
    role === "doctor" ? "/dashboard/doctor" : role === "tmc" ? "/dashboard/tmc" : role === "admin" ? "/dashboard/admin" : "/dashboard/patient";

  const isActive = (to) => location.pathname === to || (to !== "/" && location.pathname.startsWith(to + "/"));

  const compact = winW < 900;

  return (
    <header style={styles.header(THEME)}>
      <div style={styles.headerInner}>
        <Link to="/" style={styles.logo}>
          <img src={BRAND_HORIZONTAL_LOGO_PNG} alt="IRME Telemedicine" style={styles.logoImg} />
        </Link>
        {!compact ? (
          <nav style={styles.nav} aria-label="Main">
            {links.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                style={{
                  ...styles.navLink(THEME),
                  ...(isActive(l.to) ? styles.navLinkActive : {}),
                }}
              >
                {l.label}
              </Link>
            ))}
          </nav>
        ) : null}
        <div style={styles.right}>
          {onBalanceClick ? <button type="button" style={styles.profileBtn(THEME)} onClick={onBalanceClick}
            aria-label={`Balance ${balance ?? "loading"} rupees, add funds and payment history`}>◉ ₹{balance ?? "…"}</button> : null}
          {!compact ? (
            <>
              <Link to={profileHref} style={styles.profileBtn(THEME)}>
                Profile
              </Link>
              <Link to="/logout" style={styles.logout}>
                Logout
              </Link>
            </>
          ) : null}
          <button
            type="button"
            style={styles.menuBtn}
            aria-expanded={mobileOpen}
            aria-label="Menu"
            onClick={() => setMobileOpen((o) => !o)}
          >
            {mobileOpen ? "✕" : "☰"}
          </button>
        </div>
      </div>
      {compact && mobileOpen ? (
        <nav style={styles.mobileNav} aria-label="Mobile main">
          {links.map((l) => (
            <Link key={l.to} to={l.to} style={styles.mobileLink}>
              {l.label}
            </Link>
          ))}
          <Link to={dashboardHref} style={styles.mobileLink}>
            Home dashboard
          </Link>
          <Link to={profileHref} style={styles.mobileLink}>
            Profile
          </Link>
          <Link to="/logout" style={styles.mobileLinkLogout}>
            Logout
          </Link>
        </nav>
      ) : null}
    </header>
  );
};

const styles = {
  header: (T) => ({
    background: T.bg,
    color: T.text,
    position: "sticky",
    top: 0,
    left: 0,
    width: "100%",
    zIndex: 1100,
    boxShadow: "0 2px 12px rgba(11, 43, 85, 0.25)",
    minHeight: DASHBOARD_HEADER_OFFSET_PX,
    boxSizing: "border-box",
  }),
  headerInner: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    padding: "12px 16px",
    flexWrap: "wrap",
    maxWidth: 1400,
    margin: "0 auto",
  },
  logo: {
    textDecoration: "none",
    color: "#fff",
    display: "inline-flex",
    alignItems: "center",
    minWidth: 0,
  },
  logoImg: {
    height: 34,
    width: "auto",
    maxWidth: 220,
    objectFit: "contain",
    display: "block",
  },
  nav: {
    display: "flex",
    flexWrap: "wrap",
    gap: 6,
    alignItems: "center",
    justifyContent: "center",
    flex: 1,
  },
  navLink: (T) => ({
    color: T.accent,
    textDecoration: "none",
    padding: "8px 12px",
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 600,
  }),
  navLinkActive: {
    background: "rgba(255,255,255,0.15)",
    color: "#fff",
  },
  right: { display: "flex", alignItems: "center", gap: 8 },
  profileBtn: (T) => ({
    color: "#fff",
    textDecoration: "none",
    padding: "8px 14px",
    borderRadius: 8,
    border: "1px solid rgba(255,255,255,0.35)",
    fontSize: 14,
    fontWeight: 600,
  }),
  logout: {
    background: "rgba(220, 53, 69, 0.95)",
    color: "#fff",
    padding: "8px 14px",
    borderRadius: 8,
    textDecoration: "none",
    fontSize: 14,
    fontWeight: 700,
  },
  menuBtn: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    width: 44,
    height: 40,
    borderRadius: 8,
    border: "1px solid rgba(255,255,255,0.35)",
    background: "rgba(255,255,255,0.1)",
    color: "#fff",
    fontSize: 20,
    cursor: "pointer",
  },
  mobileNav: {
    display: "flex",
    flexDirection: "column",
    padding: "0 16px 16px",
    gap: 4,
    borderTop: "1px solid rgba(255,255,255,0.15)",
  },
  mobileLink: {
    color: "#e8f2ff",
    textDecoration: "none",
    padding: "12px 8px",
    borderRadius: 8,
    fontWeight: 600,
    fontSize: 15,
  },
  mobileLinkLogout: {
    color: "#ffc9c9",
    textDecoration: "none",
    padding: "12px 8px",
    marginTop: 8,
    fontWeight: 700,
  },
};

export default Header;
