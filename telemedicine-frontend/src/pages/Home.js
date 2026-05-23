import React from "react";
import PublicLayout from "../components/site/PublicLayout";
import FindCentersSection from "../components/marketing/FindCentersSection";
import HeroSection from "../components/home/HeroSection";
import MissionAlignmentSection from "../components/home/MissionAlignmentSection";
import TmcHighlightSection from "../components/home/TmcHighlightSection";
import HowItWorksSection from "../components/home/HowItWorksSection";
import JoinIrmeSection from "../components/home/JoinIrmeSection";
import ImpactSection from "../components/home/ImpactSection";
import FinalCtaSection from "../components/home/FinalCtaSection";

const Home = () => {
  return (
    <PublicLayout>
      <main
        style={{
          flex: 1,
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "24px 20px 48px",
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        <HeroSection />
        <MissionAlignmentSection />
        <TmcHighlightSection />
        <HowItWorksSection />
        <JoinIrmeSection />
        <ImpactSection />
        <FinalCtaSection />
        <FindCentersSection />
      </main>
    </PublicLayout>
  );
};

export default Home;
