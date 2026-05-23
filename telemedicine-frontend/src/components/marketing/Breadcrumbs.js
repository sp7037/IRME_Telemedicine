import React from "react";
import { Link } from "react-router-dom";
import { m } from "../../constants/marketingLayout";

const Breadcrumbs = ({ items }) => (
  <nav style={m.breadcrumb} aria-label="Breadcrumb">
    {items.map((it, i) => (
      <React.Fragment key={it.to || it.label}>
        {i > 0 && <span style={m.breadcrumbSep} aria-hidden>/</span>}
        {it.current ? (
          <span>{it.label}</span>
        ) : (
          <Link to={it.to} className="site-footer-link" style={{ color: "#1762bf" }}>
            {it.label}
          </Link>
        )}
      </React.Fragment>
    ))}
  </nav>
);

export default Breadcrumbs;
