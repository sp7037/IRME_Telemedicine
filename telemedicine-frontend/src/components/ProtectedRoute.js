import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import {
  clearAuthSession,
  getAccessToken,
  getDoctorOnboarding,
  getUserType,
  isJwtExpired,
} from "../utils/authSession";

const ProtectedRoute = ({ allowedRoles }) => {
  const token = getAccessToken();
  const userType = getUserType();
  const location = useLocation();
  const loginWithReturn = `/login?next=${encodeURIComponent(`${location.pathname}${location.search || ""}`)}`;

  if (!token || isJwtExpired(token)) {
    clearAuthSession();
    return <Navigate to={loginWithReturn} replace />;
  }

  if (!allowedRoles.includes(userType)) {
    return <Navigate to={loginWithReturn} replace />;
  }

  if (userType === "doctor") {
    const onboarding = getDoctorOnboarding();
    if (onboarding.next_step === "COMPLETE_PROFILE" && location.pathname !== "/doctor/profile") {
      return <Navigate to="/doctor/profile" replace />;
    }
  }

  return <Outlet />;
};

export default ProtectedRoute;
