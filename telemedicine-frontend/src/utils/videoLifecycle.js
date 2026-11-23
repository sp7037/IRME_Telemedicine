/**
 * Video lifecycle utilities for cleanup and terminal state handling
 */

import { isTerminalStatus } from "./consultationStatus";

/**
 * Check if video should be closed based on consultation status
 * Preserves active follow-up sessions
 */
export const shouldCloseVideo = (consultation, previousStatus) => {
  if (!consultation) return false;

  const currentStatus = consultation.follow_up?.active_status === "IN_PROGRESS"
    ? "IN_PROGRESS"
    : consultation.status;

  if (isTerminalStatus(currentStatus)) {
    const wasActive = previousStatus === "IN_PROGRESS" || previousStatus === "QUEUED" || previousStatus === "ACCEPTED";
    return wasActive;
  }

  return false;
};

/**
 * Release local media tracks
 */
export const releaseLocalTracks = (stream) => {
  if (stream && stream.getTracks) {
    stream.getTracks().forEach((track) => {
      try {
        track.stop();
      } catch (err) {
        console.warn("Failed to stop track:", err);
      }
    });
  }
};

/**
 * Leave SDK session
 */
export const leaveSdkSession = async (meeting) => {
  if (meeting && typeof meeting.leave === "function") {
    try {
      await meeting.leave();
    } catch (err) {
      console.warn("Failed to leave meeting:", err);
    }
  }
};

/**
 * Complete video cleanup
 * Returns true if cleanup was performed
 */
export const cleanupVideoSession = async (videoState) => {
  if (!videoState) return false;

  let cleaned = false;

  if (videoState.localStream) {
    releaseLocalTracks(videoState.localStream);
    cleaned = true;
  }

  if (videoState.meeting) {
    await leaveSdkSession(videoState.meeting);
    cleaned = true;
  }

  if (videoState.videoElement) {
    try {
      videoState.videoElement.srcObject = null;
      cleaned = true;
    } catch (err) {
      console.warn("Failed to clear video element:", err);
    }
  }

  return cleaned;
};

/**
 * Check if video join credentials should be cleared
 */
export const shouldClearCredentials = (consultation) => {
  if (!consultation) return false;
  return isTerminalStatus(consultation.status);
};
