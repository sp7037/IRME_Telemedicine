import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "../pages/Home";
import Login from "../pages/users/Login";
import ProtectedRoute from "../components/ProtectedRoute"; // ✅ Ensure Correct Path

// ✅ Fix Dashboard Imports
import PatientDashboard from "../pages/users/dashboards/PatientDashboard";
import DoctorDashboard from "../pages/users/dashboards/DoctorDashboard";
import TMCDashboard from "../pages/users/dashboards/TMCDashboard";

// ✅ Import Registration Pages
import RegisterPatient from "../pages/users/RegisterPatient";
import RegisterDoctor from "../pages/users/RegisterDoctor";
import RegisterTMC from "../pages/users/RegisterTMC";
import Logout from "../pages/users/Logout";

const AppRoutes = () => {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        
        {/* ✅ Ensure Registration Pages & logout routes */}
        <Route path="/register/patient" element={<RegisterPatient />} />
        <Route path="/register/doctor" element={<RegisterDoctor />} />
        <Route path="/register/tmc" element={<RegisterTMC />} />
        <Route path="/logout" element={<Logout />} />

        {/* ✅ Protected Routes */}
        <Route element={<ProtectedRoute allowedRoles={["patient"]} />}>
          <Route path="/dashboard/patient" element={<PatientDashboard />} />
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

        {/* 404 Page */}
        <Route path="*" element={<h1>404 Not Found</h1>} />
      </Routes>
    </Router>
  );
};

export default AppRoutes;
