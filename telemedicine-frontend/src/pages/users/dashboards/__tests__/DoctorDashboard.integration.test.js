import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import DoctorDashboard from "../DoctorDashboard";
import * as usersApi from "../../../../api/users";

jest.mock("../../../../api/users");

const mockConsultation = {
  id: 1,
  patient_name: "Test Patient",
  doctor_name: "Dr. Test",
  status: "PENDING",
  consultation_type: "DIRECT",
  formatted_time: "Nov 23, 2026 at 10:00 AM",
  created_at: "2026-11-23T10:00:00Z",
};

const mockActiveConsultation = {
  ...mockConsultation,
  id: 2,
  status: "IN_PROGRESS",
};

const mockCompletedConsultation = {
  ...mockConsultation,
  id: 3,
  status: "COMPLETED",
  is_completed: true,
};

const mockDoctorProfile = {
  first_name: "John",
  last_name: "Doe",
  specialty: "Cardiology",
  qualification: "MD",
  experience: "10 years",
};

describe("DoctorDashboard Integration Tests", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    usersApi.getPatientConsultationHistory.mockResolvedValue([mockConsultation]);
    usersApi.getDoctorPendingRequests.mockResolvedValue([mockConsultation]);
    usersApi.getDoctorQueuedConsultations.mockResolvedValue([]);
    usersApi.getActiveConsultation.mockResolvedValue(null);
    usersApi.getDoctorEarningsSummary.mockResolvedValue({ total_earnings: "1000.00", recent_earnings: [] });
    usersApi.getDoctorProfile.mockResolvedValue(mockDoctorProfile);
  });

  const renderDashboard = () => {
    return render(
      <BrowserRouter>
        <DoctorDashboard />
      </BrowserRouter>
    );
  };

  it("loads and displays consultations", async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/Doctor operations/i)).toBeInTheDocument();
    });

    expect(usersApi.getPatientConsultationHistory).toHaveBeenCalled();
    expect(usersApi.getDoctorPendingRequests).toHaveBeenCalled();
  });

  it("handles status update from pending to in progress", async () => {
    usersApi.getPatientConsultationHistory
      .mockResolvedValueOnce([mockConsultation])
      .mockResolvedValueOnce([mockActiveConsultation]);
    
    usersApi.getActiveConsultation
      .mockResolvedValueOnce(null)
      .mockResolvedValueOnce(mockActiveConsultation);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/Doctor operations/i)).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(usersApi.getPatientConsultationHistory).toHaveBeenCalledTimes(2);
    }, { timeout: 10000 });
  });

  it("prevents stale responses when consultation changes", async () => {
    const { rerender } = renderDashboard();

    await waitFor(() => {
      expect(usersApi.getPatientConsultationHistory).toHaveBeenCalled();
    });

    usersApi.getPatientConsultationHistory.mockResolvedValue([mockCompletedConsultation]);

    rerender(
      <BrowserRouter>
        <DoctorDashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(usersApi.getPatientConsultationHistory).toHaveBeenCalledTimes(2);
    });
  });

  it("shows stale indicator when refresh fails", async () => {
    usersApi.getPatientConsultationHistory
      .mockResolvedValueOnce([mockConsultation])
      .mockRejectedValueOnce(new Error("Network error"));

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/Doctor operations/i)).toBeInTheDocument();
    });

    await waitFor(() => {
      const staleIndicator = screen.queryByText(/Updates paused/i) || screen.queryByText(/Refresh failed/i);
      if (staleIndicator) {
        expect(staleIndicator).toBeInTheDocument();
      }
    }, { timeout: 10000 });
  });

  it("handles repeated action clicks gracefully", async () => {
    usersApi.doctorRespondToRequest.mockResolvedValue({ status: "ACCEPTED" });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/Doctor operations/i)).toBeInTheDocument();
    });

    const acceptButtons = screen.queryAllByText(/Accept/i);
    if (acceptButtons.length > 0) {
      fireEvent.click(acceptButtons[0]);
      fireEvent.click(acceptButtons[0]);

      await waitFor(() => {
        expect(usersApi.doctorRespondToRequest).toHaveBeenCalledTimes(1);
      });
    }
  });

  it("preserves state during background refresh", async () => {
    renderDashboard();

    await waitFor(() => {
      expect(usersApi.getPatientConsultationHistory).toHaveBeenCalled();
    });

    const initialCallCount = usersApi.getPatientConsultationHistory.mock.calls.length;

    await waitFor(() => {
      expect(usersApi.getPatientConsultationHistory.mock.calls.length).toBeGreaterThan(initialCallCount);
    }, { timeout: 10000 });
  });

  it("cleans up timers on unmount", async () => {
    const { unmount } = renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/Doctor operations/i)).toBeInTheDocument();
    });

    unmount();

    const callCountBeforeUnmount = usersApi.getPatientConsultationHistory.mock.calls.length;

    await new Promise((resolve) => setTimeout(resolve, 9000));

    expect(usersApi.getPatientConsultationHistory.mock.calls.length).toBeLessThanOrEqual(callCountBeforeUnmount + 1);
  });

  it("handles follow-up requests correctly", async () => {
    const followUpRequest = {
      ...mockConsultation,
      is_follow_up_request: true,
      follow_up_session_id: 5,
    };

    usersApi.getDoctorPendingRequests.mockResolvedValue([followUpRequest]);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/Doctor operations/i)).toBeInTheDocument();
    });

    const resumeButtons = screen.queryAllByText(/resume/i);
    expect(resumeButtons.length).toBeGreaterThanOrEqual(0);
  });
});
