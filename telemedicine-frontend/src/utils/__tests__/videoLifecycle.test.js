import {
  shouldCloseVideo,
  shouldClearCredentials,
  releaseLocalTracks,
  leaveSdkSession,
  cleanupVideoSession,
} from "../videoLifecycle";

describe("videoLifecycle utilities", () => {
  describe("shouldCloseVideo", () => {
    it("returns true when moving from active to terminal status", () => {
      const consultation = { status: "COMPLETED" };
      const previousStatus = "IN_PROGRESS";
      expect(shouldCloseVideo(consultation, previousStatus)).toBe(true);
    });

    it("returns false when already terminal", () => {
      const consultation = { status: "COMPLETED" };
      const previousStatus = "COMPLETED";
      expect(shouldCloseVideo(consultation, previousStatus)).toBe(false);
    });

    it("returns false when moving from PENDING to COMPLETED", () => {
      const consultation = { status: "COMPLETED" };
      const previousStatus = "PENDING";
      expect(shouldCloseVideo(consultation, previousStatus)).toBe(false);
    });

    it("preserves active follow-up sessions", () => {
      const consultation = {
        status: "COMPLETED",
        follow_up: { active_status: "IN_PROGRESS" },
      };
      const previousStatus = "IN_PROGRESS";
      expect(shouldCloseVideo(consultation, previousStatus)).toBe(false);
    });

    it("handles null consultation", () => {
      expect(shouldCloseVideo(null, "IN_PROGRESS")).toBe(false);
    });
  });

  describe("shouldClearCredentials", () => {
    it("returns true for terminal statuses", () => {
      expect(shouldClearCredentials({ status: "COMPLETED" })).toBe(true);
      expect(shouldClearCredentials({ status: "REJECTED" })).toBe(true);
      expect(shouldClearCredentials({ status: "CANCELED" })).toBe(true);
    });

    it("returns false for active statuses", () => {
      expect(shouldClearCredentials({ status: "IN_PROGRESS" })).toBe(false);
      expect(shouldClearCredentials({ status: "QUEUED" })).toBe(false);
    });

    it("handles null consultation", () => {
      expect(shouldClearCredentials(null)).toBe(false);
    });
  });

  describe("releaseLocalTracks", () => {
    it("stops all tracks in a stream", () => {
      const mockTrack1 = { stop: jest.fn() };
      const mockTrack2 = { stop: jest.fn() };
      const mockStream = {
        getTracks: jest.fn(() => [mockTrack1, mockTrack2]),
      };

      releaseLocalTracks(mockStream);

      expect(mockTrack1.stop).toHaveBeenCalled();
      expect(mockTrack2.stop).toHaveBeenCalled();
    });

    it("handles errors gracefully", () => {
      const mockTrack = {
        stop: jest.fn(() => {
          throw new Error("Track error");
        }),
      };
      const mockStream = {
        getTracks: jest.fn(() => [mockTrack]),
      };

      expect(() => releaseLocalTracks(mockStream)).not.toThrow();
    });

    it("handles null stream", () => {
      expect(() => releaseLocalTracks(null)).not.toThrow();
    });
  });

  describe("leaveSdkSession", () => {
    it("calls leave on SDK meeting", async () => {
      const mockMeeting = {
        leave: jest.fn(() => Promise.resolve()),
      };

      await leaveSdkSession(mockMeeting);

      expect(mockMeeting.leave).toHaveBeenCalled();
    });

    it("handles errors gracefully", async () => {
      const mockMeeting = {
        leave: jest.fn(() => Promise.reject(new Error("SDK error"))),
      };

      await expect(leaveSdkSession(mockMeeting)).resolves.not.toThrow();
    });

    it("handles null meeting", async () => {
      await expect(leaveSdkSession(null)).resolves.not.toThrow();
    });
  });

  describe("cleanupVideoSession", () => {
    it("performs complete cleanup", async () => {
      const mockTrack = { stop: jest.fn() };
      const mockMeeting = { leave: jest.fn(() => Promise.resolve()) };
      const mockVideoElement = { srcObject: "test" };
      const videoState = {
        localStream: { getTracks: () => [mockTrack] },
        meeting: mockMeeting,
        videoElement: mockVideoElement,
      };

      const result = await cleanupVideoSession(videoState);

      expect(result).toBe(true);
      expect(mockTrack.stop).toHaveBeenCalled();
      expect(mockMeeting.leave).toHaveBeenCalled();
      expect(mockVideoElement.srcObject).toBeNull();
    });

    it("handles partial state", async () => {
      const mockTrack = { stop: jest.fn() };
      const videoState = {
        localStream: { getTracks: () => [mockTrack] },
      };

      const result = await cleanupVideoSession(videoState);

      expect(result).toBe(true);
      expect(mockTrack.stop).toHaveBeenCalled();
    });

    it("returns false for null state", async () => {
      const result = await cleanupVideoSession(null);
      expect(result).toBe(false);
    });

    it("handles cleanup errors gracefully", async () => {
      const videoState = {
        videoElement: {
          set srcObject(val) {
            throw new Error("DOM error");
          },
        },
      };

      await expect(cleanupVideoSession(videoState)).resolves.not.toThrow();
    });
  });
});
