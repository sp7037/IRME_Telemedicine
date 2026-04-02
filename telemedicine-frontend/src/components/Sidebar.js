import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";

const Sidebar = ({ role, isCollapsed, onToggle }) => {
  const location = useLocation();
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth >= 768 && isCollapsed) {
        onToggle(); // Auto-expand on desktop
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [isCollapsed, onToggle]);

  const sidebarStyles = {
    ...styles.sidebar,
    width: isCollapsed ? (isMobile ? "0" : "70px") : (isMobile ? "280px" : "250px"),
    transform: isMobile && isCollapsed ? "translateX(-100%)" : "translateX(0)",
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isMobile && !isCollapsed && (
        <div style={styles.overlay} onClick={onToggle} />
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
                    ...styles.menuItem,
                    ...(location.pathname === "/dashboard/patient" ? styles.activeItem : {})
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
                    ...styles.menuItem,
                    ...(location.pathname === "/patient/profile" ? styles.activeItem : {})
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
                    ...styles.menuItem,
                    ...(location.pathname === "/patient/change-password" ? styles.activeItem : {})
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
                    ...styles.menuItem,
                    ...(location.pathname === "/patient/book" ? styles.activeItem : {})
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
                    ...styles.menuItem,
                    ...(location.pathname === "/patient/history" ? styles.activeItem : {})
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
                    ...styles.menuItem,
                    ...(location.pathname === "/dashboard/doctor" ? styles.activeItem : {})
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
                    ...styles.menuItem,
                    ...(location.pathname === "/doctor/profile" ? styles.activeItem : {})
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
                    ...styles.menuItem,
                    ...(location.pathname === "/doctor/availability" ? styles.activeItem : {})
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
                    ...styles.menuItem,
                    ...(location.pathname === "/doctor/schedule" ? styles.activeItem : {})
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
                    ...styles.menuItem,
                    ...(location.pathname === "/doctor/appointments" ? styles.activeItem : {})
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
                    ...styles.menuItem,
                    ...(location.pathname === "/doctor/queue" ? styles.activeItem : {})
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
                    ...styles.menuItem,
                    ...(location.pathname === "/doctor/earnings" ? styles.activeItem : {})
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
                    ...styles.menuItem,
                    ...(location.pathname === "/doctor/history" ? styles.activeItem : {})
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
                    ...styles.menuItem,
                    ...(location.pathname === "/dashboard/tmc" ? styles.activeItem : {})
                  }}
                  title="TMC Dashboard"
                  className="sidebar-menu-item"
                >
                  {isCollapsed ? "🏥" : "🏥 TMC Dashboard"}
                </Link>
              </li>
            </>
          )}
        </ul>
      </aside>
    </>
  );
};

const styles = {
  sidebar: {
    background: "linear-gradient(180deg, #2c3e50 0%, #34495e 100%)",
    padding: "20px 15px",
    position: "fixed",
    top: "60px",
    left: 0,
    height: "calc(100vh - 60px)",
    overflowY: "auto",
    boxShadow: "2px 0 10px rgba(0,0,0,0.2)",
    transition: "all 0.3s ease-in-out",
    zIndex: 1000,
    overflowX: "hidden",
  },
  overlay: {
    position: "fixed",
    top: "60px",
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    zIndex: 999,
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px",
    paddingBottom: "15px",
    borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
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
    borderRadius: "5px",
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
  menuItem: {
    display: "flex",
    alignItems: "center",
    padding: "12px 15px",
    color: "#ecf0f1",
    textDecoration: "none",
    borderRadius: "8px",
    marginBottom: "8px",
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    transition: "all 0.2s ease",
    whiteSpace: "nowrap",
    fontSize: "14px",
    cursor: "pointer",
  },
  activeItem: {
    backgroundColor: "#3498db",
    color: "#fff",
    fontWeight: "bold",
  },
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
