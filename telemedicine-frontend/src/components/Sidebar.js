import React, { useState, useEffect, useCallback } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  DASHBOARD_HEADER_OFFSET_PX,
  SIDEBAR_WIDTH_COLLAPSED_PX,
  SIDEBAR_WIDTH_EXPANDED_PX,
} from "../constants/dashboardLayout";

import {
  BRAND_BLUE_MID,
  BRAND_NAVY,
} from "../constants/brandTheme";

const THEME = {
  bg: `linear-gradient(180deg, ${BRAND_NAVY} 0%, ${BRAND_BLUE_MID} 72%, #0d6e64 100%)`,
  active: "rgba(31, 118, 216, 0.95)",
  item: "rgba(255, 255, 255, 0.075)",
};

const Sidebar = ({ role, isCollapsed: controlledCollapsed, onToggle: controlledToggle }) => {
  const location = useLocation();
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== "undefined" ? window.innerWidth < 768 : false
  );
  const [localCollapsed, setLocalCollapsed] = useState(() =>
    typeof window !== "undefined" ? window.innerWidth < 768 : false
  );

  const controlled = controlledToggle != null && controlledCollapsed != null;
  const isCollapsed = controlled ? controlledCollapsed : localCollapsed;
  const onToggle = useCallback(() => {
    if (controlled) controlledToggle();
    else setLocalCollapsed((c) => !c);
  }, [controlled, controlledToggle]);

  useEffect(() => {
    const handleResize = () => {
      const m = window.innerWidth < 768;
      setIsMobile(m);
      if (window.innerWidth >= 768 && isCollapsed && !controlled) {
        setLocalCollapsed(false);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [isCollapsed, controlled]);

  const sidebarStyles = {
    ...styles.sidebar(THEME),
    width: isCollapsed
      ? isMobile
        ? "0"
        : `${SIDEBAR_WIDTH_COLLAPSED_PX}px`
      : isMobile
        ? "min(280px, 88vw)"
        : `${SIDEBAR_WIDTH_EXPANDED_PX}px`,
    transform: isMobile && isCollapsed ? "translateX(-100%)" : "translateX(0)",
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isMobile && !isCollapsed && <div style={styles.overlay} onClick={onToggle} aria-hidden="true" />}
      {isMobile && isCollapsed && (
        <button type="button" style={styles.peekTab} onClick={onToggle} aria-label="Open menu">
          Menu ☰
        </button>
      )}
      <aside style={sidebarStyles}>
        <div style={styles.header}>
          {!isCollapsed && <h3 style={styles.heading}>📋 Menu</h3>}
          <button 
            onClick={onToggle} 
            style={styles.toggleButton}
            aria-label={isCollapsed ? "Expand menu" : "Collapse menu"}
            onMouseEnter={(e) => e.target.style.backgroundColor = "rgba(255, 255, 255, 0.2)"}
            onMouseLeave={(e) => e.target.style.backgroundColor = "rgba(255, 255, 255, 0.1)"}
          >
            {isCollapsed ? "☰" : "✕"}
          </button>
        </div>
        
        <ul style={styles.menu}>
          {role === "patient" && (
            <>
              <li>
                <Link 
                  to="/dashboard/patient" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/dashboard/patient" ? styles.activeItem(THEME) : {}),
                  }}
                  title="Home"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "🏠" : "🏠 Home"}
                </Link>
              </li>
              <li>
                <Link 
                  to="/patient/profile" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/patient/profile" ? styles.activeItem(THEME) : {})
                  }}
                  title="View Profile"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "👤" : "👤 View Profile"}
                </Link>
              </li>
              <li>
                <Link 
                  to="/patient/change-password" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/patient/change-password" ? styles.activeItem(THEME) : {})
                  }}
                  title="Change Password"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "🔑" : "🔑 Change Password"}
                </Link>
              </li>
              <li>
                <Link 
                  to="/patient/book" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/patient/book" ? styles.activeItem(THEME) : {})
                  }}
                  title="Begin Consultation"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "📅" : "📅 Begin Consultation"}
                </Link>
              </li>
              <li>
                <Link 
                  to="/patient/history" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/patient/history" ? styles.activeItem(THEME) : {})
                  }}
                  title="Consultation History"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "📜" : "📜 Consultation History"}
                </Link>
              </li>
            </>
          )}
          {role === "doctor" && (
            <>
              <li>
                <Link 
                  to="/dashboard/doctor" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/dashboard/doctor" ? styles.activeItem(THEME) : {})
                  }}
                  title="Dashboard"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "🏠" : "🏠 Dashboard"}
                </Link>
              </li>
              <li>
                <Link 
                  to="/doctor/profile" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/doctor/profile" ? styles.activeItem(THEME) : {})
                  }}
                  title="Profile"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "👤" : "👤 Profile"}
                </Link>
              </li>
              <li>
                <Link 
                  to="/doctor/availability" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/doctor/availability" ? styles.activeItem(THEME) : {})
                  }}
                  title="Availability"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "⏰" : "⏰ Availability"}
                </Link>
              </li>
              <li>
                <Link 
                  to="/doctor/schedule" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/doctor/schedule" ? styles.activeItem(THEME) : {})
                  }}
                  title="Schedule"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "🗓" : "🗓 Schedule"}
                </Link>
              </li>
              <li>
                <Link 
                  to="/doctor/appointments" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/doctor/appointments" ? styles.activeItem(THEME) : {})
                  }}
                  title="Appointments"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "📅" : "📅 Appointments"}
                </Link>
              </li>
              <li>
                <Link 
                  to="/doctor/queue" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/doctor/queue" ? styles.activeItem(THEME) : {})
                  }}
                  title="Queue"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "📋" : "📋 Queue"}
                </Link>
              </li>
              <li>
                <Link 
                  to="/doctor/earnings" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/doctor/earnings" ? styles.activeItem(THEME) : {})
                  }}
                  title="Earnings"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "💰" : "💰 Earnings"}
                </Link>
              </li>
              <li>
                <Link 
                  to="/doctor/history" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/doctor/history" ? styles.activeItem(THEME) : {})
                  }}
                  title="Consultations History"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "📋" : "📋 Consultations History"}
                </Link>
              </li>
            </>
          )}
          {role === "tmc" && (
            <>
              <li>
                <Link 
                  to="/dashboard/tmc" 
                  style={{
                    ...styles.menuItem(THEME),
                    ...(location.pathname === "/dashboard/tmc" ? styles.activeItem(THEME) : {})
                  }}
                  title="TMC Dashboard"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "🏥" : "🏥 TMC Dashboard"}
                </Link>
              </li>
            </>
          )}
          {role === "admin" && (
            <>
              {[
                ["/dashboard/admin", "Operations"],
                ["/admin/fees", "Fees"],
                ["/admin/tmc-wallets", "TMC Wallets"],
                ["/admin/doctors", "Doctors"],
                ["/admin/patients", "Patients"],
                ["/admin/reports", "Reports"],
              ].map(([to, label]) => (
                <li key={to}>
                  <Link
                    to={to}
                    style={{
                      ...styles.menuItem(THEME),
                      ...(location.pathname === to ? styles.activeItem(THEME) : {}),
                    }}
                    title={label}
                    className="sidebar-menu-item"
                  >
                    {isCollapsed ? "•" : label}
                  </Link>
                </li>
              ))}
            </>
          )}
        </ul>
      </aside>
    </>
  );
};

const styles = {
  sidebar: (T) => ({
    background: T.bg,
    padding: "18px 12px",
    position: "fixed",
    top: DASHBOARD_HEADER_OFFSET_PX,
    left: 0,
    height: `calc(100vh - ${DASHBOARD_HEADER_OFFSET_PX}px)`,
    overflowY: "auto",
    boxShadow: "8px 0 28px rgba(0, 32, 67, 0.18)",
    transition: "width 0.25s ease, transform 0.25s ease",
    zIndex: 1000,
    overflowX: "hidden",
    boxSizing: "border-box",
  }),
  overlay: {
    position: "fixed",
    top: DASHBOARD_HEADER_OFFSET_PX,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0, 0, 0, 0.45)",
    zIndex: 999,
  },
  peekTab: {
    position: "fixed",
    left: 0,
    top: "50%",
    transform: "translateY(-50%)",
    zIndex: 1001,
    background: "#123a6f",
    color: "#fff",
    border: "none",
    borderRadius: "0 10px 10px 0",
    padding: "12px 8px 12px 4px",
    fontSize: 12,
    fontWeight: 700,
    cursor: "pointer",
    boxShadow: "2px 2px 8px rgba(0,0,0,0.2)",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px",
    paddingBottom: "15px",
    borderBottom: "1px solid rgba(255, 255, 255, 0.14)",
  },
  heading: {
    fontSize: "18px",
    fontWeight: "bold",
    color: "#fff",
    margin: 0,
  },
  toggleButton: {
    background: "rgba(255, 255, 255, 0.1)",
    border: "none",
    color: "#fff",
    fontSize: "20px",
    padding: "8px 12px",
    borderRadius: "10px",
    cursor: "pointer",
    transition: "all 0.2s ease",
  },
  toggleButtonHover: {
    background: "rgba(255, 255, 255, 0.2)",
  },
  menu: {
    listStyle: "none",
    padding: 0,
    margin: 0,
  },
  menuItem: (T) => ({
    display: "flex",
    alignItems: "center",
    padding: "11px 12px",
    color: "#e8f2ff",
    textDecoration: "none",
    borderRadius: "10px",
    marginBottom: "6px",
    backgroundColor: T.item,
    transition: "background 0.2s ease, transform 0.2s ease",
    whiteSpace: "nowrap",
    fontSize: "13px",
    fontWeight: 650,
    cursor: "pointer",
  }),
  activeItem: (T) => ({
    backgroundColor: T.active,
    color: "#fff",
    fontWeight: 700,
    boxShadow: "0 10px 22px rgba(23, 98, 191, 0.24)",
  }),
};

// Add hover effect via CSS-in-JS (applied dynamically)
const addHoverStyles = () => {
  if (typeof document === "undefined") return;
  
  const existingStyle = document.getElementById("sidebar-hover-styles");
  if (existingStyle) return;
  
  const style = document.createElement("style");
  style.id = "sidebar-hover-styles";
  style.textContent = `
    .sidebar-menu-item:hover {
      background-color: rgba(255, 255, 255, 0.15) !important;
      transform: translateX(5px);
    }
  `;
  document.head.appendChild(style);
};

if (typeof window !== "undefined") {
  addHoverStyles();
}

export default Sidebar;
