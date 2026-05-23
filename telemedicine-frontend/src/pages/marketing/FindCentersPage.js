import React from "react";
import { Link } from "react-router-dom";
import PublicLayout from "../../components/site/PublicLayout";
import Breadcrumbs from "../../components/marketing/Breadcrumbs";
import FindCentersSection from "../../components/marketing/FindCentersSection";
import { m } from "../../constants/marketingLayout";
import { SITE_HEADER_NAVY } from "../../constants/brandTheme";

const main = {
  flex: 1,
  maxWidth: "1120px",
  margin: "0 auto",
  padding: "24px 20px 48px",
  width: "100%",
  boxSizing: "border-box",
};

const FindCentersPage = () => (
  <PublicLayout>
    <main style={main}>
      <Breadcrumbs
        items={[
          { label: "Home", to: "/" },
          { label: "Find Centers", current: true },
        ]}
      />
      <h1 style={{ ...m.h1, marginTop: 4 }}>Find Telemedicine Centers</h1>
      <p style={m.lead}>
        IRME Telemedicine Centers (TMCs) are local assisted points where patients can get help
        connecting with verified doctors online. Use the search below to find a center near you.
      </p>
      <FindCentersSection showIntro={false} />
      <p style={{ ...m.sectionBody, marginTop: "28px" }}>
        Want to start your own center?{" "}
        <Link to="/tmc" style={{ color: SITE_HEADER_NAVY, fontWeight: 700 }}>
          Learn how to become a Telemedicine Center
        </Link>
        .
      </p>
    </main>
  </PublicLayout>
);

export default FindCentersPage;
