import axios from "axios";
import { API_BASE_URL } from "./config";

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

// ✅ Function to Get User Profile
export const getUserProfile = async () => {
  try {
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in again.");
    }

    const response = await axios.get(`${API_BASE_URL}/users/profile/`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    console.log("✅ API Response:", response.data); // 🔍 Debugging Log
    return response.data;
  } catch (error) {
    console.error("❌ Profile Fetch Error:", error.response?.data || error.message);
    // Provide more detailed error message
    const errorMessage = error.response?.data?.detail || 
                        error.response?.data?.error || 
                        error.message || 
                        "Failed to fetch profile.";
    throw new Error(errorMessage);
  }
};

// ✅ Function to Logout User
export const logoutUser = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("userType");
  window.location.href = "/login"; // Redirect after logout
};

// Refresh token
export const refreshToken = async () => {
  const refresh_token = localStorage.getItem("refresh_token");

  if (!refresh_token) {
    throw new Error("No refresh token available. Please log in again.");
  }

  try {
    const response = await axios.post(`${API_BASE_URL}/users/token/refresh/`, {
      refresh: refresh_token,
    });

    // ✅ Store new access token
    localStorage.setItem("token", response.data.access);
    return response.data.access;
  } catch (error) {
    console.error("Token Refresh Error:", error.response?.data || error.message);
    throw new Error("Session expired. Please log in again.");
  }
};

//token refresh automatically
const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use(
  async (config) => {
    let token = localStorage.getItem("token");
    config.headers.Authorization = `Bearer ${token}`;

    return config;
  },
  (error) => Promise.reject(error)
);

// ✅ Handle expired tokens
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      console.warn("🔄 Token expired, attempting refresh...");
      try {
        const newToken = await refreshToken();
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return axios(error.config); // ✅ Retry request with new token
      } catch (refreshError) {
        console.error("🔴 Token refresh failed. Logging out...");
        logoutUser();
        throw new Error("Session expired. Please log in again.");
      }
    }
    return Promise.reject(error);
  }
);


// Patient consultation history
export const getPatientConsultationHistory = async () => {
  try {
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.get(`${API_BASE_URL}/consultations/history/`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    console.log("✅ Consultation History:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Consultation History Fetch Error:", error.response?.data || error.message);
    throw new Error("Failed to fetch consultation history.");
  }
};

// ✅ Get Pending Consultation Requests for Doctor
export const getDoctorPendingRequests = async () => {
  try {
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.get(`${API_BASE_URL}/consultations/doctor/pending-requests/`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    console.log("✅ Pending Requests:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Pending Requests Fetch Error:", error.response?.data || error.message);
    throw new Error("Failed to fetch pending requests.");
  }
};

// ✅ Doctor Response to Consultation Request
export const doctorRespondToRequest = async (consultationId, action, newSuggestedTime = null) => {
  try {
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const data = { status: action };
    if (action === "POSTPONED" && newSuggestedTime) {
      data.new_suggested_time = newSuggestedTime;
    }

    const response = await axios.patch(
      `${API_BASE_URL}/consultations/doctor-response/${consultationId}/`,
      data,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

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
export const getDoctorProfile = async () => {
  try {
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.get(`${API_BASE_URL}/consultations/doctor/profile/`, {
      headers: { Authorization: `Bearer ${token}` },
    });

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
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const formData = new FormData();
    
    // Add text fields - only if they have values (not empty strings)
    if (profileData.qualification && profileData.qualification.trim()) {
      formData.append('qualification', profileData.qualification.trim());
    }
    if (profileData.specialty && profileData.specialty.trim()) {
      formData.append('specialty', profileData.specialty.trim());
    }
    if (profileData.experience && profileData.experience.trim()) {
      formData.append('experience', profileData.experience.trim());
    }
    if (profileData.license_number && profileData.license_number.trim()) {
      formData.append('license_number', profileData.license_number.trim().toUpperCase());
    }
    if (profileData.registration_number && profileData.registration_number.trim()) {
      formData.append('registration_number', profileData.registration_number.trim());
    }
    if (profileData.major_diseases_specializations && profileData.major_diseases_specializations.trim()) {
      formData.append('major_diseases_specializations', profileData.major_diseases_specializations.trim());
    }
    if (profileData.previous_hospitals_served && profileData.previous_hospitals_served.trim()) {
      formData.append('previous_hospitals_served', profileData.previous_hospitals_served.trim());
    }
    if (profileData.hospital_or_clinic_name && profileData.hospital_or_clinic_name.trim()) {
      formData.append('hospital_or_clinic_name', profileData.hospital_or_clinic_name.trim());
    }
    if (profileData.max_daily_consultations) {
      formData.append('max_daily_consultations', profileData.max_daily_consultations);
    }
    
    // Add file fields - only if they are File objects
    if (profileData.photo instanceof File) {
      formData.append('photo', profileData.photo);
    }
    if (profileData.registration_certificate instanceof File) {
      formData.append('registration_certificate', profileData.registration_certificate);
    }

    const response = await axios.patch(`${API_BASE_URL}/consultations/doctor/profile/`, formData, {
      headers: { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data',
      },
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
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.get(`${API_BASE_URL}/consultations/doctor/availability/`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    return response.data;
  } catch (error) {
    console.error("❌ Doctor Availability Fetch Error:", error.response?.data || error.message);
    throw new Error("Failed to fetch doctor availability.");
  }
};

export const updateDoctorAvailability = async (availabilityData) => {
  try {
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

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
      response = await axios.patch(`${API_BASE_URL}/consultations/doctor/availability/`, payload, {
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (error) {
      // If availability row doesn't exist yet, create then update.
      if (error.response?.status === 404) {
        await axios.post(`${API_BASE_URL}/consultations/doctor/availability/create/`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
        response = await axios.patch(`${API_BASE_URL}/consultations/doctor/availability/`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
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
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.get(`${API_BASE_URL}/consultations/doctor/schedule/`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    return response.data;
  } catch (error) {
    console.error("❌ Doctor Schedule Fetch Error:", error.response?.data || error.message);
    throw new Error("Failed to fetch doctor schedules.");
  }
};

export const createDoctorSchedule = async (scheduleData) => {
  try {
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.post(`${API_BASE_URL}/consultations/doctor/schedule/`, scheduleData, {
      headers: { Authorization: `Bearer ${token}` },
    });

    return response.data;
  } catch (error) {
    console.error("❌ Doctor Schedule Create Error:", error.response?.data || error.message);
    throw error;
  }
};

// ✅ Patient Response to Consultation (Approve/Reject Postponed, Cancel)
export const patientRespondToConsultation = async (consultationId, action) => {
  try {
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.patch(
      `${API_BASE_URL}/consultations/patient-response/${consultationId}/`,
      { action: action },
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

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
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.get(`${API_BASE_URL}/consultations/doctor/queued-consultations/`, {
      headers: { Authorization: `Bearer ${token}` },
    });

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
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.post(
      `${API_BASE_URL}/consultations/start-consultation/${consultationId}/`,
      {},
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

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
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.post(
      `${API_BASE_URL}/consultations/complete-consultation/${consultationId}/`,
      {},
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

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

// ✅ Get Active Consultation
export const getActiveConsultation = async () => {
  try {
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.get(`${API_BASE_URL}/consultations/active-consultation/`, {
      headers: { Authorization: `Bearer ${token}` },
    });

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
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.get(
      `${API_BASE_URL}/consultations/chat-history/${consultationId}/`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

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
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    // Use FormData if file is present, otherwise send JSON
    let data, headers;
    if (file) {
      const formData = new FormData();
      if (message) {
        formData.append('message', message);
      }
      formData.append('attachment', file);
      data = formData;
      headers = { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      };
    } else {
      data = { message: message };
      headers = { Authorization: `Bearer ${token}` };
    }

    const response = await axios.post(
      `${API_BASE_URL}/consultations/send-message/${consultationId}/`,
      data,
      { headers }
    );

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
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.post(
      `${API_BASE_URL}/consultations/prescription/${consultationId}/`,
      {
        medicines: medicines,
        instructions: instructions || "Take medicines as prescribed. Follow up if symptoms persist."
      },
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

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
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.get(
      `${API_BASE_URL}/consultations/prescription/${consultationId}/`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

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
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("⚠ No authentication token found. Please log in.");
    }

    const response = await axios.put(
      `${API_BASE_URL}/consultations/prescription/${consultationId}/`,
      {
        medicines: medicines,
        instructions: instructions || "Take medicines as prescribed. Follow up if symptoms persist."
      },
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

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

export const getConsultationEvents = async (consultationId) => {
  const token = localStorage.getItem("token");
  const response = await axios.get(
    `${API_BASE_URL}/consultations/events/${consultationId}/`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
};

export const getTMCSummary = async () => {
  const token = localStorage.getItem("token");
  const response = await axios.get(`${API_BASE_URL}/consultations/tmc/summary/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const getTMCConsultations = async () => {
  const token = localStorage.getItem("token");
  const response = await axios.get(`${API_BASE_URL}/consultations/tmc/consultations/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const getTMCPatients = async () => {
  const token = localStorage.getItem("token");
  const response = await axios.get(`${API_BASE_URL}/users/patients/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const createTMCConsultation = async (payload) => {
  const token = localStorage.getItem("token");
  const response = await axios.post(
    `${API_BASE_URL}/consultations/tmc/book-consultation/`,
    payload,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
};

export const downloadPrescriptionPdf = async (prescriptionId) => {
  const token = localStorage.getItem("token");
  const response = await axios.get(
    `${API_BASE_URL}/consultations/prescription/pdf/${prescriptionId}/`,
    {
      responseType: "blob",
      headers: { Authorization: `Bearer ${token}` },
    }
  );
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
  const token = localStorage.getItem("token");
  const response = await axios.get(`${API_BASE_URL}/consultations/patient/wallet/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const topupPatientWallet = async (amount) => {
  const token = localStorage.getItem("token");
  const response = await axios.post(
    `${API_BASE_URL}/consultations/patient/wallet/`,
    { amount },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
};

export const getDoctorEarningsSummary = async () => {
  const token = localStorage.getItem("token");
  const response = await axios.get(`${API_BASE_URL}/consultations/doctor/earnings-summary/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const getTMCFinanceSummary = async () => {
  const token = localStorage.getItem("token");
  const response = await axios.get(`${API_BASE_URL}/consultations/tmc/finance-summary/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export default apiClient;
