import {
  getStatusLabel,
  getStatusMessage,
  getAvailableActions,
  isTerminalStatus,
  canInteract,
  getPostponementExplanation,
  getFollowUpStatus,
} from "../consultationStatus";

describe("consultationStatus utilities", () => {
  describe("getStatusLabel", () => {
    it("returns friendly labels for known statuses", () => {
      expect(getStatusLabel("PENDING")).toBe("Pending");
      expect(getStatusLabel("IN_PROGRESS")).toBe("In Progress");
      expect(getStatusLabel("COMPLETED")).toBe("Completed");
      expect(getStatusLabel("REJECTED")).toBe("Rejected");
    });

    it("returns the status itself for unknown values", () => {
      expect(getStatusLabel("UNKNOWN_STATUS")).toBe("UNKNOWN_STATUS");
    });

    it("handles null/undefined gracefully", () => {
      expect(getStatusLabel(null)).toBe("Unknown");
      expect(getStatusLabel(undefined)).toBe("Unknown");
    });
  });

  describe("getStatusMessage", () => {
    it("returns null for null consultation", () => {
      expect(getStatusMessage(null, "patient")).toBeNull();
    });

    it("returns patient-facing message for PENDING status", () => {
      const consultation = {
        status: "PENDING",
        doctor_name: "Dr. Smith",
      };
      const result = getStatusMessage(consultation, "patient");
      expect(result).toBeTruthy();
      expect(result.title).toBe("Request sent");
      expect(result.message).toContain("Dr. Smith");
      expect(result.severity).toBe("info");
    });

    it("returns doctor-facing message for PENDING status", () => {
      const consultation = {
        status: "PENDING",
        patient_name: "John Doe",
      };
      const result = getStatusMessage(consultation, "doctor");
      expect(result).toBeTruthy();
      expect(result.title).toBe("New request waiting");
      expect(result.message).toContain("John Doe");
      expect(result.severity).toBe("urgent");
    });

    it("includes queue number in message when available", () => {
      const consultation = {
        status: "QUEUED",
        doctor_name: "Dr. Smith",
        queue_number: 3,
      };
      const result = getStatusMessage(consultation, "patient");
      expect(result.message).toContain("position 3");
    });

    it("handles POSTPONED status with formatted time", () => {
      const consultation = {
        status: "POSTPONED",
        doctor_name: "Dr. Smith",
        formatted_suggested_time: "Dec 25, 2026 at 3:00 PM",
      };
      const result = getStatusMessage(consultation, "patient");
      expect(result.title).toBe("New time suggested");
      expect(result.message).toContain("Dec 25, 2026 at 3:00 PM");
    });

    it("returns TMC-specific messages", () => {
      const consultation = {
        status: "IN_PROGRESS",
        doctor_name: "Dr. Smith",
        patient_name: "John Doe",
      };
      const result = getStatusMessage(consultation, "tmc");
      expect(result).toBeTruthy();
      expect(result.message).toContain("Dr. Smith");
      expect(result.message).toContain("John Doe");
    });
  });

  describe("getAvailableActions", () => {
    it("returns empty array for null consultation", () => {
      expect(getAvailableActions(null, "patient")).toEqual([]);
    });

    it("returns doctor actions for PENDING status", () => {
      const consultation = { status: "PENDING" };
      const actions = getAvailableActions(consultation, "doctor");
      expect(actions.length).toBeGreaterThan(0);
      expect(actions.some((a) => a.key === "accept")).toBe(true);
      expect(actions.some((a) => a.key === "reject")).toBe(true);
      expect(actions.some((a) => a.key === "postpone")).toBe(true);
    });

    it("returns patient actions for POSTPONED status", () => {
      const consultation = { status: "POSTPONED" };
      const actions = getAvailableActions(consultation, "patient");
      expect(actions.length).toBeGreaterThan(0);
      expect(actions.some((a) => a.key === "accept_postponed")).toBe(true);
      expect(actions.some((a) => a.key === "reject_postponed")).toBe(true);
    });

    it("includes follow-up actions for completed consultations", () => {
      const consultation = {
        status: "COMPLETED",
        follow_up: { can_request: true, next_is_billable: false },
      };
      const actions = getAvailableActions(consultation, "patient");
      expect(actions.some((a) => a.key === "request_followup")).toBe(true);
    });

    it("shows active follow-up action when in progress", () => {
      const consultation = {
        status: "COMPLETED",
        follow_up: { active_status: "IN_PROGRESS", can_request: false },
      };
      const actions = getAvailableActions(consultation, "patient");
      expect(actions.some((a) => a.key === "open_followup")).toBe(true);
    });
  });

  describe("isTerminalStatus", () => {
    it("returns true for terminal statuses", () => {
      expect(isTerminalStatus("COMPLETED")).toBe(true);
      expect(isTerminalStatus("REJECTED")).toBe(true);
      expect(isTerminalStatus("REJECTED_BY_PATIENT")).toBe(true);
      expect(isTerminalStatus("CANCELED")).toBe(true);
    });

    it("returns false for active statuses", () => {
      expect(isTerminalStatus("PENDING")).toBe(false);
      expect(isTerminalStatus("IN_PROGRESS")).toBe(false);
      expect(isTerminalStatus("QUEUED")).toBe(false);
      expect(isTerminalStatus("POSTPONED")).toBe(false);
    });
  });

  describe("canInteract", () => {
    it("returns true for interactive statuses", () => {
      expect(canInteract("ACCEPTED")).toBe(true);
      expect(canInteract("QUEUED")).toBe(true);
      expect(canInteract("IN_PROGRESS")).toBe(true);
    });

    it("returns false for non-interactive statuses", () => {
      expect(canInteract("PENDING")).toBe(false);
      expect(canInteract("COMPLETED")).toBe(false);
      expect(canInteract("REJECTED")).toBe(false);
    });
  });

  describe("getPostponementExplanation", () => {
    it("returns explanation for POSTPONED status", () => {
      const consultation = {
        status: "POSTPONED",
        formatted_suggested_time: "Dec 25, 2026 at 3:00 PM",
      };
      const result = getPostponementExplanation(consultation);
      expect(result).toBeTruthy();
      expect(result.title).toBe("New time proposed");
      expect(result.body).toContain("Dec 25, 2026 at 3:00 PM");
      expect(result.body).toContain("No second consultation charge");
    });

    it("returns null for non-postponed consultations", () => {
      const consultation = { status: "PENDING" };
      expect(getPostponementExplanation(consultation)).toBeNull();
    });

    it("returns null for null consultation", () => {
      expect(getPostponementExplanation(null)).toBeNull();
    });
  });

  describe("getFollowUpStatus", () => {
    it("returns status text for PENDING follow-up", () => {
      const consultation = {
        follow_up: { active_status: "PENDING" },
      };
      const result = getFollowUpStatus(consultation);
      expect(result).toContain("Waiting for doctor");
    });

    it("returns status text for IN_PROGRESS follow-up", () => {
      const consultation = {
        follow_up: { active_status: "IN_PROGRESS" },
      };
      const result = getFollowUpStatus(consultation);
      expect(result).toContain("Chat is available");
    });

    it("returns null when no follow-up data", () => {
      expect(getFollowUpStatus({})).toBeNull();
      expect(getFollowUpStatus(null)).toBeNull();
    });
  });
});
