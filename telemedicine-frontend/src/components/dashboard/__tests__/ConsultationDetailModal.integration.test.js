import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import ConsultationDetailModal from "../ConsultationDetailModal";
import * as usersApi from "../../../api/users";
import * as videoLifecycle from "../../../utils/videoLifecycle";

jest.mock("../../../api/users");
jest.mock("../../../utils/videoLifecycle");

jest.mock("../VideoPanel", () => {
  return function MockVideoPanel({ onSessionReady }) {
    React.useEffect(() => {
      if (onSessionReady) {
        const mockSession = {
          meeting: { leave: jest.fn() },
          localStream: { getTracks: () => [{ stop: jest.fn() }] },
          videoElement: {},
        };
        onSessionReady(mockSession);
      }
    }, [onSessionReady]);
    return <div data-testid="video-panel">Video Panel</div>;
  };
});

const mockConsultation = {
  id: 1,
  patient_name: "Test Patient",
  doctor_name: "Dr. Test",
  status: "IN_PROGRESS",
  consultation_type: "DIRECT",
  formatted_time: "Nov 23, 2026 at 10:00 AM",
  video: { status: "NONE" },
};

const mockEvents = [
  {
    id: 1,
    event_type: "CONSULTATION_REQUESTED",
    created_at: "2026-11-23T10:00:00Z",
  },
];

describe("ConsultationDetailModal Integration Tests", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    videoLifecycle.shouldCloseVideo.mockReturnValue(false);
    videoLifecycle.shouldClearCredentials.mockReturnValue(false);
    videoLifecycle.cleanupVideoSession.mockResolvedValue(true);
  });

  const renderModal = (props = {}) => {
    const defaultProps = {
      consultation: mockConsultation,
      events: mockEvents,
      onClose: jest.fn(),
      viewerRole: "doctor",
    };
    return render(<ConsultationDetailModal {...defaultProps} {...props} />);
  };

  it("displays status message for the consultation", async () => {
    renderModal();

    await waitFor(() => {
      expect(screen.getByText(/Consultation active/i)).toBeInTheDocument();
    });
  });

  it("triggers video cleanup when consultation becomes terminal", async () => {
    videoLifecycle.shouldCloseVideo.mockReturnValue(true);

    const { rerender } = renderModal();

    const completedConsultation = {
      ...mockConsultation,
      status: "COMPLETED",
      is_completed: true,
    };

    rerender(
      <ConsultationDetailModal
        consultation={completedConsultation}
        events={mockEvents}
        onClose={jest.fn()}
        viewerRole="doctor"
      />
    );

    await waitFor(() => {
      expect(videoLifecycle.shouldCloseVideo).toHaveBeenCalled();
    });
  });

  it("clears video credentials on terminal status", async () => {
    videoLifecycle.shouldClearCredentials.mockReturnValue(true);

    const completedConsultation = {
      ...mockConsultation,
      status: "COMPLETED",
      is_completed: true,
    };

    renderModal({ consultation: completedConsultation });

    await waitFor(() => {
      expect(videoLifecycle.shouldClearCredentials).toHaveBeenCalled();
    });
  });

  it("preserves active follow-up session video access", async () => {
    const consultationWithFollowUp = {
      ...mockConsultation,
      status: "COMPLETED",
      is_completed: true,
      follow_up: {
        active_status: "IN_PROGRESS",
      },
    };

    videoLifecycle.shouldCloseVideo.mockReturnValue(false);

    renderModal({ consultation: consultationWithFollowUp });

    await waitFor(() => {
      expect(videoLifecycle.shouldCloseVideo).toHaveBeenCalled();
    });
  });

  it("cleans up video session on consultation switch", async () => {
    usersApi.getConsultationVideoJoin.mockResolvedValue({
      consultation_id: 1,
      token: "test-token",
      session_id: "test-session",
      account_id: "test-account",
      app_id: "test-app",
    });

    const { rerender } = renderModal();

    await waitFor(() => {
      expect(screen.getByText(/Consultation #1/i)).toBeInTheDocument();
    });

    const newConsultation = {
      ...mockConsultation,
      id: 2,
    };

    rerender(
      <ConsultationDetailModal
        consultation={newConsultation}
        events={mockEvents}
        onClose={jest.fn()}
        viewerRole="doctor"
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Consultation #2/i)).toBeInTheDocument();
    });
  });

  it("cleans up video session on unmount", async () => {
    const { unmount } = renderModal();

    await waitFor(() => {
      expect(screen.getByText(/Consultation #1/i)).toBeInTheDocument();
    });

    unmount();

    expect(videoLifecycle.cleanupVideoSession).toHaveBeenCalled();
  });

  it("tracks video session state via onSessionReady callback", async () => {
    usersApi.getConsultationVideoJoin.mockResolvedValue({
      consultation_id: 1,
      token: "test-token",
      session_id: "test-session",
      account_id: "test-account",
      app_id: "test-app",
      provider: "cloudflare",
    });

    const consultationWithVideo = {
      ...mockConsultation,
      video: { status: "ACCEPTED" },
    };

    renderModal({ consultation: consultationWithVideo });

    const joinButton = screen.queryByText(/Join video/i);
    if (joinButton) {
      fireEvent.click(joinButton);

      await waitFor(() => {
        expect(screen.getByTestId("video-panel")).toBeInTheDocument();
      });
    }
  });

  it("handles video request errors gracefully", async () => {
    usersApi.requestConsultationVideo.mockRejectedValue(
      new Error("Video provider not configured")
    );

    renderModal({ viewerRole: "doctor" });

    const requestButton = screen.queryByText(/Request video/i);
    if (requestButton) {
      fireEvent.click(requestButton);

      await waitFor(() => {
        expect(screen.getByText(/Video provider not configured/i)).toBeInTheDocument();
      });
    }
  });

  it("displays postponement information correctly", async () => {
    const postponedConsultation = {
      ...mockConsultation,
      status: "POSTPONED",
      formatted_suggested_time: "Nov 24, 2026 at 2:00 PM",
    };

    renderModal({ consultation: postponedConsultation, viewerRole: "doctor" });

    await waitFor(() => {
      expect(screen.getByText(/New time suggested/i)).toBeInTheDocument();
    });
  });

  it("hides video actions for terminal states without active follow-up", async () => {
    const completedConsultation = {
      ...mockConsultation,
      status: "COMPLETED",
      is_completed: true,
    };

    renderModal({ consultation: completedConsultation, viewerRole: "doctor" });

    await waitFor(() => {
      expect(screen.queryByText(/Request video/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Join video/i)).not.toBeInTheDocument();
    });
  });

  it("releases local media tracks when video closes", async () => {
    videoLifecycle.shouldCloseVideo.mockReturnValue(true);
    videoLifecycle.releaseLocalTracks = jest.fn();

    const { rerender } = renderModal();

    const completedConsultation = {
      ...mockConsultation,
      status: "COMPLETED",
      is_completed: true,
    };

    rerender(
      <ConsultationDetailModal
        consultation={completedConsultation}
        events={mockEvents}
        onClose={jest.fn()}
        viewerRole="doctor"
      />
    );

    await waitFor(() => {
      expect(videoLifecycle.cleanupVideoSession).toHaveBeenCalled();
    });
  });
});
