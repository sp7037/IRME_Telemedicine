import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "../pages/Home";
import Login from "../pages/users/Login";
import ProtectedRoute from "../components/ProtectedRoute";

import PatientDashboard from "../pages/users/dashboards/PatientDashboard";
import DoctorDashboard from "../pages/users/dashboards/DoctorDashboard";
import TMCDashboard from "../pages/users/dashboards/TMCDashboard";
import AdminDashboard from "../pages/users/dashboards/AdminDashboard";

import RegisterPatientNew from "../pages/users/RegisterPatientNew";
import RegisterDoctor from "../pages/users/RegisterDoctor";
import RegisterTMC from "../pages/users/RegisterTMC";
import VerifyDoctorEmail from "../pages/users/VerifyDoctorEmail";
import Logout from "../pages/users/Logout";

import JoinIRMEPage from "../pages/marketing/JoinIRMEPage";
import BecomeTMCPage from "../pages/marketing/BecomeTMCPage";
import JoinDoctorPage from "../pages/marketing/JoinDoctorPage";
import TelemedicineCoursePage from "../pages/marketing/TelemedicineCoursePage";
import MarketingLocationPage from "../pages/marketing/MarketingLocationPage";
import NotFoundPage from "../pages/NotFoundPage";

const AppRoutes = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/join/doctor" element={<JoinDoctorPage />} />
        <Route path="/tmc" element={<BecomeTMCPage />} />
        <Route path="/join-irme" element={<JoinIRMEPage />} />
        <Route path="/telemedicine-centers/join" element={<BecomeTMCPage />} />
        <Route path="/telemedicine-center/:stateSlug" element={<MarketingLocationPage type="tmc" />} />
        <Route path="/telemedicine-center/:stateSlug/:citySlug" element={<MarketingLocationPage type="tmc" />} />
        <Route path="/doctors/join" element={<JoinDoctorPage />} />
        <Route path="/telemedicine-course" element={<TelemedicineCoursePage />} />
        <Route path="/telemedicine-assistant-course/:stateSlug" element={<MarketingLocationPage type="course" />} />
        <Route path="/telemedicine-assistant-course/:stateSlug/:citySlug" element={<MarketingLocationPage type="course" />} />

        <Route path="/login" element={<Login />} />
        <Route path="/verify-email" element={<VerifyDoctorEmail />} />
        <Route path="/verify-doctor-email" element={<VerifyDoctorEmail />} />

        <Route path="/register/patient" element={<RegisterPatientNew />} />
        <Route path="/register/doctor" element={<RegisterDoctor />} />
        <Route path="/register/tmc" element={<RegisterTMC />} />
        <Route path="/logout" element={<Logout />} />

        <Route element={<ProtectedRoute allowedRoles={["patient"]} />}>
          <Route path="/dashboard/patient" element={<PatientDashboard />} />
          <Route path="/patient/profile" element={<PatientDashboard />} />
          <Route path="/patient/book" element={<PatientDashboard />} />
          <Route path="/patient/history" element={<PatientDashboard />} />
          <Route path="/patient/change-password" element={<PatientDashboard />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={["doctor"]} />}>
          <Route path="/dashboard/doctor" element={<DoctorDashboard />} />
          <Route path="/doctor/profile" element={<DoctorDashboard />} />
          <Route path="/doctor/availability" element={<DoctorDashboard />} />
          <Route path="/doctor/appointments" element={<DoctorDashboard />} />
          <Route path="/doctor/queue" element={<DoctorDashboard />} />
          <Route path="/doctor/schedule" element={<DoctorDashboard />} />
          <Route path="/doctor/earnings" element={<DoctorDashboard />} />
          <Route path="/doctor/history" element={<DoctorDashboard />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={["tmc"]} />}>
          <Route path="/dashboard/tmc" element={<TMCDashboard />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
          <Route path="/dashboard/admin" element={<AdminDashboard />} />
          <Route path="/admin/fees" element={<AdminDashboard />} />
          <Route path="/admin/tmc-wallets" element={<AdminDashboard />} />
          <Route path="/admin/doctors" element={<AdminDashboard />} />
          <Route path="/admin/patients" element={<AdminDashboard />} />
          <Route path="/admin/reports" element={<AdminDashboard />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Router>
  );
};

export default AppRoutes;
