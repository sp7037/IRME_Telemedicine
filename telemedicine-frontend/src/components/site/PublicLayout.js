import React from "react";
import SiteHeader from "./SiteHeader";
import SiteFooter from "./SiteFooter";
import { DASHBOARD_PAGE_BG } from "../../constants/brandTheme";

/**
 * Standard shell for public marketing and auth pages (register/login).
 */
const PublicLayout = ({ children }) => (
  <div
    style={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      background: DASHBOARD_PAGE_BG,
      color: "#10243e",
      fontFamily: 'Segoe UI, system-ui, -apple-system, sans-serif',
    }}
  >
    <SiteHeader />
    {children}
    <SiteFooter />
  </div>
);

export default PublicLayout;
