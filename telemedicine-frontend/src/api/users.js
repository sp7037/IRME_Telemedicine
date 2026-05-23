import axios from "axios";
import { API_BASE_URL } from "./config";
import {
  clearAuthSession,
  getAccessToken,
  getRefreshToken,
  setAuthItem,
} from "../utils/authSession";

// ✅ Login API Call (Using `axios` for consistency)
export const loginUser = async (email, password) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/users/login/`, {
      email,
      password,
    });

    return response.data;  // ✅ Return only the necessary data
  } catch (error) {
    console.error("Login Error:", error.response?.data || error.message);

    const responseData = error.response?.data;
    if (responseData?.next_step === "VERIFY_EMAIL") {
      const err = new Error(responseData.error?.message || "Please verify your email before signing in.");
      err.code = responseData.error?.code || "EMAIL_NOT_VERIFIED";
      err.nextStep = responseData.next_step;
      err.email = responseData.email;
      throw err;
    }

    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    }

    throw new Error("❌ Unable to login. Please check your credentials.");
  }
};

// ✅ Register API Call
export const registerUser = async (userData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/users/register/`, userData);
    return response.data;
  } catch (error) {
    console.error("Registration Error:", error.response?.data || error.message);
    const err = new Error(
      error.response?.data?.detail ||
        error.response?.data?.error?.non_field_errors?.[0] ||
        "Registration failed."
    );
    err.fieldErrors = error.response?.data?.error;
    throw err;
  }
};

// ✅ Function to Logout User
export const verifyRegistrationEmail = async ({ email, otp }) => {
  const response = await axios.post(`${API_BASE_URL}/users/verify-email/`, { email, otp });
  return response.data;
};

export const resendRegistrationEmailOTP = async (email) => {
  const response = await axios.post(`${API_BASE_URL}/users/resend-email-otp/`, { email });
  return response.data;
};

/** @deprecated Use verifyRegistrationEmail — kept for older imports */
export const verifyDoctorEmail = verifyRegistrationEmail;
/** @deprecated Use resendRegistrationEmailOTP */
export const resendDoctorEmailOTP = resendRegistrationEmailOTP;

export const logoutUser = () => {
  clearAuthSession();
  window.location.href = "/login"; // Redirect after logout
};

// Refresh token (plain axios — must not use apiClient to avoid interceptor loops)
export const refreshToken = async () => {
  const refresh_token = getRefreshToken();

  if (!refresh_token) {
    throw new Error("No refresh token available. Please log in again.");
  }

  try {
    const response = await axios.post(`${API_BASE_URL}/users/token/refresh/`, {
      refresh: refresh_token,
    });

    const access = response.data?.access?.trim();
    if (!access) {
      throw new Error("No access token in refresh response.");
    }
    setAuthItem("token", access);
    return access;
  } catch (error) {
    console.error("Token Refresh Error:", error.response?.data || error.message);
    throw new Error("Session expired. Please log in again.");
  }
};

function isTokenRefreshRequest(config) {
  const path = `${config?.baseURL || ""}${config?.url || ""}`;
  return path.includes("/users/token/refresh");
}

/** Consultation history returns `[]` or `{ message }` when empty. */
function normalizeConsultationHistoryPayload(data) {
  if (Array.isArray(data)) return data;
  if (data && typeof data === "object" && "message" in data && !Array.isArray(data)) return [];
  return [];
}

// Authenticated API client: attaches JWT and refreshes on 401
const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      delete config.headers.Authorization;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      isTokenRefreshRequest(originalRequest)
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;
    console.warn("🔄 401 from API, attempting token refresh…");
    try {
      const newToken = await refreshToken();
      originalRequest.headers.Authorization = `Bearer ${newToken}`;
      return apiClient.request(originalRequest);
    } catch (refreshErr) {
      console.error("🔴 Token refresh failed. Logging out…", refreshErr);
      logoutUser();
      return Promise.reject(new Error("Session expired. Please log in again."));
    }
  }
);

// ✅ Function to Get User Profile (uses apiClient for refresh-on-401)
export const getUserProfile = async () => {
  try {
    if (!getAccessToken()) {
      throw new Error("⚠ No authentication token found. Please log in again.");
    }
    const response = await apiClient.get("/users/profile/");
    console.log("✅ API Response:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Profile Fetch Error:", error.response?.data || error.message);
    const errorMessage =
      error.response?.data?.detail ||
      error.response?.data?.error ||
      error.message ||
      "Failed to fetch profile.";
    throw new Error(errorMessage);
  }
};

/** PATCH `/users/profile/` — updates `user` fields and role-specific `profile` in one request. */
export const patchUserProfile = async (payload) => {
  try {
    if (!getAccessToken()) {
      throw new Error("⚠ No authentication token found. Please log in again.");
    }
    const response = await apiClient.patch("/users/profile/", payload);
    return response.data;
  } catch (error) {
    console.error("❌ Profile update error:", error.response?.data || error.message);
    const d = error.response?.data;
    const msg =
      (typeof d?.error === "string" && d.error) ||
      d?.detail ||
      (d?.error && typeof d?.error === "object" && JSON.stringify(d.error)) ||
      error.message ||
      "Failed to update profile.";
    throw new Error(msg);
  }
};


// Patient consultation history
export const getPatientConsultationHistory = async () => {
  try {
    const response = await apiClient.get("/consultations/history/");
    console.log("✅ Consultation History:", response.data);
    return normalizeConsultationHistoryPayload(response.data);
  } catch (error) {
    console.error("❌ Consultation History Fetch Error:", error.response?.data || error.message);
    const detail = error.response?.data?.detail || error.response?.data?.message;
    throw new Error(detail || "Failed to fetch consultation history.");
  }
};

// ✅ Get Pending Consultation Requests for Doctor
export const getDoctorPendingRequests = async () => {
  try {
    const response = await apiClient.get("/consultations/doctor/pending-requests/");
    console.log("✅ Pending Requests:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Pending Requests Fetch Error:", error.response?.data || error.message);
    const detail = error.response?.data?.detail || error.response?.data?.message;
    throw new Error(detail || "Failed to fetch pending requests.");
  }
};

// ✅ Doctor Response to Consultation Request
export const doctorRespondToRequest = async (consultationId, action, newSuggestedTime = null) => {
  try {
    const data = { status: action };
    if (action === "POSTPONED" && newSuggestedTime) {
      data.new_suggested_time = newSuggestedTime;
    }

    const response = await apiClient.patch(`/consultations/doctor-response/${consultationId}/`, data);

    console.log("✅ Doctor Response:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Doctor Response Error:", error.response?.data || error.message);
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        "Failed to process request.";
    throw new Error(errorMessage);
  }
};

// ✅ Doctor Profile Completion API Functions
export const lookupPincode = async (pincode) => {
  const response = await apiClient.get("/users/pincode-lookup/", {
    params: { pincode: String(pincode).trim() },
  });
  return response.data;
};

export const getDoctorProfile = async () => {
  try {
    const response = await apiClient.get("/consultations/doctor/profile/");

    // Handle response - could be direct profile data or wrapped in a profile key
    const data = response.data;
    if (data.profile) {
      return data.profile;
    }
    return data;
  } catch (error) {
    console.error("❌ Doctor Profile Fetch Error:", error.response?.data || error.message);
    
    // Handle 404 or 400 errors gracefully (profile doesn't exist yet)
    if (error.response?.status === 404 || error.response?.status === 400) {
      console.log("Profile doesn't exist yet - this is normal for new doctors");
      return null; // Return null instead of throwing error
    }
    
    // For other errors, throw with detailed message
    const errorMessage = error.response?.data?.detail || 
                        error.response?.data?.error || 
                        error.message || 
                        "Failed to fetch doctor profile.";
    throw new Error(errorMessage);
  }
};

export const updateDoctorProfile = async (profileData) => {
  try {
    const formData = new FormData();
    const fields = [
      "qualification", "degree", "college_university_name", "passing_year", "specialty",
      "experience", "license_number", "registration_number", "state_medical_council",
      "major_diseases_specializations", "previous_hospitals_served", "hospital_or_clinic_name",
      "clinic_address_street", "city", "state", "pin_code", "consultation_fee",
      "max_daily_consultations"
    ];
    fields.forEach((field) => {
      const value = profileData[field];
      if (value !== undefined && value !== null && String(value).trim() !== "") {
        formData.append(field, field === "license_number" ? String(value).trim().toUpperCase() : String(value).trim());
      }
    });
    (profileData.consultation_modes || []).forEach((mode) => formData.append("consultation_modes", mode));
    
    // Add file fields - only if they are File objects
    if (profileData.photo instanceof File) {
      formData.append('photo', profileData.photo);
    }
    if (profileData.identity_proof instanceof File) {
      formData.append('identity_proof', profileData.identity_proof);
    }
    if (profileData.registration_certificate instanceof File) {
      formData.append('registration_certificate', profileData.registration_certificate);
    }

    // Let the browser set multipart boundary — do not set Content-Type manually
    const response = await apiClient.patch("/consultations/doctor/profile/", formData, {
      timeout: 180000,
    });

    return response.data;
  } catch (error) {
    console.error("❌ Doctor Profile Update Error:", error.response?.data || error.message);
    
    // Create a more detailed error message
    if (error.response?.data?.error) {
      const errorData = error.response.data.error;
      let errorMessage = "Validation errors:\n";
      
      if (typeof errorData === 'object') {
        Object.keys(errorData).forEach(key => {
          errorMessage += `${key}: ${Array.isArray(errorData[key]) ? errorData[key].join(', ') : errorData[key]}\n`;
        });
      } else {
        errorMessage = errorData;
      }
      
      const detailedError = new Error(errorMessage);
      detailedError.response = error.response;
      throw detailedError;
    }
    
    throw error;
  }
};

// ✅ Doctor Availability API Functions
export const getDoctorAvailability = async () => {
  try {
    const response = await apiClient.get("/consultations/doctor/availability/");
    return response.data;
  } catch (error) {
    console.error("❌ Doctor Availability Fetch Error:", error.response?.data || error.message);
    const detail = error.response?.data?.detail || error.response?.data?.message;
    throw new Error(detail || "Failed to fetch doctor availability.");
  }
};

export const updateDoctorAvailability = async (availabilityData) => {
  try {
    // Sanitize payload for DRF DateTimeField:
    // send `null` instead of empty string to avoid 400 validation errors.
    const payload = {
      ...availabilityData,
      next_available_online: availabilityData.next_available_online || null,
      next_available_in_clinic: availabilityData.next_available_in_clinic || null,
    };

    // If doctor is available now, clear "next available" fields.
    if (payload.is_available_online) {
      payload.next_available_online = null;
    }
    if (payload.is_available_in_clinic) {
      payload.next_available_in_clinic = null;
    }

    let response;
    try {
      response = await apiClient.patch("/consultations/doctor/availability/", payload);
    } catch (error) {
      // If availability row doesn't exist yet, create then update.
      if (error.response?.status === 404) {
        await apiClient.post("/consultations/doctor/availability/create/", payload);
        response = await apiClient.patch("/consultations/doctor/availability/", payload);
      } else {
        throw error;
      }
    }

    return response.data;
  } catch (error) {
    console.error("❌ Doctor Availability Update Error:", error.response?.data || error.message);
    throw error;
  }
};

// ✅ Doctor Schedule API Functions
export const getDoctorSchedules = async () => {
  try {
    const response = await apiClient.get("/consultations/doctor/schedule/");
    return response.data;
  } catch (error) {
    console.error("❌ Doctor Schedule Fetch Error:", error.response?.data || error.message);
    const detail = error.response?.data?.detail || error.response?.data?.message;
    throw new Error(detail || "Failed to fetch doctor schedules.");
  }
};

export const createDoctorSchedule = async (scheduleData) => {
  try {
    const response = await apiClient.post("/consultations/doctor/schedule/", scheduleData);

    return response.data;
  } catch (error) {
    console.error("❌ Doctor Schedule Create Error:", error.response?.data || error.message);
    throw error;
  }
};

export const updateDoctorSchedule = async (scheduleId, scheduleData) => {
  const response = await apiClient.patch(`/consultations/doctor/schedule/${scheduleId}/`, scheduleData);
  return response.data;
};

export const deleteDoctorSchedule = async (scheduleId) => {
  const response = await apiClient.delete(`/consultations/doctor/schedule/${scheduleId}/`);
  return response.data;
};

// ✅ Patient Response to Consultation (Approve/Reject Postponed, Cancel)
export const patientRespondToConsultation = async (consultationId, action) => {
  try {
    const response = await apiClient.patch(`/consultations/patient-response/${consultationId}/`, {
      action,
    });

    console.log("✅ Patient Response:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Patient Response Error:", error.response?.data || error.message);
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        "Failed to process request.";
    throw new Error(errorMessage);
  }
};

// ✅ Get Queued Consultations for Doctor
export const getDoctorQueuedConsultations = async () => {
  try {
    const response = await apiClient.get("/consultations/doctor/queued-consultations/");

    console.log("✅ Queued Consultations:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Queued Consultations Fetch Error:", error.response?.data || error.message);
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        "Failed to fetch queued consultations.";
    throw new Error(errorMessage);
  }
};

// ✅ Start Consultation (Change to IN_PROGRESS)
export const startConsultation = async (consultationId) => {
  try {
    const response = await apiClient.post(`/consultations/start-consultation/${consultationId}/`, {});

    console.log("✅ Consultation Started:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Start Consultation Error:", error.response?.data || error.message);
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        "Failed to start consultation.";
    throw new Error(errorMessage);
  }
};

// ✅ Complete Consultation
export const completeConsultation = async (consultationId) => {
  try {
    const response = await apiClient.post(`/consultations/complete-consultation/${consultationId}/`, {});

    console.log("✅ Consultation Completed:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Complete Consultation Error:", error.response?.data || error.message);
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        "Failed to complete consultation.";
    throw new Error(errorMessage);
  }
};

export const requestConsultationFollowUp = async (consultationId) => {
  try {
    const response = await apiClient.post(`/consultations/followups/request/${consultationId}/`, {});
    return response.data;
  } catch (error) {
    const data = error.response?.data;
    const errorMessage =
      data?.wallet ||
      data?.error ||
      data?.message ||
      error.message ||
      "Failed to request follow-up.";
    throw new Error(errorMessage);
  }
};

export const doctorRespondToFollowUp = async (followUpSessionId, action = "ACCEPTED") => {
  try {
    const response = await apiClient.post(`/consultations/followups/${followUpSessionId}/doctor-response/`, {
      action,
    });
    return response.data;
  } catch (error) {
    const data = error.response?.data;
    const errorMessage = data?.error || data?.message || error.message || "Failed to respond to follow-up.";
    throw new Error(errorMessage);
  }
};

// ✅ Get Active Consultation
export const getActiveConsultation = async () => {
  try {
    const response = await apiClient.get("/consultations/active-consultation/");

    console.log("✅ Active Consultation Response:", response.data);
    
    // Check if response contains a message field (no active consultation)
    if (response.data && response.data.message) {
      console.log("ℹ️ No active consultation found");
      return null;
    }
    
    // Return the consultation data
    return response.data;
  } catch (error) {
    console.error("❌ Active Consultation Fetch Error:", error.response?.data || error.message);
    // Return null for any errors (no active consultation)
    return null;
  }
};

// ✅ Get Chat History
export const getChatHistory = async (consultationId) => {
  try {
    const response = await apiClient.get(`/consultations/chat-history/${consultationId}/`);

    console.log("✅ Chat History:", response.data);
    return response.data.chat_history || [];
  } catch (error) {
    console.error("❌ Chat History Fetch Error:", error.response?.data || error.message);
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        "Failed to fetch chat history.";
    throw new Error(errorMessage);
  }
};

// ✅ Send Message (with optional file attachment)
export const sendMessage = async (consultationId, message, file = null) => {
  try {
    let data;
    if (file) {
      const formData = new FormData();
      if (message) {
        formData.append("message", message);
      }
      formData.append("attachment", file);
      data = formData;
    } else {
      data = { message: message };
    }

    const response = await apiClient.post(`/consultations/send-message/${consultationId}/`, data);

    console.log("✅ Message Sent:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Send Message Error:", error.response?.data || error.message);
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        "Failed to send message.";
    throw new Error(errorMessage);
  }
};

// ✅ Create Prescription
export const createPrescription = async (consultationId, medicines, instructions) => {
  try {
    const response = await apiClient.post(`/consultations/prescription/${consultationId}/`, {
      medicines: medicines,
      instructions: instructions || "Take medicines as prescribed. Follow up if symptoms persist.",
    });

    console.log("✅ Prescription Created:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Prescription Creation Error:", error.response?.data || error.message);
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        "Failed to create prescription.";
    throw new Error(errorMessage);
  }
};

// ✅ Get Prescription
export const getPrescription = async (consultationId) => {
  try {
    const response = await apiClient.get(`/consultations/prescription/${consultationId}/`);

    console.log("✅ Prescription:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Prescription Fetch Error:", error.response?.data || error.message);
    if (error.response?.status === 404) {
      return null; // No prescription found
    }
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        "Failed to fetch prescription.";
    throw new Error(errorMessage);
  }
};

// ✅ Update Prescription
export const updatePrescription = async (consultationId, medicines, instructions) => {
  try {
    const response = await apiClient.put(`/consultations/prescription/${consultationId}/`, {
      medicines: medicines,
      instructions: instructions || "Take medicines as prescribed. Follow up if symptoms persist.",
    });

    console.log("✅ Prescription Updated:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Prescription Update Error:", error.response?.data || error.message);
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        "Failed to update prescription.";
    throw new Error(errorMessage);
  }
};

export const getConsultationEvents = async (consultationId, options = {}) => {
  const params = {};
  if (options.order) params.order = options.order;
  const response = await apiClient.get(`/consultations/events/${consultationId}/`, { params });
  return response.data;
};

export const getPrescriptionVersions = async (consultationId) => {
  const response = await apiClient.get(`/consultations/prescription/${consultationId}/versions/`);
  return response.data;
};

export const getTMCSummary = async () => {
  const response = await apiClient.get("/consultations/tmc/summary/");
  return response.data;
};

export const getTMCConsultations = async () => {
  const response = await apiClient.get("/consultations/tmc/consultations/");
  return response.data;
};

export const getTMCPatients = async () => {
  const response = await apiClient.get("/users/patients/");
  return response.data;
};

export const createTMCPatient = async (payload) => {
  const response = await apiClient.post("/users/patients/", payload);
  return response.data;
};

export const createTMCConsultation = async (payload) => {
  const response = await apiClient.post("/consultations/tmc/book-consultation/", payload);
  return response.data;
};

export const downloadPrescriptionPdf = async (prescriptionId) => {
  const response = await apiClient.get(`/consultations/prescription/pdf/${prescriptionId}/`, {
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const a = document.createElement("a");
  a.href = url;
  a.download = `prescription_${prescriptionId}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
};

export const getPatientWalletSummary = async () => {
  const response = await apiClient.get("/consultations/patient/wallet/");
  return response.data;
};

export const topupPatientWallet = async (amount) => {
  const response = await apiClient.post("/consultations/patient/wallet/", { amount });
  return response.data;
};

export const createPatientWalletRechargeRequest = async (payload) => {
  const response = await apiClient.post("/consultations/patient/wallet/", payload);
  return response.data;
};

export const createPatientWalletRazorpayOrder = async (rechargeId) => {
  const response = await apiClient.post(
    `/consultations/patient/wallet/recharge-requests/${rechargeId}/razorpay/order/`
  );
  return response.data;
};

export const verifyPatientWalletRazorpayPayment = async (rechargeId, payload) => {
  const response = await apiClient.post(
    `/consultations/patient/wallet/recharge-requests/${rechargeId}/razorpay/verify/`,
    payload
  );
  return response.data;
};

export const cancelPatientWalletRechargeRequest = async (rechargeId) => {
  const response = await apiClient.post(`/consultations/patient/wallet/recharge-requests/${rechargeId}/cancel/`);
  return response.data;
};

export const getDoctorEarningsSummary = async () => {
  const response = await apiClient.get("/consultations/doctor/earnings-summary/");
  return response.data;
};

export const getTMCFinanceSummary = async () => {
  const response = await apiClient.get("/consultations/tmc/finance-summary/");
  return response.data;
};

export const getTMCRechargeRequests = async () => {
  const response = await apiClient.get("/consultations/tmc/recharge-requests/");
  return response.data;
};

export const createTMCRechargeRequest = async (payload) => {
  const response = await apiClient.post("/consultations/tmc/recharge-requests/", payload);
  return response.data;
};

export const createTMCRazorpayOrder = async (rechargeId) => {
  const response = await apiClient.post(
    `/consultations/tmc/recharge-requests/${rechargeId}/razorpay/order/`
  );
  return response.data;
};

export const verifyTMCRazorpayPayment = async (rechargeId, payload) => {
  const response = await apiClient.post(
    `/consultations/tmc/recharge-requests/${rechargeId}/razorpay/verify/`,
    payload
  );
  return response.data;
};

export const cancelTMCRechargeRequest = async (rechargeId) => {
  const response = await apiClient.post(`/consultations/tmc/recharge-requests/${rechargeId}/cancel/`);
  return response.data;
};

export const getStaffOperationsReport = async () => {
  const response = await apiClient.get("/consultations/staff/reports/summary/");
  return response.data;
};

export const getStaffFeeSettings = async () => {
  const response = await apiClient.get("/consultations/staff/fee-settings/");
  return response.data;
};

export const createStaffFeeSetting = async (payload) => {
  const response = await apiClient.post("/consultations/staff/fee-settings/", payload);
  return response.data;
};

export const staffTopupTMCWallet = async (payload) => {
  const response = await apiClient.post("/consultations/staff/tmc-wallet-topup/", payload);
  return response.data;
};

export const staffTopupAdminPlatformWallet = async (payload) => {
  const response = await apiClient.post("/consultations/staff/admin-platform-wallet-topup/", payload);
  return response.data;
};

export const getStaffPatients = async () => {
  const response = await apiClient.get("/consultations/staff/patients/");
  return response.data;
};

export const getStaffPatientRechargeRequests = async () => {
  const response = await apiClient.get("/consultations/staff/patient-recharge-requests/");
  return response.data;
};

export const processPatientRechargeRequest = async (rechargeId, payload) => {
  const response = await apiClient.post(
    `/consultations/staff/patient-recharge-requests/${rechargeId}/process/`,
    payload
  );
  return response.data;
};

export const staffTopupPatientWallet = async (payload) => {
  const response = await apiClient.post("/consultations/staff/wallet-topup/", payload);
  return response.data;
};

export const getStaffTMCs = async () => {
  const response = await apiClient.get("/consultations/staff/tmcs/");
  return response.data;
};

export const updateStaffTMCOfferSettings = async (payload) => {
  const response = await apiClient.patch("/consultations/staff/tmcs/", payload);
  return response.data;
};

export const getStaffTMCRechargeRequests = async () => {
  const response = await apiClient.get("/consultations/staff/tmc-recharge-requests/");
  return response.data;
};

export const processTMCRechargeRequest = async (rechargeId, payload) => {
  const response = await apiClient.post(
    `/consultations/staff/tmc-recharge-requests/${rechargeId}/process/`,
    payload
  );
  return response.data;
};

export const getStaffDoctors = async () => {
  const response = await apiClient.get("/consultations/staff/doctors/");
  return response.data;
};

export const updateDoctorVerification = async (doctorProfileId, action) => {
  const response = await apiClient.post(
    `/consultations/staff/doctors/${doctorProfileId}/verification/`,
    { action }
  );
  return response.data;
};

export const createRazorpayOrder = async (paymentId) => {
  const response = await apiClient.post(`/consultations/payments/${paymentId}/razorpay/order/`);
  return response.data;
};

export const verifyRazorpayPayment = async (paymentId, payload) => {
  const response = await apiClient.post(`/consultations/payments/${paymentId}/razorpay/verify/`, payload);
  return response.data;
};

export const getConsultationVideoJoin = async (consultationId) => {
  const response = await apiClient.post(`/consultations/video/join/${consultationId}/`);
  return response.data;
};

export const requestConsultationVideo = async (consultationId) => {
  const response = await apiClient.post(`/consultations/video/request/${consultationId}/`);
  return response.data;
};

export const respondConsultationVideo = async (consultationId, action) => {
  const response = await apiClient.post(`/consultations/video/respond/${consultationId}/`, { action });
  return response.data;
};

export const getTMCProfile = async () => {
  const response = await apiClient.get("/users/tmc/profile/");
  return response.data;
};

export const updateTMCProfile = async (profileData) => {
  const formData = new FormData();
  [
    "tmc_details",
    "clinic_name",
    "clinic_address_street",
    "city",
    "state",
    "pin_code",
  ].forEach((field) => {
    const value = profileData[field];
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      formData.append(field, String(value).trim());
    }
  });
  ["aadhaar_document", "user_photo", "clinic_front_photo"].forEach((field) => {
    if (profileData[field] instanceof File) {
      formData.append(field, profileData[field]);
    }
  });
  const response = await apiClient.patch("/users/tmc/profile/", formData, { timeout: 180000 });
  return response.data;
};

export const getTMCQualificationDocuments = async () => {
  const response = await apiClient.get("/users/tmc/qualification-documents/");
  return response.data;
};

export const uploadTMCQualificationDocument = async (payload) => {
  const formData = new FormData();
  ["exam_name", "board_or_university", "percentage"].forEach((field) => {
    const value = payload[field];
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      formData.append(field, String(value).trim());
    }
  });
  if (payload.document instanceof File) {
    formData.append("document", payload.document);
  }
  const response = await apiClient.post("/users/tmc/qualification-documents/", formData, { timeout: 180000 });
  return response.data;
};

export const deleteTMCQualificationDocument = async (id) => {
  const response = await apiClient.delete(`/users/tmc/qualification-documents/${id}/`);
  return response.data;
};

export default apiClient;
